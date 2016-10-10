django-graph-auth
=======================

django-graph-auth is a Django application which provides simple mutations and queries for managing users with GraphQL. It can register users, log in, reset users, and expose `JSON web tokens`_.

.. _Django Rest Framework: http://www.django-rest-framework.org/

.. _JSON web tokens: http://getblimp.github.io/django-rest-framework-jwt/

Requirements
------------

This has only been tested with:

* Python: 3.5
* Django: 1.10

Setup
-----

Install from **pip**:

.. code-block:: sh

    pip install django-graph-auth

and then add it to your installed apps:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'graph_auth',
        ...
    )

You will also need to add a middleware class to listen in on responses:

Credits
-------

``django-graph-auth`` was created by Morgante Pell (`@morgante
<https://github.com/morgante>`_). It is based on (`django-rest-auth<https://github.com/Tivix/django-rest-auth>`_).
