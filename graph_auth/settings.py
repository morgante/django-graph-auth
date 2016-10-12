"""
Settings for Graph Auth framework are all namespaced in the GRAPH_AUTH setting.
For example your project's `settings.py` file might look like this:
REST_FRAMEWORK = {
    'USER_FIELDS': ('first_name', 'last_name', )
}
This module provides the `graph_auth_settings` object, that is used to access
graph auth settings, checking for user settings first, then falling
back to the defaults.

This implementation is taken from Graphene's Django library:
https://github.com/graphql-python/graphene-django/blob/master/graphene_django/settings.py
"""
from __future__ import unicode_literals

from django.conf import settings
from django.test.signals import setting_changed
from django.utils import six

try:
    import importlib  # Available in Python 3.1+
except ImportError:
    from django.utils import importlib  # Will be removed in Django 1.9

DEFAULTS = {
    'USER_FIELDS': ('email', 'first_name', 'last_name', )
}

# List of settings that may be in string import notation.
IMPORT_STRINGS = ()

def perform_import(val, setting_name):
    """
    If the given setting is a string import notation,
    then perform the necessary import or imports.
    """
    if val is None:
        return None
    elif isinstance(val, six.string_types):
        return import_from_string(val, setting_name)
    elif isinstance(val, (list, tuple)):
        return [import_from_string(item, setting_name) for item in val]
    return val


def import_from_string(val, setting_name):
    """
    Attempt to import a class from a string representation.
    """
    try:
        # Nod to tastypie's use of importlib.
        parts = val.split('.')
        module_path, class_name = '.'.join(parts[:-1]), parts[-1]
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        msg = "Could not import '%s' for Graph Auth setting '%s'. %s: %s." % (val, setting_name, e.__class__.__name__, e)
        raise ImportError(msg)


class GraphAuthSettings(object):
    """
    A settings object, that allows API settings to be accessed as properties.
    For example:
        from graph_auth.settings import graph_auth_settings
        print(graph_auth_settings.USER_FIELDS)
    Any setting with string import paths will be automatically resolved
    and return the class, rather than the string literal.
    """
    def __init__(self, user_settings=None, defaults=None, import_strings=None):
        if user_settings:
            self._user_settings = self.__check_user_settings(user_settings)
        self.defaults = defaults or DEFAULTS
        self.import_strings = import_strings or IMPORT_STRINGS

    @property
    def user_settings(self):
        if not hasattr(self, '_user_settings'):
            self._user_settings = getattr(settings, 'GRAPH_AUTH', {})
        return self._user_settings

    def __getattr__(self, attr):
        if attr not in self.defaults:
            raise AttributeError("Invalid Graph Auth setting: '%s'" % attr)

        try:
            # Check if present in user settings
            val = self.user_settings[attr]
        except KeyError:
            # Fall back to defaults
            val = self.defaults[attr]

        # Coerce import strings into classes
        if attr in self.import_strings:
            val = perform_import(val, attr)

        # Cache the result
        setattr(self, attr, val)
        return val

graph_auth_settings = GraphAuthSettings(None, DEFAULTS, IMPORT_STRINGS)

def reload_graph_auth_settings(*args, **kwargs):
    global graph_auth_settings
    setting, value = kwargs['setting'], kwargs['value']
    if setting == 'GRAPH_AUTH':
        graph_auth_settings = GraphAuthSettings(value, DEFAULTS, IMPORT_STRINGS)

setting_changed.connect(reload_graph_auth_settings)
