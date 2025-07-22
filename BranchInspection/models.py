from datetime import date
from django.conf import settings
from django.db import models
from django.utils import timezone
from audit_workflow.models import Branch
from django.utils.timezone import now


class OffSiteItem(models.Model):
    ITEM_TYPES = (
        ('branch_management', 'Branch Management'),
        ('cash_instrumental', 'Cash and Instrumental Transaction'),
        ('deposit', 'Deposit'),
        ('general_banking', 'General Banking'),
        ('accounting', 'Accounting'),
        ('loan_advances', 'Loan and Advances'),
        ('foreign_trade', 'Foreign Trade'),
    )
    item_no = models.CharField(max_length=20)
    name = models.TextField()
    item_type = models.CharField(max_length=50, choices=ITEM_TYPES)
    predefined_replies = models.TextField(blank=True, help_text="Separate replies by | or use JSON if needed")


    def __str__(self):
        return f"{self.item_no} - {self.name}"


class BranchInspectionSubmission(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='inspection_submissions'
    )
    month = models.DateField(default=date.today)
    created_at = models.DateTimeField(auto_now_add=True)
    finalized = models.BooleanField(default=False)

    # CRM (Regional Manager) actions
    extended_until = models.DateField(null=True, blank=True)
    is_forwarded = models.BooleanField(default=False)
    is_returned = models.BooleanField(default=False)
    return_comment = models.TextField(null=True, blank=True)
    forwarded_at = models.DateTimeField(null=True, blank=True)
    returned_at = models.DateTimeField(null=True, blank=True)

    # DGM Monitoring reply (single overall comment)
    monitoring_reply = models.TextField(null=True, blank=True)
    replied_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='monitoring_replies'
    )
    replied_at = models.DateTimeField(null=True, blank=True)
    is_reply_finalized = models.BooleanField(default=False)
    _items_cache = None

    def __str__(self):
        return f"Submission for {self.branch} - {self.month.strftime('%B %Y')}"

    def is_submission_allowed(self):
        today = timezone.now().date()
        deadline = self.month.replace(day=10)
        return today <= deadline or (self.extended_until and today <= self.extended_until)

    def get_status_display(self):
        if not self.finalized:
            return "Draft"
        if self.is_returned:
            return "Returned"
        if self.is_forwarded and not self.monitoring_reply:
            return "Forwarded"
        if self.monitoring_reply:
            return "Replied"
        return "Submitted"

    def get_items(self):
        if self._items_cache is None:
            from .models import OffSiteItem

            if self.branch.type == 'branch':
                self._items_cache = OffSiteItem.objects.exclude(item_type='foreign_trade')
            else:
                self._items_cache = OffSiteItem.objects.all()
        return self._items_cache


class BranchInspectionComment(models.Model):
    submission = models.ForeignKey(
        BranchInspectionSubmission,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    item = models.ForeignKey(OffSiteItem, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('submission', 'item', 'user')

    def __str__(self):
        return f"Comment by {self.user} on {self.item.name}"


class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    submission = models.ForeignKey(BranchInspectionSubmission, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"To {self.recipient} | {self.message}"


# Optional model if you want to track MonitoringReply separately
# You can use the `monitoring_reply` TextField in BranchInspectionSubmission if this is unnecessary

class MonitoringReply(models.Model):
    submission = models.ForeignKey(BranchInspectionSubmission, on_delete=models.CASCADE, related_name='monitoring_replies')
    item = models.ForeignKey(OffSiteItem, on_delete=models.CASCADE, related_name='monitoring_replies', null=True,
                             blank=True)
    reply = models.TextField()
    replied_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    replied_at = models.DateTimeField(default=now, blank=True)
    seen = models.BooleanField(default=False)


    class Meta:
        unique_together = ('submission', 'item')  # Ensures only one reply per item per submission

    def __str__(self):
        return f"Monitoring Reply for {self.item} in Submission {self.submission}"


class BranchExtension(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    month = models.DateField()
    extended_until = models.DateField()
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='granted_extensions'
    )
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('branch', 'month')

    def __str__(self):
        return f"{self.branch} - {self.month.strftime('%B %Y')} → {self.extended_until}"


class RegionReplyFinalization(models.Model):
    region = models.CharField(max_length=100)
    finalized_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    finalized_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Finalized replies for {self.region}"



