from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.utils.timezone import now

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
def audit_summary(request, audit_id):
    audit = get_object_or_404(AuditSubmission, id=audit_id, auditor=request.user)
    items = Items.objects.all()

    # Get or create AuditItemStatus objects for this audit
    item_statuses = {}
    for item in items:
        status, created = AuditItemStatus.objects.get_or_create(audit=audit, item=item)
        item_statuses[item.id] = status.is_completed

    selected_item = None
    if request.method == "GET" and 'item_id' in request.GET:
        selected_item_id = request.GET.get('item_id')
        selected_item = get_object_or_404(Items, id=selected_item_id)
        form = AuditObjectionForm(initial={'items': selected_item})
    else:
        form = AuditObjectionForm()

    context = {
        "audit": audit,
        "items": items,
        "item_statuses": item_statuses,  # Pass the dictionary to the template
        "selected_item": selected_item,
        "form": form,
    }
    return render(request, "audit_workflow/audit_summary.html", context)



@login_required
def submit_objection(request, audit_id, item_id):
    audit = get_object_or_404(AuditSubmission, pk=audit_id)
    # Assuming you have a way to identify the specific item
    item = get_object_or_404(Items, id=item_id)

    UploadFormSet = formset_factory(UploadForm, extra=1, can_delete=True)
    PersonFormSet = formset_factory(PersonForm, extra=1, can_delete=True)

    if request.method == 'POST':
        logger.info(f"AJAX POST request received for audit_id={audit_id}, item_id={item_id}")
        logger.info("Processing POST data...")
        logger.info(f"POST data: {request.POST}")
        logger.info(f"FILES data: {request.FILES}")

        objection_form = AuditObjectionForm(request.POST)
        decision_form = Personel_DecisionForm(request.POST, instance=Personel_DecisionForm().Meta.model()) # Initialize with an instance for potential saving
        upload_formset = UploadFormSet(request.POST, request.FILES, prefix='upload_set') # Temporarily removed
        person_formset = PersonFormSet(request.POST, prefix='form')

        if all([objection_form.is_valid(), decision_form.is_valid(), upload_formset.is_valid(), person_formset.is_valid()]): # Removed upload_formset.is_valid()
            logger.info("All forms are valid. Proceeding to save data.")
            objection = objection_form.save(commit=False)
            objection.submission = audit
            objection.items = item
            objection.save()
            print("AuditObjection saved:", objection)

            #Save Personel_Decision (or update if exists)
            decision, created = Personel_Decision.objects.update_or_create(
                audit_id=audit,
                items=item,
                defaults={"isEmployee_involve": decision_form.cleaned_data["isEmployee_involve"]},
            )
            print("Personel_Decision saved/updated:", decision, "Created:", created)

            # Save Persons
            if decision.isEmployee_involve:
                for person_form in person_formset:
                    if person_form.is_valid() and person_form.has_changed():
                        person = person_form.save(commit=False)
                        person.audit_id = audit
                        person.items = item
                        person.audit_objection = objection
                        person.save()
                        print("Person saved:", person)


            # Handle uploads (temporarily skipped)
            for upload_form in upload_formset:
                if upload_form.is_valid() and upload_form.cleaned_data:
                    upload = upload_form.save(commit=False)
                    upload.upload_link = objection
                    upload.save()

            return JsonResponse({'success': 'Objection submitted successfully!'})
        else:
            logger.warning("Form validation failed.")
            errors = {}
            if objection_form.errors:
                errors['objection_form'] = objection_form.errors.as_json()
                logger.warning(f"Objection Form Errors: {objection_form.errors.as_json()}")
            if decision_form.errors:
                errors['decision_form'] = decision_form.errors.as_json()
                logger.warning(f"Decision Form Errors: {decision_form.errors.as_json()}")
            if upload_formset.errors: # Temporarily removed
                errors['upload_formset'] = upload_formset.errors.as_json()
                logger.warning(f"Upload Formset Errors: {upload_formset.errors.as_json()}")
            if person_formset.errors:
                person_errors = {}
                for i, errors_in_form in enumerate(person_formset.errors):
                    if errors_in_form:
                        person_errors[f'form-{i}'] = errors_in_form.as_json()
                errors['person_formset'] = person_errors
                logger.warning(f"Person Formset Errors: {person_errors}")
            error_response = {"error": "Form validation failed", "errors": errors}
            logger.warning(f"Returning JSON error response: {error_response}")
            return JsonResponse(error_response, status=400)

    else:
        objection_form = AuditObjectionForm()
        decision_form = Personel_DecisionForm(instance=Personel_DecisionForm().Meta.model())
        upload_formset = UploadFormSet(queryset=Upload.objects.none(), prefix='upload_set')
        person_formset = PersonFormSet(queryset=Person.objects.none(), prefix='form')

    return render(request, 'audit_workflow/submit_objection_form.html', {
        'objection_form': objection_form,
        'upload_formset': upload_formset, # Temporarily removed
        'decision_form': decision_form,
        'person_formset': person_formset,
        'audit': audit,
        'item': item
    })



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

