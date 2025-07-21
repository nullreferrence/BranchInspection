
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.db import models

from django.core.validators import RegexValidator
from django.db.models import TextField
from django.utils import timezone
from django_ckeditor_5.fields import CKEditor5Field

from django.conf import settings


class UserManager(BaseUserManager):
    """
    Custom manager for the User model.
    """

    def create_user(self, email, password=None, role='regular', **extra_fields):
        """
        Creates and saves a regular user with the given email and password.
        """
        if not email:
            raise ValueError('The Email field is required')
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)  # Ensure default activation
        user = self.model(email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_staffuser(self, email, password=None):
        """
        Creates and saves a staff user (Manager) with the given email and password.
        """
        return self.create_user(email, password, role='manager')

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Creates and saves a superuser with the given email and password.
        """
        extra_fields.setdefault('is_superuser', True)  # ✅ Required for superuser
        extra_fields.setdefault('is_staff', True)  # ✅ Required for admin panel
        extra_fields.setdefault('is_active', True)  # ✅ Superuser should be active by default
        return self.create_user(email, password, role='admin', **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model that supports using email instead of username.
    """
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('regular', 'Regular User'),
        ('rao', 'RAO'),
        ('authorizer', 'Authorizer'),
    ]

    email = models.EmailField(max_length=255, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='regular')
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)  # ✅ ADD THIS FIELD
    is_staff = models.BooleanField(default=False)  # ✅ Django needs this for admin panel
    timestamp = models.DateTimeField(auto_now_add=True)
    branch = models.ForeignKey('Branch', on_delete=models.PROTECT, null=True, blank=True)
    branch_code = models.IntegerField(null=True, blank=True)
    region = models.CharField(max_length=250, null=True, blank=True)
    division = models.CharField(max_length=250, null=True, blank=True)
    groups = models.ManyToManyField(Group, blank=True, related_name="internal_audit_users")
    user_permissions = models.ManyToManyField(Permission, blank=True, related_name="internal_audit_users_permissions") # Add this line



    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def get_full_name(self):
        return self.email

    def get_short_name(self):
        return self.email

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True





status = (('নিষ্পন্ন', 'নিষ্পন্ন'), ('অনিষ্পন্ন', 'অনিষ্পন্ন'))
employeeStatus = (('yes', 'yes'),('no', 'no'))

class AuditTypeChoices(models.TextChoices):
    GENERAL = 'General', 'General'
    AD = 'AD', 'AD'
    ICT = 'ICT Audit', 'ICT Audit'

class Items(models.Model):
    itemNo = models.CharField(max_length=20, null=True, blank=True)
    itemName = models.CharField(max_length=200, null=True, blank=True)
    category = models.CharField(max_length=200, null=True, blank=True)
    audit_type = models.CharField(
        max_length=25,
        choices=AuditTypeChoices.choices,
        default=AuditTypeChoices.GENERAL,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.itemName



class Branch(models.Model):
    name = models.CharField(max_length=250, null=True)
    bn_name = models.CharField(max_length=250, null=True)
    branch_code = models.IntegerField(null=True)
    region = models.CharField(max_length=250, null=True)
    division = models.CharField(max_length=250, null=True)
    BRANCH_TYPE_CHOICES = [
        ('corporate', 'Corporate'),
        ('regional', 'Regional Office'),
        ('division', 'Divisional Office'),
        ('branch', 'Regular Branch'),
        ('ho', 'Head Office'),
    ]
    type = models.CharField(
        max_length=20,
        choices=BRANCH_TYPE_CHOICES,
        default='branch'
    )
    fixed_auditor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='fixed_auditor_branches'
    )
    fixed_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='fixed_manager_branches'
    )
    fixed_authorizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='fixed_authorizer_branches'
    )
    def __str__(self):
        return self.name

