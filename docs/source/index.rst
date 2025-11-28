Contacts API Documentation
==========================

Welcome to Contacts API documentation!

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules/index
   api/index


Overview
--------

Contacts API is a modern RESTful API built with FastAPI for managing contacts with user authentication, role-based access control, and advanced features.

Features
--------

* **JWT Authentication** - Secure user registration and login
* **Email Verification** - Token-based email verification
* **Password Reset** - Secure password reset with email confirmation
* **Role-Based Access Control** - USER and ADMIN roles
* **Redis Caching** - High-performance user data caching
* **Avatar Upload** - Cloudinary integration for profile pictures
* **Contact Management** - Full CRUD operations for contacts
* **Advanced Search** - Search by name, email, or phone
* **Birthday Tracking** - Find contacts with upcoming birthdays

Quick Start
-----------

Installation
~~~~~~~~~~~~

.. code-block:: bash

   docker-compose up -d --build

API Documentation
~~~~~~~~~~~~~~~~~

Interactive API documentation is available at:

* Swagger UI: http://localhost:8000/docs
* ReDoc: http://localhost:8000/redoc

Authentication
~~~~~~~~~~~~~~

1. Register a new user:

.. code-block:: bash

   curl -X POST http://localhost:8000/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com", "password": "password123"}'

2. Login to get access token:

.. code-block:: bash

   curl -X POST http://localhost:8000/auth/login \
     -d "username=user@example.com&password=password123"

3. Use the token in subsequent requests:

.. code-block:: bash

   curl -X GET http://localhost:8000/contacts/ \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

