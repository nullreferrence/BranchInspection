# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Comment, AuditSubmission, Notification, AuditObjection
from .utils import get_effective_user_role, get_next_user_for_notification


@receiver(post_save, sender=Comment)
def notify_on_comment(sender, instance, created, **kwargs):
    if not created:
        return

    submission = instance.submission

    # Invalidate authorization on any new comment
    if submission.is_authorized:
        submission.is_authorized = False
        submission.save(update_fields=['is_authorized'])

    user_role = get_effective_user_role(instance.commented_by, submission)

    # Determine the next user to notify
    next_user = get_next_user_for_notification(instance.commented_by, submission)

    if not next_user:
        return

    # Prepare the message based on who is commenting
    if user_role == 'regular':
        msg = f"🗣️ A new comment has been submitted for Audit #{submission.id}. Please review."
    elif user_role == 'manager':
        msg = f"📩 Manager has replied for Audit #{submission.id}. Please authorize."
    elif user_role == 'authorizer':
        msg = f"✅ Audit #{submission.id} has been authorized. You can now proceed."
    else:
        msg = f"📌 New comment activity on Audit #{submission.id}."

    # Create the notification
    Notification.objects.create(
        recipient=next_user,
        audit=submission,
        message=msg,
    )


@receiver(post_save, sender=AuditSubmission)
def notify_on_authorization_or_finalize(sender, instance, created, **kwargs):
    if not created and instance.is_authorized:
        # Notify regular user
        branch_user = instance.branch.user_set.first()
        if branch_user:
            Notification.objects.create(
                recipient=branch_user,
                audit=instance,
                message=f"✅ Your Audit #{instance.id} has been authorized. You can now download the Jaripotro."
            )
    elif not created and instance.submitted:
        # Notify auditor
        Notification.objects.create(
            recipient=instance.auditor,
            audit=instance,
            message=f"📨 Audit #{instance.id} has been finalized and submitted."
        )



@receiver(post_save, sender=AuditObjection)
def notify_on_objection_submit(sender, instance, created, **kwargs):
    if created:
        audited_branch = instance.submission.branch
        branch_users = audited_branch.user_set.all()  # 🔄 Assuming reverse FK relationship

        for user in branch_users:
            Notification.objects.create(
                recipient=user,
                audit=instance.submission,
                message=f"📝 A new objection was submitted for item \"{instance.items.itemName}\" in Audit #{instance.submission.id}."
            )
