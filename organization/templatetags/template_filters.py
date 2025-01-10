from django import template

register = template.Library()

@register.filter
def dict_get(dictionary, key):
    """Returns dictionary value for the given key"""
    return dictionary.get(key, "Pending")