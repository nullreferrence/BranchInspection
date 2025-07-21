from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Fetch value from a dictionary by key in Django templates"""
    return dictionary.get(key, False)

@register.filter
def dict_get(dict_obj, key):
    return dict_obj.get(key, False)