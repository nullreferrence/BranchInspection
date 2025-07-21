# utils.py

def get_effective_user_role(user, submission):
    """
    Dynamically determines the user's effective role based on context of audit.
    """
    branch = submission.branch

    # If the user is auditing their own branch (manager or rao)
    if user.role in ['manager', 'rao'] and user.branch == branch:
        return 'regular'

    # If an admin is managing a submission started by rao
    if user.role == 'admin' and submission.auditor.role == 'rao':
        return 'manager'

    return user.role


def get_next_user_for_notification(current_user, submission):
    """
    Returns the next user in the comment/authorization workflow to notify.
    """
    current_role = get_effective_user_role(current_user, submission)

    if current_role == 'regular':
        # Notify effective manager
        return submission.effective_manager  # You must store this during audit creation
    elif current_role == 'manager':
        return submission.authorizer  # Authorizer for the submission
    elif current_role == 'authorizer':
        # Notify regular user the process is complete (optional)
        return submission.created_by
    return None

