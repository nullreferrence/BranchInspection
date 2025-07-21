from datetime import date

from django.conf import settings
from django.db import models

from audit_workflow.models import Branch
from django.utils import timezone


# Create your models here.
class OffSiteItem(models.Model):
    ITEM_TYPES = (
        ('branch_management', 'Branch Management'),
        ('cash_instrumental', 'Cash and Instrumental Transaction'),
        ('deposit', 'Deposit'),
        ('general_banking', 'General Banking'),
        ('accounting', 'Accounting'),
        ('loan_advances', 'Loan and Advances'),
        ('foreign_trade', 'Foreign Trade'),
        # Add more as needed
    )
    item_no = models.PositiveIntegerField()
    name = models.TextField()
    item_type = models.CharField(max_length=50, choices=ITEM_TYPES)

    def __str__(self):
        return f"{self.item_no} - {self.name}"

class BranchInspectionSubmission(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='inspection_submissions')
    submitted_at = models.DateTimeField(auto_now_add=True)
    authorized_by_manager = models.BooleanField(default=False)
    replied_by_headoffice = models.BooleanField(default=False)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    month = models.DateField(default=date.today)  # Add this line
    extended_until = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Submission for {self.branch} by {self.submitted_by}"

    def is_submission_allowed(self):
        today = timezone.now().date()
        tenth = self.month.replace(day=10)
        return today <= tenth or (self.extended_until and today <= self.extended_until)

class BranchInspectionComment(models.Model):
    submission = models.ForeignKey(BranchInspectionSubmission, on_delete=models.CASCADE, related_name='comments')
    item = models.ForeignKey(OffSiteItem, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    verified_by_manager = models.BooleanField(default=False)
    returned_by_manager = models.BooleanField(default=False)
    reply_by_monitoring = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('submission', 'item', 'user')  # One comment per user per item per submission

    def __str__(self):
        return f"Comment by {self.user} on {self.item.name}"