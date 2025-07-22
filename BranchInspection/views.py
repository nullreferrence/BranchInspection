from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta, date

from .models import OffSiteItem, BranchInspectionSubmission, BranchInspectionComment, BranchExtension, MonitoringReply, \
    Notification, RegionReplyFinalization


from audit_workflow.models import Branch
from django.db.models import Q
from django.utils.timezone import now
from collections import defaultdict
from django.db.models import Prefetch
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .forms import OffSiteItemForm
from django.http import HttpResponseForbidden
from collections import defaultdict
from .utils import is_branch_user, is_crm_user, is_monitoring_user

@login_required
def offsite_commenting(request):
    user = request.user
    if not is_branch_user(user):
        return render(request, 'BranchInspection/error.html', {'message': 'You are not allowed to comment on inspections.'})

    branch = user.branch
    month_start = timezone.now().date().replace(day=1)
    submission, _ = BranchInspectionSubmission.objects.get_or_create(
        branch=branch,
        submitted_by=user,
        month=month_start
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



@require_POST
@login_required
def set_extension(request, branch_id):
    if not is_crm_user(request.user):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    try:
        days = int(request.POST.get('extra_days', 0))
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid number of days'}, status=400)

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

    return JsonResponse({
        'message': f'Extension granted until {extended_until.strftime("%Y-%m-%d")}',
        'extended_until': extended_until.strftime('%Y-%m-%d'),
        'created': created
    })




@require_POST
@login_required
def forward_to_monitoring(request, submission_id):
    if not is_crm_user(request.user):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    submission = BranchInspectionSubmission.objects.get(id=submission_id)

    if not submission.finalized:
        return JsonResponse({'error': 'Submission is not finalized'}, status=400)

    submission.is_forwarded = True  # ✅ Correct field name
    submission.is_returned = False  # Optional reset if re-forwarded
    submission.forwarded_at = timezone.now()  # ✅ Track forward time
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




from django.db.models import Q

@login_required
def inspection_dashboard(request, submission_id):
    submission = get_object_or_404(BranchInspectionSubmission, id=submission_id)
    user = request.user

    # Role checks
    branch_user = is_branch_user(user)
    crm_user = is_crm_user(user)
    monitoring_user = is_monitoring_user(user)

    # Comments by branch
    comments_qs = BranchInspectionComment.objects.filter(submission=submission).select_related('item', 'user')
    total_items = submission.get_items().count()
    commented_items = comments_qs.values('item').distinct().count()
    replied = bool(submission.monitoring_reply)

    # Map comments to item_id
    comment_map = {}
    for comment in comments_qs:
        comment_map.setdefault(comment.item_id, []).append(comment)

    # Categorize items
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

    # Monitoring replies
    monitoring_replies = MonitoringReply.objects.filter(submission=submission).select_related('item')
    seen_or_replied_item_ids = set(
        monitoring_replies.filter(Q(seen=True) | ~Q(reply="")).values_list('item_id', flat=True)
    )
    replied_items = len(seen_or_replied_item_ids)
    monitoring_reply_map = {int(mr.item.id): mr for mr in monitoring_replies}

    # Finalization condition
    can_finalize_reply = (
        user.email == "dgmmonitoring@krishibank.org.bd"
        and submission.is_forwarded
        and replied_items == total_items
        and not submission.monitoring_reply  # not yet finalized
    )

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
        'comment_map': comment_map,
        'monitoring_reply_map': monitoring_reply_map,
        'replied_items': replied_items,
        'all_items_seen_or_replied': replied_items == total_items,
        'can_finalize_reply': can_finalize_reply,
    }

    return render(request, 'BranchInspection/dashboard.html', context)



@require_POST
@login_required
def return_to_branch(request, submission_id):
    if not is_crm_user(request.user):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    submission = get_object_or_404(BranchInspectionSubmission, id=submission_id)
    comment = request.POST.get('return_comment', '').strip()

    if not comment:
        return JsonResponse({'error': 'Return comment is required.'}, status=400)

    submission.is_returned = True
    submission.forwarded_to_dgm = False
    submission.finalized = False
    submission.returned_at = timezone.now()
    submission.return_comment = comment  # ✅ This was missing
    submission.save()

    for user in submission.branch.user_set.all():
        Notification.objects.create(
            recipient=user,
            submission=submission,
            message=f"Your submission for {submission.month.strftime('%B %Y')} has been returned by the CRM."
        )

    return JsonResponse({'message': 'Returned with comment'})




