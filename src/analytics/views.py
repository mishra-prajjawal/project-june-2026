import re
import datetime
from collections import defaultdict
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from donations.models import Donation, DonationStatus, QualityFeedback

@login_required
def impact_report(request):
    """
    Computes and renders database-agnostic aggregates of platform servings,
    NGO quality checks, and monthly trends for Chart.js rendering.
    """
    # 1. Platform-wide stats
    collected_donations = Donation.objects.filter(status=DonationStatus.COLLECTED)
    total_listings_saved = collected_donations.count()

    total_servings = 0
    for d in collected_donations:
        match = re.search(r'\d+', d.quantity)
        if match:
            total_servings += int(match.group())
        else:
            total_servings += 10  # Standard fallback

    # Calculate kilograms (assume 0.3kg per serving equivalent)
    total_kgs = round(total_servings * 0.3, 1)

    # 2. Quality Approval Rate
    total_feedback = QualityFeedback.objects.count()
    good_feedback = QualityFeedback.objects.filter(acceptable=True).count()
    quality_rate = round((good_feedback / total_feedback) * 100, 1) if total_feedback > 0 else 100.0

    # 3. Monthly Saved Servings (Past 6 Months)
    now = timezone.now()
    monthly_data = defaultdict(int)

    # Pre-populate past 6 months to guarantee clean labels even with empty data
    for i in range(6):
        # Estimate month offsets using timedelta
        month_date = now - datetime.timedelta(days=i * 30)
        month_key = month_date.strftime('%b %Y')
        monthly_data[month_key] = 0

    for d in collected_donations:
        if d.collected_at:
            month_key = d.collected_at.strftime('%b %Y')
            if month_key in monthly_data:
                match = re.search(r'\d+', d.quantity)
                servings = int(match.group()) if match else 10
                monthly_data[month_key] += servings

    # Sort keys chronologically
    sorted_months = sorted(
        monthly_data.keys(),
        key=lambda m: datetime.datetime.strptime(m, '%b %Y')
    )
    monthly_labels = sorted_months
    monthly_values = [monthly_data[m] for m in sorted_months]

    # 4. User-Specific Stats (if Donor)
    my_collected = collected_donations.filter(donor=request.user)
    my_servings = 0
    for d in my_collected:
        match = re.search(r'\d+', d.quantity)
        my_servings += int(match.group()) if match else 10

    context = {
        'metrics': {
            'total_listings_saved': total_listings_saved,
            'total_servings': total_servings,
            'total_kgs': total_kgs,
            'quality_rate': quality_rate,
            'my_listings': my_collected.count(),
            'my_servings': my_servings,
        },
        'chart_data': {
            'labels': monthly_labels,
            'values': monthly_values,
        }
    }
    
    return render(request, 'analytics/report.html', context)
