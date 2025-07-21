from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta, date

from .models import OffSiteItem, BranchInspectionSubmission, BranchInspectionComment, BranchExtension
from .utils import is_branch_user, is_crm_user, is_monitoring_user
from audit_workflow.models import Branch



@login_required
def offsite_commenting(request):
    user = request.user
    if not is_branch_user(user):
        return render(request, 'BranchInspection/error.html', {'message': 'You are not allowed to comment on inspections.'})

    branch = user.branch
    submission, _ = BranchInspectionSubmission.objects.get_or_create(
        branch=branch,
        submitted_by=user,
    )

    all_items = list(OffSiteItem.objects.order_by('id'))
    comments = BranchInspectionComment.objects.filter(submission=submission, user=user)
    comment_map = {c.item.id: c.comment for c in comments}

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
    status = submission.get_status_display()
    context = {
        'categorized_items': formatted_categories,
        'comment_map': comment_map,
        'submission': submission,
        'can_comment': not submission.finalized and submission.is_submission_allowed(),

    'status': status,
    }

    return render(request, 'BranchInspection/offsite_commenting.html', context)


@require_POST
@login_required
def submit_offsite_comment(request):
    user = request.user
    if not is_branch_user(user):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})

    item_id = request.POST.get('item_id')
    comment_text = request.POST.get('comment')

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


@login_required
def create_branch_inspection_submission(request):
    if not is_branch_user(request.user):
        return redirect('audit_workflow:login')

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

        BranchInspectionSubmission.objects.create(
            branch=request.user.branch,
            submitted_by=request.user,
            month=month,
            comment="",
        )
        messages.success(request, f'Submission created for {month.strftime("%B %Y")}.')
        return redirect('BranchInspection:offsite_commenting')

    return render(request, 'BranchInspection/create_submission.html')


@login_required
def regional_manager_submission_list(request):
    if not is_crm_user(request.user):
        return redirect('audit_workflow:login')

    submissions = BranchInspectionSubmission.objects.filter(
        branch__region=request.user.branch.region,
        branch__type='branch'
    ).order_by('-month')

    return render(request, 'BranchInspection/manager_submission_list.html', {'submissions': submissions})


from django.utils.timezone import now

@login_required
# def set_extension(request, submission_id):
#     if not is_crm_user(request.user):
#         return redirect('audit_workflow:login')
#
#     submission = get_object_or_404(BranchInspectionSubmission, id=submission_id)
#
#     if request.method == 'POST':
#         extra_days = int(request.POST.get('extra_days', 0))
#         if 1 <= extra_days <= 7:
#             submission.extended_until = now().date() + timedelta(days=extra_days)
#             submission.save()
#             return redirect('BranchInspection:regional_manager_submission_list')
#
#     return render(request, 'BranchInspection/set_extension.html', {
#         'submission': submission,
#         'now': now().date(),
#     })


@require_POST
@login_required
def set_extension(request, branch_id):
    if not is_crm_user(request.user):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    days = int(request.POST.get('extra_days', 0))
    if days < 1 or days > 7:
        return JsonResponse({'error': 'Day range must be between 1 and 7'}, status=400)

    current_month = timezone.now().date().replace(day=1)
    extended_until = timezone.now().date() + timedelta(days=days)

    obj, created = BranchExtension.objects.update_or_create(
        branch_id=branch_id,
        month=current_month,
        defaults={
            'extended_until': extended_until,
            'granted_by': request.user
        }
    )

    return JsonResponse({'message': f'Extension granted until {extended_until.strftime("%b %d")}'})




@require_POST
@login_required
def forward_to_monitoring(request, submission_id):
    if not is_crm_user(request.user):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    from .models import BranchInspectionSubmission

    submission = BranchInspectionSubmission.objects.get(id=submission_id)

    if not submission.finalized:
        return JsonResponse({'error': 'Submission is not finalized'}, status=400)

    submission.forwarded_to_dgm = True
    submission.returned_by_crm = False
    submission.save()

    return JsonResponse({'message': 'Submission forwarded to DGM Monitoring'})




