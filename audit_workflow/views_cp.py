from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from .forms import AuditSubmissionForm
from datetime import datetime
from django.shortcuts import get_object_or_404
from .models import AuditSubmission, Items, AuditObjection, AuditItemStatus
from .forms import AuditObjectionForm, LoginForm

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required





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
def submit_objection(request, audit_id, item_id):
    """ Handles objection submission for a specific item. """
    audit = get_object_or_404(AuditSubmission, id=audit_id, auditor=request.user)
    item = get_object_or_404(Items, id=item_id)  # Fixed line

    if request.method == "POST":
        form = AuditObjectionForm(request.POST)
        if form.is_valid():
            objection = form.save(commit=False)
            objection.submission = audit  # Link objection to the audit
            objection.items = item  # Link objection to the selected item
            objection.save()
            return redirect("audit_workflow:audit_summary", audit_id=audit.id)
    else:
        form = AuditObjectionForm()

    context = {
        "audit": audit,
        "item": item,
        "form": form,
    }
    return render(request, "audit_workflow/submit_objection.html", context)



@login_required
def audit_summary(request, audit_id):
    """ Displays audit items with submit objection functionality. """
    audit = get_object_or_404(AuditSubmission, id=audit_id, auditor=request.user)
    items = Items.objects.all()

    context = {
        "audit": audit,
        "items": items,
    }
    return render(request, "audit_workflow/audit_summary.html", context)


@login_required
def finalize_audit(request, audit_id):
    """ Finalizes the audit if all items are completed. """
    audit = get_object_or_404(AuditSubmission, id=audit_id, auditor=request.user)
    incomplete_items = audit.items.filter(is_completed=False)

    if incomplete_items.exists():
        return render(request, "audit_workflow/finalize_error.html", {"audit": audit})

    audit.is_finalized = True
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

