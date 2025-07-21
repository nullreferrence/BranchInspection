# views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from .models import OffSiteItem, BranchInspectionSubmission, BranchInspectionComment
from audit_workflow.models import Branch



@login_required
def offsite_commenting(request):
    user = request.user
    branch = getattr(user, 'branch', None)

    if not branch:
        return render(request, 'BranchInspection/error.html', {'message': 'User has no associated branch.'})

    submission, _ = BranchInspectionSubmission.objects.get_or_create(
        branch=branch,
        submitted_by=user,
    )

    all_items = list(OffSiteItem.objects.order_by('id'))
    comments = BranchInspectionComment.objects.filter(submission=submission, user=user)
    comment_map = {c.item.id: c.comment for c in comments}

    # Group by category
    categorized_items = {}
    progress = {}

    for item in all_items:
        cat = item.item_type
        categorized_items.setdefault(cat, []).append(item)

    for cat, items in categorized_items.items():
        completed = sum(1 for item in items if item.id in comment_map)
        total = len(items)
        progress[cat] = {
            'completed': completed,
            'total': total
        }

    formatted_categories = {}
    for cat_key, items in categorized_items.items():
        display_name = cat_key.replace("_", " ").title()
        formatted_categories[cat_key] = {
            'display_name': display_name,
            'items': items,
            'progress': progress[cat_key],
        }

    context = {
        'categorized_items': formatted_categories,
        'comment_map': comment_map,
        'submission': submission,
    }

    return render(request, 'BranchInspection/offsite_commenting.html', context)


@require_POST
@login_required

def submit_offsite_comment(request):
    item_id = request.POST.get('item_id')
    comment_text = request.POST.get('comment')
    user = request.user

    item = get_object_or_404(OffSiteItem, id=item_id)
    submission = BranchInspectionSubmission.objects.filter(
        branch=user.branch,
        submitted_by=user,
        month__month=timezone.now().month,
        month__year=timezone.now().year
    ).first()

    if not submission:
        return JsonResponse({'success': False, 'error': 'No active submission for this month.'})

    if not submission.is_submission_allowed():
        return JsonResponse({'success': False, 'error': 'Submission deadline has passed and no extension granted.'})

    BranchInspectionComment.objects.update_or_create(
        submission=submission,
        item=item,
        user=user,
        defaults={'comment': comment_text}
    )

    # Load next item by ID (not item_no)
    all_items = list(OffSiteItem.objects.order_by('id'))
    current_index = next((i for i, it in enumerate(all_items) if it.id == item.id), -1)
    next_item = all_items[current_index + 1] if current_index + 1 < len(all_items) else None

    return JsonResponse({
        'success': True,
        'next_item_id': next_item.id if next_item else None
    })




def get_next_item_id(current_item_id):
    next_item = OffSiteItem.objects.filter(id__gt=current_item_id).order_by('id').first()
    return next_item.id if next_item else None

def create_branch_inspection_submission(request):
    if request.method == 'POST':
        month_str = request.POST.get('month')
        month = datetime.strptime(month_str, '%Y-%m').date().replace(day=1)
        existing = BranchInspectionSubmission.objects.filter(
            branch=request.user.branch,
            submitted_by=request.user,
            month=month
        ).first()

        if existing:
            messages.info(request, 'Submission for this month already exists.')
            return redirect('BranchInspection:offsite_commenting')

        submission = BranchInspectionSubmission.objects.create(
            branch=request.user.branch,
            submitted_by=request.user,
            month=month,
            comment="",
        )
        messages.success(request, f'Submission created for {month.strftime("%B %Y")}.')
        return redirect('BranchInspection:offsite_commenting')  # Adjust as needed

    return render(request, 'BranchInspection/create_submission.html')

@login_required
def regional_manager_submission_list(request):
    if request.user.role != 'manager':
        return redirect('audit_workflow:login')


    submissions = BranchInspectionSubmission.objects.filter(
        branch__region=request.user.region
    ).order_by('-month')

    return render(request, 'BranchInspection/manager_submission_list.html', {'submissions': submissions})

@login_required
def set_extension(request, submission_id):
    if request.user.role != 'manager':
        return redirect('audit_workflow:login')

    submission = get_object_or_404(BranchInspectionSubmission, id=submission_id)


    if request.method == 'POST':
        extra_days = int(request.POST.get('extra_days', 0))
        if 1 <= extra_days <= 7:
            submission.extended_until = timezone.now().date() + timedelta(days=extra_days)
            submission.save()
            return redirect('BranchInspection:regional_manager_submission_list')

    return render(request, 'BranchInspection/set_extension.html', {'submission': submission})

@login_required
def forward_to_monitoring(request, submission_id):
    if request.user.role != 'manager':
        return redirect('audit_workflow:login')

    submission = get_object_or_404(BranchInspectionSubmission, id=submission_id)


    submission.forwarded_to_monitoring = True
    submission.save()
    return redirect('BranchInspection:regional_manager_submission_list')