@login_required
def finalize_submission(request):
    user = request.user
    if not is_branch_user(user):
        return redirect('audit_workflow:login')

    submission = BranchInspectionSubmission.objects.filter(
        branch=user.branch,
        submitted_by=user,
        month__month=timezone.now().month,
        month__year=timezone.now().year
    ).first()

    if not submission:
        messages.error(request, "No submission found to finalize.")
        return redirect('BranchInspection:offsite_commenting')

    all_items = OffSiteItem.objects.all()
    comments = BranchInspectionComment.objects.filter(submission=submission, user=user)

    if not submission.is_submission_allowed():
        messages.error(request, "Submission deadline has passed and no extension granted.")
        return redirect('BranchInspection:offsite_commenting')

    if comments.count() < all_items.count():
        messages.error(request, "Please comment on all items before finalizing.")
        return redirect('BranchInspection:offsite_commenting')

    if submission and not submission.finalized:
        submission.finalized = True
        submission.finalized_at = timezone.now()

        # Reset is_returned if it's a resubmission after return
        if submission.is_returned:
            submission.is_returned = False

        submission.save()
        # send notification to CRM etc.

    messages.success(request, "Submission finalized successfully.")
    return redirect('BranchInspection:inspection_dashboard', submission_id=submission.id)


@login_required
def view_submission_detail(request, submission_id):
    if not is_crm_user(request.user):
        return redirect('audit_workflow:login')

    submission = get_object_or_404(BranchInspectionSubmission, id=submission_id)

    all_items = OffSiteItem.objects.order_by('id')
    comments = BranchInspectionComment.objects.filter(submission=submission)
    comment_map = {c.item.id: c.comment for c in comments}

    categorized_items = {}
    for item in all_items:
        cat = item.item_type
        categorized_items.setdefault(cat, []).append(item)

    formatted_categories = {}
    for cat_key, items in categorized_items.items():
        display_name = cat_key.replace("_", " ").title()
        formatted_categories[cat_key] = {
            'display_name': display_name,
            'items': items
        }

    context = {
        'submission': submission,
        'comment_map': comment_map,
        'categorized_items': formatted_categories,
        'is_finalized': submission.finalized,
    }
    return render(request, 'BranchInspection/view_submission_detail.html', context)

from .utils import is_branch_user, is_crm_user, is_monitoring_user


# def inspection_dashboard(request, submission_id):
#     submission = get_object_or_404(BranchInspectionSubmission, id=submission_id)
#     user = request.user
#
#     # Role checks
#     branch_user = is_branch_user(user)
#     crm_user = is_crm_user(user)
#     monitoring_user = is_monitoring_user(user)
#
#     # Core comment stats
#     comments = submission.comments.select_related('item', 'user')
#     total_items = submission.get_items().count()
#     commented_items = comments.values('item').distinct().count()
#     replied = submission.monitoring_replies.exists()
#
#     # Optional: Categorize items by item_type (for template rendering)
#     all_items = OffSiteItem.objects.order_by('id')
#     categorized_items = {}
#     for item in all_items:
#         categorized_items.setdefault(item.item_type, []).append(item)
#
#     formatted_categories = {
#         cat_key: {
#             'display_name': cat_key.replace("_", " ").title(),
#             'items': items
#         } for cat_key, items in categorized_items.items()
#     }
#
#     context = {
#         'submission': submission,
#         'total_items': total_items,
#         'commented_items': commented_items,
#         'replied': replied,
#         'is_branch_user': branch_user,
#         'is_crm_user': crm_user,
#         'is_monitoring_user': monitoring_user,
#         'submission_status': submission.get_status_display(),
#         'is_finalized': submission.finalized,
#         'categorized_items': formatted_categories,  # Optional, use in template if needed
#     }
#
#     return render(request, 'BranchInspection/dashboard.html', context)
@login_required
def inspection_dashboard(request, submission_id):
    submission = get_object_or_404(BranchInspectionSubmission, id=submission_id)
    user = request.user

    # Role checks (make sure these helpers are accurate)
    branch_user = is_branch_user(user)
    crm_user = is_crm_user(user)
    monitoring_user = is_monitoring_user(user)

    # Core comment stats
    comments = submission.comments.select_related('item', 'user')  # Ensure related_name='comments' exists
    total_items = submission.get_items().count()
    commented_items = comments.values('item').distinct().count()
    replied = bool(submission.monitoring_reply)

    # Categorized item mapping
    all_items = submission.get_items().order_by('id')
    categorized_items = {}
    for item in all_items:
        categorized_items.setdefault(item.item_type, []).append(item)

    formatted_categories = {
        cat_key: {
            'display_name': cat_key.replace("_", " ").title(),
            'items': items
        } for cat_key, items in categorized_items.items()
    }

    context = {
        'submission': submission,
        'total_items': total_items,
        'commented_items': commented_items,
        'replied': replied,
        'is_branch_user': branch_user,
        'is_crm_user': crm_user,
        'is_monitoring_user': monitoring_user,
        'submission_status': submission.get_status_display(),
        'is_finalized': submission.finalized,
        'categorized_items': formatted_categories,
    }

    return render(request, 'BranchInspection/dashboard.html', context)