@login_required
def submission_overview(request):
    user = request.user
    today = date.today()
    current_month = today.replace(day=1)

    # Clean up old extensions
    BranchExtension.objects.filter(month__lt=current_month).delete()

    # Get filters from request
    selected_region = request.GET.get('region')
    selected_division = request.GET.get('division')
    selected_branch_id = request.GET.get('branch')

    if is_branch_user(user):
        role = 'branch'
        branches = Branch.objects.filter(id=user.branch_id)

    elif is_crm_user(user):
        role = 'crm'
        selected_region = user.region
        selected_division = user.division
        #branches = Branch.objects.filter(region=selected_region, division=selected_division)
        branches = Branch.objects.filter(
            region=selected_region,
            division=selected_division,
            type__in=['branch', 'corporate']
        )
    elif is_monitoring_user(user):
        role = 'dgmmonitoring'
        branches = Branch.objects.filter(type__in=['branch', 'corporate'])
        if selected_division:
            branches = branches.filter(division=selected_division)
        if selected_region:
            branches = branches.filter(region=selected_region)
        if selected_branch_id:
            branches = branches.filter(id=selected_branch_id)
    else:
        role = 'unknown'
        branches = Branch.objects.none()

    submissions = BranchInspectionSubmission.objects.filter(
        branch__in=branches,
        month__year=today.year,
        month__month=today.month
    ).select_related('branch')

    extensions = BranchExtension.objects.filter(
        branch__in=branches,
        month__year=today.year,
        month__month=today.month
    )

    submissions_map = {s.branch_id: s for s in submissions}
    extensions_map = {e.branch_id: e for e in extensions}

    dashboard_data = []
    late_submission_alert = False

    for branch in branches:
        submission = submissions_map.get(branch.id)
        extension = extensions_map.get(branch.id)

        alert_due = today.day > 10 and (not submission or not submission.submitted_by)

        if role == 'branch' and branch.id == user.branch_id and alert_due:
            late_submission_alert = True

        total_items = submission.get_items().count() if submission else 0

        # Use the submission's own fields for reply status:
        is_replied = bool(submission.monitoring_reply) if submission else False
        is_reply_finalized = submission.is_reply_finalized if submission else False

        dashboard_data.append({
            'branch': branch,
            'submission': submission,
            'extension_deadline': extension.extended_until if extension else None,
            'alert_due': alert_due,
            'can_submit': role == 'branch' and branch.id == user.branch_id and not (
                    submission and submission.finalized),
            'can_grant_extension': role == 'crm' and not (submission and submission.finalized),
            'can_forward': role == 'crm' and submission and submission.finalized and not submission.is_forwarded,
            'can_return': role == 'crm' and submission and submission.finalized,
            'view_only': role == 'dgmmonitoring',
            'total_items': total_items,
            'is_replied': is_replied,
            'is_reply_finalized': is_reply_finalized,
        })

    context = {
        'dashboard_data': dashboard_data,
        'current_month': current_month,
        'user_role': role,
        'late_submission_alert': late_submission_alert,
        'all_divisions': Branch.objects.values_list('division', flat=True).distinct().order_by('division'),
        'selected_region': selected_region,
        'selected_division': selected_division,
        'selected_branch': int(selected_branch_id) if selected_branch_id else None,
    }

    if role == 'dgmmonitoring':
        context['all_regions'] = Branch.objects.filter(division=selected_division).values_list('region', flat=True).distinct().order_by('region') if selected_division else []
        #context['all_branches'] = Branch.objects.filter(division=selected_division, region=selected_region).order_by('name') if selected_region else []
        context['all_branches'] = Branch.objects.filter(
            division=selected_division,
            region=selected_region,
            type__in=['branch', 'corporate']
        ).order_by('name') if selected_region else []

    return render(request, 'BranchInspection/submission_overview.html', context)
