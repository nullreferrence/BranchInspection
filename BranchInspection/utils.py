from audit_workflow.models import Branch
def is_branch_user(user):
    return (
        hasattr(user, 'branch') and
        user.branch and
        user.branch.type in ['branch', 'corporate']
    )

def is_crm_user(user):
    return hasattr(user, 'branch') and user.branch and user.branch.type == 'regional'

def is_monitoring_user(user):
    return user.email.lower() == 'dgmmonitoring@krishibank.org.bd'

def get_submission_branches(region=None, division=None):
    qs = Branch.objects.filter(type__in=['branch', 'corporate'])
    if region:
        qs = qs.filter(region=region)
    if division:
        qs = qs.filter(division=division)
    return qs