@require_POST
@login_required
def return_to_branch(request, submission_id):
    if not is_crm_user(request.user):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    from .models import BranchInspectionSubmission, Notification

    submission = BranchInspectionSubmission.objects.get(id=submission_id)

    submission.status = True
    submission.forwarded_to_dgm = False
    submission.finalized = False
    submission.returned_at = timezone.now()
    submission.save()

    branch_users = submission.branch.user_set.all()
    for user in branch_users:
        Notification.objects.create(
            recipient=user,
            submission=submission,
            message=f"Your submission for {submission.month.strftime('%B %Y')} has been returned by the regional manager."
        )

    return JsonResponse({'message': 'Submission returned to branch and users notified'})




@require_POST
@login_required
def monitoring_reply(request, submission_id):
    submission = get_object_or_404(BranchInspectionSubmission, id=submission_id)
    if request.user.email != "dgmmonitoring@gmail.com":
        return HttpResponseForbidden()

    reply_text = request.POST.get("reply", "").strip()
    if reply_text:
        submission.monitoring_reply = reply_text
        submission.save()

    return redirect('BranchInspection:inspection_dashboard', submission_id=submission.id)


def submission_overview(request):
    user = request.user
    today = date.today()
    current_month = today.replace(day=1)

    # Determine user role
    if is_branch_user(user):
        role = 'branch'
        branches = Branch.objects.filter(id=user.branch_id)
    elif is_crm_user(user):
        role = 'crm'
        branches = Branch.objects.filter(region=user.region)
    elif is_monitoring_user(user):
        role = 'dgmmonitoring'
        branches = Branch.objects.all()
    else:
        role = 'unknown'
        branches = Branch.objects.none()

    # Get this month's submissions and extensions
    # submissions = BranchInspectionSubmission.objects.filter(
    #     branch__in=branches, month=current_month
    # ).select_related('branch')
    submissions = BranchInspectionSubmission.objects.filter(
        branch__in=branches,
        month__month=today.month,
        month__year=today.year
    ).select_related('branch')

    # extensions = BranchExtension.objects.filter(
    #     branch__in=branches, month=current_month
    # )
    extensions = BranchExtension.objects.filter(
        branch__in=branches,
        month__month=today.month,
        month__year=today.year
    )

    # Map for quick lookup
    submissions_map = {s.branch_id: s for s in submissions}
    extensions_map = {e.branch_id: e for e in extensions}

    dashboard_data = []
    late_submission_alert = False  # For branch user alert

    for branch in branches:
        submission = submissions_map.get(branch.id)
        extension = extensions_map.get(branch.id)

        # Determine if today > 10th and no submission
        alert_due = today.day > 10 and (not submission or not submission.submitted_by)

        # Show alert only if current user is branch user for their own branch
        if role == 'branch' and branch.id == user.branch_id and alert_due:
             late_submission_alert = True

        dashboard_data.append({
            'branch': branch,
            'submission': submission,
            'extension_deadline': extension.extended_until  if extension else None,
            'alert_due': alert_due,

            'can_submit': role == 'branch' and branch.id == user.branch_id and not (submission and submission.finalized),
            'can_grant_extension': role == 'crm' and not (submission and submission.finalized),
            'can_forward': role == 'crm' and submission and submission.finalized and not submission.is_forwarded,
            'can_return': role == 'crm' and submission and submission.finalized,

            'view_only': role == 'dgmmonitoring',
        })

    context = {
        'dashboard_data': dashboard_data,
        'current_month': current_month,
        'user_role': role,
        'late_submission_alert': late_submission_alert,
        # Add for filtering form if you implement it:
        'all_regions': Branch.objects.values_list('region', flat=True).distinct(),
        'all_divisions': Branch.objects.values_list('division', flat=True).distinct(),
    }

    return render(request, 'BranchInspection/submission_overview.html', context)