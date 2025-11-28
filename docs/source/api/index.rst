API Reference
=============

This section contains detailed API reference documentation.

Authentication
--------------

The API uses JWT (JSON Web Tokens) for authentication.

**Token Types:**

* **Access Token**: Short-lived (30 minutes) - used for API requests
* **Refresh Token**: Long-lived (7 days) - used to obtain new access tokens

**Roles:**

* **USER**: Default role for registered users
* **ADMIN**: Administrative role with elevated privileges


Endpoints Overview
------------------

Authentication Endpoints
~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 10 30 40 20

   * - Method
     - Endpoint
     - Description
     - Auth Required
   * - POST
     - /auth/register
     - Register new user
     - No
   * - POST
     - /auth/login
     - Login and get tokens
     - No
   * - POST
     - /auth/refresh
     - Refresh access token
     - No
   * - POST
     - /auth/logout
     - Logout (revoke tokens)
     - Yes
   * - GET
     - /auth/me
     - Get current user profile
     - Yes
   * - PATCH
     - /auth/avatar
     - Upload avatar (Admin only)
     - Yes (Admin)
   * - POST
     - /auth/reset-password-request
     - Request password reset
     - No
   * - POST
     - /auth/reset-password-confirm
     - Confirm password reset
     - No


Contact Endpoints
~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 10 30 40 20

   * - Method
     - Endpoint
     - Description
     - Auth Required
   * - GET
     - /contacts/
     - List all contacts
     - Yes
   * - POST
     - /contacts/
     - Create new contact
     - Yes
   * - GET
     - /contacts/{id}
     - Get contact by ID
     - Yes
   * - PUT
     - /contacts/{id}
     - Update contact
     - Yes
   * - DELETE
     - /contacts/{id}
     - Delete contact
     - Yes
   * - GET
     - /contacts/search/
     - Search contacts
     - Yes
   * - GET
     - /contacts/birthdays/
     - Upcoming birthdays
     - Yes


Error Responses
---------------

The API uses standard HTTP status codes:

* **200 OK**: Success
* **201 Created**: Resource created
* **400 Bad Request**: Invalid request
* **401 Unauthorized**: Authentication required
* **403 Forbidden**: Insufficient permissions
* **404 Not Found**: Resource not found
* **409 Conflict**: Resource conflict (e.g., duplicate email)
* **422 Unprocessable Entity**: Validation error
* **500 Internal Server Error**: Server error