class AuditSubmission(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    auditor = models.ForeignKey(User, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    submitted = models.BooleanField(default=False)
    submission_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    submission_date = models.DateTimeField(null=True, blank=True)
    year_range = models.CharField(
        max_length=9,
        validators=[RegexValidator(r'^\d{4}-\d{4}$', 'Invalid year range format.')]
    )
    audit_type = models.CharField(
        max_length=25,
        choices=AuditTypeChoices.choices,
        default=AuditTypeChoices.GENERAL,
    )
    is_authorized = models.BooleanField(default=False)  # ✅ Whether authorized
    authorized_by = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='authorized_submissions'
    )

    def __str__(self):
        return f"Audit {self.submission_id} - {self.branch.name} ({self.audit_type})"


class AuditObjection(models.Model):
    CATEGORY_CHOICES = [
        ('Memo', 'Memo'),
        ('Part-2', 'Part-2'),
        ('Part-3', 'Part-3'),
    ]

    submission = models.ForeignKey(AuditSubmission, on_delete=models.CASCADE)
    items = models.ForeignKey(Items, on_delete=models.CASCADE, null=True, blank=True)
    description = TextField(null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.submission.branch.name} - {self.items.itemName} - {self.category}"



class AuditItemStatus(models.Model):
    audit = models.ForeignKey(AuditSubmission, on_delete=models.CASCADE, related_name='item_statuses')
    item = models.ForeignKey(Items, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('audit', 'item')  # Prevent duplicate entries for the same audit and item

    def __str__(self):
        return f"{self.audit} - {self.item} - {'Completed' if self.is_completed else 'Incomplete'}"



class Objection(models.Model):

    case_title = models.CharField(max_length=10, default=0)
    case_description = models.CharField(max_length=50, null=True, blank = True)
    case_filed_at = models.DateField(null=False, blank=False)
    case_status = models.CharField(max_length=100, choices=status, default="অনিষ্পন্ন")
    #status = models.CharField(max_length=20, choices=[('open', 'Open'), ('closed', 'Closed')], default='open')

    amount = models.BigIntegerField(default=0)
    current_assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_cases')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_cases')
    item_id = models.ForeignKey(Items, on_delete=models.CASCADE, related_name='cases', null=True, blank=True)  # Make nullable

    #item_id = models.CharField(max_length=15, default=0)
    Branch_id = models.ForeignKey(Branch, on_delete=models.CASCADE)

    def __str__(self):
        return self.case_title




class Comment(models.Model):
    comment_date = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True, null=True)
    commented_by = models.ForeignKey(User, on_delete=models.CASCADE)
    submission = models.ForeignKey(AuditSubmission, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name="replies")
    item = models.ForeignKey(Items, on_delete=models.CASCADE, related_name='comments')
    file = models.FileField(upload_to="comment_files/", null=True, blank=True)  # New file field

    def has_admin_manager_reply(self):
        """Check if an admin or manager has replied to this comment"""
        return self.replies.filter(commented_by__groups__name__in=['Admin', 'Manager']).exists()

    def can_user_reply(self, user):
        last_reply = self.replies.order_by('-created_at').first()
        if not last_reply:
            return user.is_staff or user.groups.filter(name__in=['admin', 'manager']).exists()
        if last_reply.user == user:
            return False
        if user.is_staff and last_reply.user.is_staff:
            return False
        if not user.is_staff and not last_reply.user.is_staff:
            return False
        return True


class Upload(models.Model):
    upload_link = models.ForeignKey('AuditObjection', on_delete=models.CASCADE, related_name='uploads')  # Link to AuditObjection
    file_description = models.CharField(verbose_name='ডকুমেন্টের বর্ণনাঃ', max_length = 50, null=True, blank=True)
    document = models.FileField(verbose_name='ডকুমেন্ট সংযুক্তকরণঃ', upload_to="audit_workflow/%Y/%m/%d")


    def __str__(self):
        return f"{self.upload_link} - {self.document.name}"



class Personel_Decision(models.Model):

    isEmployee_involve = models.BooleanField(default=False, null=True, blank=True)  # Allow blank values
    audit_id = models.ForeignKey(AuditSubmission, on_delete=models.CASCADE, null=True, blank=True)
    items = models.ForeignKey(Items, on_delete=models.CASCADE, null=True, blank=True)  # Track decisions per item

    def __str__(self):
        return f"{self.items.itemName} - {self.isEmployee_involve}"

class Person(models.Model):
    name = models.CharField(max_length=50)
    pf = models.CharField(max_length=50, null=True, blank=True)
    accused_time_post = models.CharField(max_length=50, null=True, blank=True)
    current_post = models.CharField(max_length=50, null=True, blank=True)
    accusing_time = models.DateField(null=True, blank=True)
    accusing_tenure = models.CharField(max_length=15, blank=True)
    accusing_time_branch = models.CharField(max_length=25, blank=False)
    current_branch = models.CharField(max_length=25, blank=False)

    audit_id = models.ForeignKey(AuditSubmission, on_delete=models.CASCADE, null=True, blank=True)
    items = models.ForeignKey(Items, on_delete=models.CASCADE, null=True, blank=True)
    audit_objection = models.ForeignKey(AuditObjection, on_delete=models.CASCADE, null=True, blank=True, related_name='convicted_persons')

    def __str__(self):
        return self.name


class ObjectionDecision(models.Model):
    audit_objection = models.OneToOneField(AuditObjection, on_delete=models.CASCADE, related_name='decision', null=True, blank=True)
    decided_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='decisions')
    decision = models.CharField(max_length=20, choices=[('run', 'Run'), ('close', 'Close')])
    reason = models.TextField(blank=True, null=True)
    decided_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.audit_objection.item.name} - {self.decision}"


class ObjectionAction(models.Model):
    case = models.ForeignKey(Objection, on_delete=models.CASCADE, related_name='actions')
    action_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='actions')
    action_type = models.CharField(max_length=20, choices=[('comment', 'Comment'), ('decision', 'Decision'), ('pass', 'Pass')])
    action_details = models.TextField()  # For comments, decisions, or case transfers
    timestamp = models.DateTimeField(auto_now_add=True)


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    audit = models.ForeignKey('AuditSubmission', on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.recipient} - {self.message[:50]}"
