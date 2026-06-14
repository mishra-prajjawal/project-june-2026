import queue
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from events.sse import sse_manager

def sse_stream(request):
    """
    Generator that registers a client queue, waits for broadcasted messages,
    and yields them to the client. Periodically yields keep-alive comments.
    """
    q = sse_manager.register_client()
    try:
        # Initial connection acknowledgement
        yield "event: connected\ndata: {\"status\": \"ok\"}\n\n"
        
        while True:
            try:
                # Wait for broadcast messages with a timeout
                msg = q.get(timeout=15)
                yield msg
            except queue.Empty:
                # Send keepalive to prevent connection timeouts
                yield ": keepalive\n\n"
    except GeneratorExit:
        # Normal disconnection of stream
        pass
    finally:
        sse_manager.unregister_client(q)

@csrf_exempt
def sse_events(request):
    """
    View returning the SSE text/event-stream.
    """
    response = StreamingHttpResponse(sse_stream(request), content_type="text/event-stream")
    # Standard headers for event streams
    response['Cache-Control'] = 'no-cache, must-revalidate'
    response['X-Accel-Buffering'] = 'no'  # Prevents Nginx buffering
    return response
