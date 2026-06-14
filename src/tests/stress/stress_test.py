import urllib.request
import urllib.parse
import re
import time
import threading
import sys

# Target Base URL
BASE_URL = "http://127.0.0.1:8000"

# Target duration for the stress test (in seconds)
TEST_DURATION = 15

# Total requests tracked
total_requests = 0
successful_requests = 0
failed_requests = 0
latencies = []
stats_lock = threading.Lock()

def user_session_worker(user_id, username, role):
    global total_requests, successful_requests, failed_requests
    
    # Each thread has its own cookie jar
    cookie_processor = urllib.request.HTTPCookieProcessor()
    opener = urllib.request.build_opener(cookie_processor)
    opener.addheaders = [('User-Agent', f'StressTester-User-{user_id}')]
    
    start_time = time.time()
    
    while time.time() - start_time < TEST_DURATION:
        try:
            # 1. Fetch Landing Page
            t0 = time.perf_counter()
            resp = opener.open(f"{BASE_URL}/")
            html = resp.read().decode('utf-8')
            t1 = time.perf_counter()
            
            with stats_lock:
                total_requests += 1
                if resp.status == 200:
                    successful_requests += 1
                else:
                    failed_requests += 1
                latencies.append((t1 - t0) * 1000)
            
            # 2. Fetch Login Page to get CSRF token
            t0 = time.perf_counter()
            resp = opener.open(f"{BASE_URL}/login/")
            login_html = resp.read().decode('utf-8')
            t1 = time.perf_counter()
            
            with stats_lock:
                total_requests += 1
                if resp.status == 200:
                    successful_requests += 1
                else:
                    failed_requests += 1
                latencies.append((t1 - t0) * 1000)
                
            # Extract CSRF token
            csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', login_html)
            if not csrf_match:
                continue
            csrf_token = csrf_match.group(1)
            
            # 3. Post Login
            post_data = urllib.parse.urlencode({
                'csrfmiddlewaretoken': csrf_token,
                'username': username,
                'password': 'password'
            }).encode('utf-8')
            
            t0 = time.perf_counter()
            resp = opener.open(f"{BASE_URL}/login/", data=post_data)
            resp.read()  # follow redirect
            t1 = time.perf_counter()
            
            with stats_lock:
                total_requests += 1
                if resp.status == 200:
                    successful_requests += 1
                else:
                    failed_requests += 1
                latencies.append((t1 - t0) * 1000)
                
            # 4. Fetch Dashboard
            dashboard_url = f"{BASE_URL}/donations/donor/" if role == 'Donor' else f"{BASE_URL}/donations/ngo/"
            t0 = time.perf_counter()
            resp = opener.open(dashboard_url)
            resp.read()
            t1 = time.perf_counter()
            
            with stats_lock:
                total_requests += 1
                if resp.status == 200:
                    successful_requests += 1
                else:
                    failed_requests += 1
                latencies.append((t1 - t0) * 1000)
            
            # Brief pause to space out queries
            time.sleep(0.05)
            
        except Exception as e:
            with stats_lock:
                total_requests += 1
                failed_requests += 1
            time.sleep(0.1)

def main():
    print(f"Starting Stress test against: {BASE_URL}")
    print(f"Simulating 16 concurrent users (active threads) for {TEST_DURATION} seconds...")
    
    # 16 demo users to distribute roles
    users = [
        ('donor1', 'Donor'),
        ('ngo1', 'NGO'),
        ('donor2', 'Donor'),
        ('ngo2', 'NGO'),
    ] * 4  # 16 users
    
    threads = []
    t_start = time.time()
    
    for i, (username, role) in enumerate(users):
        t = threading.Thread(target=user_session_worker, args=(i, username, role))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    duration = time.time() - t_start
    
    print("\n=== STRESS TEST RESULTS ===")
    print(f"Total Duration:     {duration:.2f} seconds")
    print(f"Total Requests:     {total_requests}")
    print(f"Successful (200):   {successful_requests}")
    print(f"Failed/Errors:      {failed_requests}")
    
    if total_requests > 0:
        avg_qps = total_requests / duration
        avg_lat = sum(latencies) / len(latencies)
        min_lat = min(latencies)
        max_lat = max(latencies)
        print(f"Achieved QPS:       {avg_qps:.2f} requests/sec")
        print(f"Average Latency:    {avg_lat:.2f} ms")
        print(f"Min Latency:        {min_lat:.2f} ms")
        print(f"Max Latency:        {max_lat:.2f} ms")
        
        # Verify correctness
        error_rate = (failed_requests / total_requests) * 100
        print(f"Error Rate:         {error_rate:.2f}%")
        
        if error_rate < 1.0:
            print("\nSTATUS: SUCCESS - System is highly stable under stress!")
        else:
            print("\nSTATUS: WARNING - High error rates detected!")
            sys.exit(1)
    else:
        print("No requests executed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