# def submission_overview(request):
#     user = request.user
#     today = date.today()
#     current_month = today.replace(day=1)
#
#     # Clean up old extensions
#     BranchExtension.objects.filter(month__lt=current_month).delete()
#
#     # Defaults
#     selected_region = ""
#     selected_division = ""
#
#     # Branch filtering based on role
#     if is_branch_user(user):
#         role = 'branch'
#         branches = Branch.objects.filter(id=user.branch_id)
#
#     elif is_crm_user(user):
#         role = 'crm'
#         selected_region = user.region
#         selected_division = user.division
#         branches = Branch.objects.filter(region=selected_region, division=selected_division)
#
#     elif is_monitoring_user(user):
#         role = 'dgmmonitoring'
#         selected_region = request.GET.get('region')
#         selected_division = request.GET.get('division')
#         branches = Branch.objects.all()
#         if selected_region:
#             branches = branches.filter(region=selected_region)
#         if selected_division:
#             branches = branches.filter(division=selected_division)
#     else:
#         role = 'unknown'
#         branches = Branch.objects.none()
#
#     submissions = BranchInspectionSubmission.objects.filter(
#         branch__in=branches,
#         month__year=today.year,
#         month__month=today.month
#     ).select_related('branch')
#
#     extensions = BranchExtension.objects.filter(
#         branch__in=branches,
#         month__year=today.year,
#         month__month=today.month
#     )
#
#     submissions_map = {s.branch_id: s for s in submissions}
#     extensions_map = {e.branch_id: e for e in extensions}
#
#     dashboard_data = []
#     late_submission_alert = False
#
#     for branch in branches:
#         submission = submissions_map.get(branch.id)
#         extension = extensions_map.get(branch.id)
#
#         alert_due = today.day > 10 and (not submission or not submission.submitted_by)
#
#         if role == 'branch' and branch.id == user.branch_id and alert_due:
#             late_submission_alert = True
#
#         all_items = submission.get_items().count() if submission else 0
#         replied_count = MonitoringReply.objects.filter(submission=submission).count() if submission else 0
#         all_replied = (replied_count >= all_items) if all_items else False
#
#         dashboard_data.append({
#             'branch': branch,
#             'submission': submission,
#             'extension_deadline': extension.extended_until if extension else None,
#             'alert_due': alert_due,
#
#             'can_submit': role == 'branch' and branch.id == user.branch_id and not (submission and submission.finalized),
#             'can_grant_extension': role == 'crm' and not (submission and submission.finalized),
#             'can_forward': role == 'crm' and submission and submission.finalized and not submission.is_forwarded,
#             'can_return': role == 'crm' and submission and submission.finalized,
#
#             'view_only': role == 'dgmmonitoring',
#             'all_replied': all_replied,
#         })
#
#     context = {
#         'dashboard_data': dashboard_data,
#         'current_month': current_month,
#         'user_role': role,
#         'late_submission_alert': late_submission_alert,
#         'all_regions': Branch.objects.values_list('region', flat=True).distinct().order_by('region'),
#         'all_divisions': Branch.objects.values_list('division', flat=True).distinct().order_by('division'),
#         'selected_region': selected_region,
#         'selected_division': selected_division,
#     }
#
#     if role == 'dgmmonitoring':
#         region_finalization_map = {}
#         for region in branches.values_list('region', flat=True).distinct():
#             region_branches = branches.filter(region=region)
#             region_subs = [submissions_map.get(b.id) for b in region_branches if submissions_map.get(b.id)]
#             region_finalization_map[region] = all(
#                 s.monitoring_reply == "✅ Replied to all items" for s in region_subs
#             ) if region_subs else False
#
#         context['region_finalization_map'] = region_finalization_map
#
#     return render(request, 'BranchInspection/submission_overview.html', context)






@login_required

