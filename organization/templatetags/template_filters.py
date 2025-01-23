from django import template

register = template.Library()

@register.filter
def dict_get(dictionary, key):
    """ Custom template filter to safely get a key from a dictionary. """
    if isinstance(dictionary, dict):
        return dictionary.get(key, {"id": None, "status": "pending"})  # Default to unknown status
    return None


@register.filter
def dict_get_p(dictionary, key):
    """ Custom template filter to safely get a key from a dictionary. """
    if isinstance(dictionary, dict):
        return dictionary.get(key, {"id": None, "status": "Not verified"})  # Default to unknown status
    return None
