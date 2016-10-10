from graph_auth import __version__
from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

setup(
    name='django-graph-auth',
    version=__version__,
    description='django-graph-auth is a Django application which provides simple mutations and queries for managing users with GraphQL.',
    long_description=readme + '\n\n' + history,
    author='Morgante Pell',
    author_email='morgante.pell@morgante.net',
    url='https://github.com/morgante/django-graph-auth',
    packages=['graph_auth'],
    license='MIT License',
    keywords='django graphql api authentication jwt',
    platforms=['any'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    install_requires=[],
)
