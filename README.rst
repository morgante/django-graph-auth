django-graph-auth
=======================

django-graph-auth is a Django application which provides simple mutations and queries for managing users with GraphQL. It can register users, log in, reset users, and expose `JSON web tokens`_.

Documentation can be found on `GitHub`_.

.. _Django Rest Framework: http://www.django-rest-framework.org/

.. _JSON web tokens: http://getblimp.github.io/django-rest-framework-jwt/

.. _GitHub: https://github.com/morgante/django-graph-auth/blob/master/docs/api.md

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

You will also need to edit your base schema to import the mutations and queries, like this:

.. code-block:: python

	import graphene
	from graphene import relay, ObjectType

	import graph_auth.schema

	class Query(graph_auth.schema.Query, ObjectType):
	    node = relay.Node.Field()

	class Mutation(graph_auth.schema.Mutation, ObjectType):
	    pass

	schema = graphene.Schema(query=Query, mutation=Mutation)


Credits
-------

``django-graph-auth`` was created by Morgante Pell (`@morgante
<https://github.com/morgante>`_). It is based on `django-rest-auth`_.

.. _django-rest-auth: https://github.com/Tivix/django-rest-auth
