# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

import os
import sys

sys.path.insert(0, os.path.abspath('..'))


# -- Project information -----------------------------------------------------

project = 'Jade Tree'
copyright = '2020, Asymworks, LLC'
author = 'Jonathan Krauss'

# The full version, including alpha/beta/rc tags
release = '0.1.0'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx_rtd_theme',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# Mapping of external documentation sites
intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'arrow': ('https://arrow.readthedocs.io/en/latest/', None),
    'babel': ('http://babel.pocoo.org/en/latest/', None),
    'flask': ('https://flask.palletsprojects.com/en/1.1.x/', None),
    'flask-classful': ('http://flask-classful.teracy.org/', None),
    'flask-login': ('https://flask-login.readthedocs.io/en/latest/', None),
    'flask-mail': ('https://pythonhosted.org/flask-mail/', None),
    'flask-restplus': ('https://flask-restplus.readthedocs.io/en/stable/', None),
    'flask-sqlalchemy': ('https://flask-sqlalchemy.palletsprojects.com/en/2.x/', None),
    'itsdangerous': ('https://itsdangerous.palletsprojects.com/en/1.1.x/', None),
    'marshmallow': ('https://marshmallow.readthedocs.io/en/stable/', None),
    'sqlalchemy': ('https://docs.sqlalchemy.org/en/latest/', None),
    'werkzeug': ('https://werkzeug.palletsprojects.com/en/1.0.x/', None),
    'wtforms': ('https://wtforms.readthedocs.io/en/stable/', None),
}

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# These paths are either relative to html_static_path
# or fully qualified paths (eg. https://...)
html_css_files = [
    'css/wrap-tables.css',
]
