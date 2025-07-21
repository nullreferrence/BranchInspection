from django.contrib.auth import authenticate, login
from django.utils.timezone import now
from .forms import AuditSubmissionForm
from .models import AuditSubmission, Items, AuditObjection, AuditItemStatus
from .forms import AuditObjectionForm, LoginForm

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse


def start_audit(request):
    if request.method == "POST":
        form = AuditSubmissionForm(request.POST)
        if form.is_valid():
            audit = form.save(commit=False)
            audit.auditor = request.user  # Ensure user is logged in
            audit.save()
            return redirect('audit_workflow:audit_summary', audit_id=audit.id)  # Namespaced URL
    else:
        form = AuditSubmissionForm()

    return render(request, 'audit_workflow/start_audit.html', {'form': form})


@login_required
def audit_summary(request, audit_id):
    audit = get_object_or_404(AuditSubmission, id=audit_id, auditor=request.user)
    items = Items.objects.all()

    item_statuses = {status.item.id: status.is_completed for status in AuditItemStatus.objects.filter(audit=audit)}

    if request.method == "GET" and request.headers.get(
            'x-requested-with') == 'XMLHttpRequest' and 'item_id' in request.GET:  # AJAX request for form
        selected_item_id = request.GET.get('item_id')
        selected_item = get_object_or_404(Items, id=selected_item_id)
        form = AuditObjectionForm(initial={'items': selected_item})
        form_html = render_to_string("audit_workflow/submit_objection_form.html",
                                     {"form": form, "audit": audit, "item": selected_item},
                                     request=request)  # Pass audit and item to template
        return HttpResponse(form_html)  # Return only the form HTML

        # Initial page load
    selected_item = None
    form_html = ""
    if request.method == "GET" and 'item_id' in request.GET:
        selected_item_id = request.GET.get('item_id')
        selected_item = get_object_or_404(Items, id=selected_item_id)
        form = AuditObjectionForm(initial={'items': selected_item})
        form_html = render_to_string("audit_workflow/submit_objection_form.html",
                                     {"form": form, "audit": audit, "item": selected_item},
                                     request=request)  # Pass audit and item to template

    context = {
        "audit": audit,
        "items": items,
        "item_statuses": item_statuses,
        "selected_item": selected_item,
        "form_html": form_html,
    }
    return render(request, "audit_workflow/audit_summary.html", context)



# def audit_summary(request, audit_id, item_id=None):
#     audit = get_object_or_404(AuditSubmission, id=audit_id, auditor=request.user)
#     items = Items.objects.all()
#
#     # Fetch statuses
#     item_statuses = {status.item.id: status.is_completed for status in AuditItemStatus.objects.filter(audit=audit)}
#
#     selected_item = None
#     form_html = ""
#
#     if item_id:
#         selected_item = get_object_or_404(Items, id=item_id)
#         form = AuditObjectionForm(initial={'items': selected_item})
#         form_html = render_to_string("audit_workflow/submit_objection_form.html", {"form": form}, request=request)
#
#     context = {
#         "audit": audit,
#         "items": items,
#         "item_statuses": item_statuses,
#         "selected_item": selected_item,
#         "form_html": form_html
#     }
#     return render(request, "audit_workflow/audit_summary.html", context)





def submit_objection(request, audit_id, item_id):
    audit = get_object_or_404(AuditSubmission, id=audit_id)
    item = get_object_or_404(Items, id=item_id)

    if request.method == 'POST' and request.headers.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':  # Correct AJAX check
        form = AuditObjectionForm(request.POST)  # Initialize form with POST data
        if form.is_valid():
            objection = form.save(commit=False)
            objection.submission = audit
            objection.items = item
            objection.save()

            item_status = AuditItemStatus.objects.get(audit=audit, item=item)
            item_status.is_completed = True
            item_status.save()

            return JsonResponse({"message": "Objection submitted successfully!"})
        else:
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(error) for error in error_list]
            return JsonResponse({"errors": errors}, status=400)  # 400 status for errors

    elif request.method == 'GET' and request.headers.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':  # Correct AJAX check for GET
        form = AuditObjectionForm(initial={'items': item})
        form_html = render_to_string("audit_workflow/submit_objection_form.html", {"form": form, "audit": audit, "item": item}, request=request)
        return JsonResponse({"form": form_html})

    return HttpResponseBadRequest("Invalid request")  # 400 for non-AJAX POST or other requests


# def submit_objection(request, audit_id, item_id):
#     # Retrieve the specific audit and item from the database
#     audit = get_object_or_404(AuditSubmission, id=audit_id)
#     item = get_object_or_404(Items, id=item_id)
#
#     # Initialize the form
#     form = AuditObjectionForm()
#
#     if request.method == 'POST' and request.is_ajax():
#         form = AuditObjectionForm(request.POST)
#         if form.is_valid():
#             # Save the form data and associate it with the current audit and item
#             objection = form.save(commit=False)
#             objection.audit_submission = audit
#             objection.item = item
#             objection.save()
#
#             # Return the success response
#             return JsonResponse({"message": "Objection submitted successfully!"})
#         else:
#             # Return errors if the form is invalid
#             return JsonResponse({"message": "Failed to submit objection.", "errors": form.errors})
#
#     # If it's a GET request (initial loading of the form)
#     if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#         form_html = render_to_string("audit_workflow/submit_objection_form.html", {"form": form})
#         return JsonResponse({"form": form_html})
#
#     return render(request, "audit_workflow/submit_objection.html", {"form": form, "audit": audit, "item": item})



@login_required
def finalize_audit(request, audit_id):
    audit = get_object_or_404(AuditSubmission, id=audit_id, auditor=request.user)
    incomplete_items = AuditItemStatus.objects.filter(audit=audit, is_completed=False)

    if incomplete_items.exists():
        return render(request, "audit_workflow/finalize_error.html", {"audit": audit})

    audit.submitted = True
    audit.submission_date = now()
    audit.save()
    return redirect("audit_workflow:dashboard")

@login_required
def dashboard(request):
    """ Displays the dashboard after audit completion. """
    audits = AuditSubmission.objects.filter(user=request.user)
    return render(request, "audit_workflow/dashboard.html", {"audits": audits})



def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)  # Authenticate using email
            if user is not None:
                login(request, user)
                return redirect("audit_workflow:start_audit")  # Redirect to your home page after login
            else:
                form.add_error(None, "Invalid email or password")  # Add error message to the form
    else:
        form = LoginForm()
    return render(request, 'audit_workflow/login.html', {'form': form})

