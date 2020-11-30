Development
===========

Quick Start
```````````

.. important::
  Before starting with Jade Tree development, ensure that
  `npm <https://www.npmjs.com>`_,
  `yarn <https://yarnpkg.com>`_, and
  `pipenv <https://github.com/pypa/pipenv>`_ are installed on your development
  machine.

To get started developing with Jade Tree, after cloning the
`GitHub repository <https://github.com/asymworks/jadetree>`_, enter the project
folder and initialize the npm package and Python virtual environments:

.. code-block:: shell

  yarn
  pipenv install

The development server may be launched by executing

.. code-block:: shell

  npm run serve:dev

Domain Models
`````````````

.. automodule:: jadetree.domain.models
  :members:
  :special-members:

.. automodule:: jadetree.domain.mixins
  :members:

.. automodule:: jadetree.domain.types
  :members:

Database Layer
``````````````

.. automodule:: jadetree.database
  :members:
  :special-members:


Service Layer
`````````````

.. automodule:: jadetree.service

Constants and Enumerations
``````````````````````````

.. automodule:: jadetree.domain.data
  :members:


Application Globals and Initializers
````````````````````````````````````

Jade Tree Application Factory
-----------------------------

.. automodule:: jadetree.factory
  :members:

Exceptions
``````````

.. automodule:: jadetree.exc
  :members:
