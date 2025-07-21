def is_branch_user(user):
    return hasattr(user, 'branch') and user.branch and user.branch.type == 'branch'

def is_crm_user(user):
    return hasattr(user, 'branch') and user.branch and user.branch.type == 'regional'

def is_monitoring_user(user):
    return user.email.lower() == 'dgmmonitoring@krishibank.org.bd'
