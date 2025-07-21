from django import template
from BranchInspection.utils import is_branch_user, is_crm_user, is_monitoring_user

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Fetch value from a dictionary by key in Django templates"""
    if isinstance(dictionary, dict):
        return dictionary.get(key, False)
    return None  # Or return '' or False as per your design

@register.filter
def dict_get(dict_obj, key):
    if isinstance(dict_obj, dict):
        return dict_obj.get(key, False)
    return None

@register.filter
def to(start, end):
    return range(start, end + 1)

@register.filter
def has_role(user, role_name):
    return getattr(user, 'role', '') == role_name

@register.filter
def trim(value):
    if isinstance(value, str):
        return value.strip()
    return value

@register.filter
def split(value, delimiter=','):
    return value.split(delimiter)

@register.filter
def get(dictionary, key):
    try:
        return dictionary.get(key, '')
    except Exception:
        return ''


@register.filter
def attr(obj, attr_name):
    return getattr(obj, attr_name, '')

@register.filter(name='add_class')
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})

@register.filter
def has_role(user, role_name):
    role_name = role_name.lower()
    if not user.is_authenticated:
        return False
    if role_name == "branch":
        return is_branch_user(user)
    elif role_name == "crm":
        return is_crm_user(user)
    elif role_name == "monitoring":
        return is_monitoring_user(user)
    return False