def crm_monitoring_reply_report(request):
    user = request.user
    today = date.today()
    selected_region = request.GET.get('region') or getattr(user, 'region', None)
    #selected_division = request.GET.get('division') or getattr(user, 'division', None)

    if not selected_region:
        messages.warning(request, "Region or division not specified.")
        return redirect('BranchInspection:submission_overview')

    # Block branch users only
    if not (is_crm_user(user) or is_monitoring_user(user)):
        return HttpResponseForbidden("Unauthorized")

    # Get all branches in region/division
    branches = Branch.objects.filter(region=selected_region, type='branch')
    total_branch_count = branches.count()

    # Count only submissions that are finalized properly
    finalized_submissions = BranchInspectionSubmission.objects.filter(
        branch__in=branches,
        finalized=True,
        is_forwarded=True,
        is_reply_finalized=True,
        month__year=today.year,
        month__month=today.month
    )
    finalized_branch_ids = finalized_submissions.values_list('branch_id', flat=True).distinct()
    finalized_branch_count = finalized_branch_ids.count()

    all_finalized = finalized_branch_count == total_branch_count and total_branch_count > 0

    # Restrict CRM only (NOT dgmmonitoring)
    if is_crm_user(user) and not all_finalized:
        return render(request, 'BranchInspection/crm_monitoring_reply_denied.html', {
            'region': selected_region,
            #'division': selected_division
        })

    # Get all replies — even if partial
    replies = MonitoringReply.objects.select_related('submission__branch', 'item').filter(
        submission__branch__region=selected_region,
        #submission__branch__division=selected_division,
        submission__month__year=today.year,
        submission__month__month=today.month
    ).order_by('item__item_type', 'reply', 'item__name', 'submission__branch__bn_name')

    # Group by type → reply → item → branches
    grouped_by_type = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))

    for r in replies:
        item_type = r.item.item_type
        reply_text = r.reply.strip()
        item_name = r.item.name.strip()
        branch_name = r.submission.branch.bn_name or r.submission.branch.name
        grouped_by_type[item_type][reply_text][item_name].add(branch_name)

    type_wise_reports = []
    for item_type, reply_blocks in grouped_by_type.items():
        report_rows = []
        serial = 1
        for reply_text, items_dict in sorted(reply_blocks.items(), key=lambda x: x[0]):
            item_names = []
            all_branches = set()
            for item_name, branches in items_dict.items():
                item_names.append(item_name)
                all_branches.update(branches)
            report_rows.append({
                'serial': serial,
                'branches': sorted(all_branches),
                'items': item_names,
                'reply': reply_text
            })
            serial += 1
        type_wise_reports.append({
            'item_type': item_type.replace("_", " ").title(),
            'rows': report_rows
        })
    print("Replies count:", replies.count())
    context = {
        'type_wise_reports': type_wise_reports,
        'region': selected_region,
        #'division': selected_division,
        'can_finalize': is_monitoring_user(user) and not all_finalized,
        'partial_warning': not all_finalized,
    }

    return render(request, 'BranchInspection/crm_monitoring_reply_report.html', context)




@require_POST
@login_required
def finalize_dgm_region(request):
    if request.user.role != 'dgmmonitoring':
        return HttpResponseForbidden("Unauthorized")

    region = request.POST.get("region")
    division = request.POST.get("division")

    if not region:
        messages.error(request, "Region is required.")
        return redirect("BranchInspection:submission_overview")

    current_month = timezone.now().date().replace(day=1)

    # Filter branches by region and division
    branches = Branch.objects.filter(region=region, division=division, type__in=['branch', 'corporate'])
    submissions = BranchInspectionSubmission.objects.filter(branch__in=branches, month=current_month)

    if not submissions.exists():
        messages.warning(request, f"No submissions found for region '{region}'.")
        return redirect("BranchInspection:submission_overview")

    # Check if any submission is missing forward or finalized reply
    for sub in submissions:
        if not sub.is_forwarded:
            messages.error(request, f"❌ {sub.branch.name} not forwarded by CRM.")
            return redirect("BranchInspection:submission_overview")
        if not sub.is_reply_finalized or sub.monitoring_reply != "✅ Replied to all items":
            messages.error(request, f"❌ Monitoring reply incomplete for {sub.branch.name}.")
            return redirect("BranchInspection:submission_overview")

    # All passed, finalize region
    for sub in submissions:
        sub.is_region_finalized = True
        sub.region_finalized_at = timezone.now()
        sub.save(update_fields=['is_region_finalized', 'region_finalized_at'])

    messages.success(request, f"✅ Region '{region}' successfully finalized.")
    return redirect("BranchInspection:submission_overview")




@require_POST
@login_required
def finalize_branch_monitoring(request, submission_id):
    if not is_monitoring_user(request.user):
        return HttpResponseForbidden("Unauthorized")

    submission = get_object_or_404(BranchInspectionSubmission, id=submission_id)

    total_items = submission.get_items().count()
    replied_count = MonitoringReply.objects.filter(submission=submission).count()

    if replied_count >= total_items:
        submission.monitoring_reply = "✅ Replied to all items"
        submission.is_reply_finalized = True
        submission.save()
        messages.success(request, f"{submission.branch.name} finalized.")
    else:
        messages.error(request, f"Not all items are replied for {submission.branch.name}.")

    return redirect('BranchInspection:submission_overview')


@require_POST
@login_required
def monitoring_reply_item(request, submission_id, item_id):
    submission = get_object_or_404(BranchInspectionSubmission, id=submission_id)
    item = get_object_or_404(OffSiteItem, id=item_id)

    if not is_monitoring_user(request.user):
        return HttpResponseForbidden("You are not authorized to reply.")

    if not submission.finalized or not submission.is_forwarded:
        messages.error(request, "Submission must be finalized and forwarded by CRM.")
        return redirect('BranchInspection:inspection_dashboard', submission_id=submission_id)

    reply_text = request.POST.get("reply", "").strip()
    seen_only = request.POST.get("seen_only") == "on"

    MonitoringReply.objects.update_or_create(
        submission=submission,
        item=item,
        defaults={
            'reply': reply_text if not seen_only else "",
            'seen': True,  # ✅ Always mark as seen
            'replied_by': request.user,
            'replied_at': timezone.now(),
        }
    )

    messages.success(request, "Reply saved and marked as seen.")
    return redirect('BranchInspection:inspection_dashboard', submission_id=submission_id)


@login_required
def undo_finalize_reply(request, submission_id):
    submission = get_object_or_404(BranchInspectionSubmission, id=submission_id)

    if request.user.email != "dgmmonitoring@krishibank.org.bd":
        return HttpResponseForbidden("Only DGM Monitoring can undo finalization.")

    if request.method == "POST":
        submission.is_reply_finalized = False
        submission.replied_at = None
        submission.replied_by = None
        submission.monitoring_reply = None
        submission.save()
        messages.success(request, "Reply finalization undone.")
        return redirect('BranchInspection:inspection_dashboard', submission_id=submission.id)

    return redirect('BranchInspection:inspection_dashboard', submission_id=submission.id)



def get_region_branch_options(request):
    division = request.GET.get('division')
    region = request.GET.get('region')

    filters = {}
    if division:
        filters['division'] = division
    if region:
        filters['region'] = region

    regions = Branch.objects.filter(**{ 'division': division }).values_list('region', flat=True).distinct().order_by('region') if division else []
    branches = Branch.objects.filter(**filters).values('id', 'name').order_by('name') if filters else []

    return JsonResponse({
        'regions': list(regions),
        'branches': list(branches)
    })


@login_required
def manage_offsite_items(request):
    if not is_monitoring_user(request.user):
        messages.error(request, "Unauthorized Access")
        return redirect("BranchInspection:submission_overview")  # or custom 403 page

    items = OffSiteItem.objects.all().order_by('item_type', 'item_no')
    return render(request, "BranchInspection/manage_offsite_items.html", {
        "items": items
    })


# views.py

@login_required
def add_offsite_item(request):
    if not is_monitoring_user(request.user):
        return redirect('BranchInspection:submission_overview')

    if request.method == 'POST':
        form = OffSiteItemForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Item added successfully.")
            return redirect('manage_offsite_items')
    else:
        form = OffSiteItemForm()

    return render(request, 'BranchInspection/offsite_item_form.html', {'form': form, 'title': 'Add New Item'})


@login_required
def edit_offsite_item(request, item_id):
    item = get_object_or_404(OffSiteItem, id=item_id)
    if not is_monitoring_user(request.user):
        return redirect('BranchInspection:submission_overview')

    if request.method == 'POST':
        form = OffSiteItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Item updated successfully.")
            return redirect('BranchInspection:manage_offsite_items')
    else:
        form = OffSiteItemForm(instance=item)

    return render(request, 'BranchInspection/offsite_item_form.html', {'form': form, 'title': 'Edit Item'})


@login_required
def delete_offsite_item(request, item_id):
    item = get_object_or_404(OffSiteItem, id=item_id)
    if is_monitoring_user(request.user):
        item.delete()
        messages.success(request, "Item deleted successfully.")
    return redirect('manage_offsite_items')
