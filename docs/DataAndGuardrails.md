# Data and Security Guardrails Context Document

## Overview

This document defines the data ownership and security guardrails for the project. Its purpose is to ensure that user data is protected, access is restricted appropriately, and the system prevents unauthorized cross-user actions. These guardrails apply across the frontend, backend, database, and deployment environment.

The document covers:

* Per-user data ownership
* Authorization checks
* Protected route behavior
* Prohibited cross-user access patterns

## 1. Per-User Data Ownership

All user-generated or user-related data must belong to a specific authenticated user. Each record tied to a user must include a `user_id` or equivalent ownership field.

Examples of user-owned data include:

* Job applications
* Saved jobs
* Notes
* Resume or cover letter content
* Dashboard analytics tied to account activity

Rules:

* A user can only create, view, update, or delete their own records.
* All application data must be linked to the authenticated user's ID.
* Ownership must be enforced in backend logic and reflected in the database schema.
* The frontend must never assume access without backend verification.

Example:

* User A can view User A's applications.
* User A cannot access User B's applications, even if they know the record ID.

## 2. Authorization Checks

Authorization determines what an authenticated user is allowed to access. The backend is responsible for enforcing all authorization checks.

Rules:

* Every protected backend request must verify the identity of the current user.
* The backend must check that the requested resource belongs to the authenticated user before returning data.
* Authorization must not rely only on frontend behavior.
* Requests for resources that do not belong to the user must be denied.

Example behavior:

* If a user requests `/applications/15`, the backend must verify that application `15` belongs to that user.
* If it does not belong to them, the API should return an error such as `403 Forbidden` or `404 Not Found`.

## 3. Protected Route Behavior

Protected routes are pages or API endpoints that require authentication before access is granted.

### Frontend Protected Routes

Examples:

* `/dashboard`
* `/applications`
* `/board`
* `/profile`

Rules:

* Unauthenticated users must be redirected away from protected pages.
* Protected views must only render when a valid user session exists.
* The frontend may hide restricted UI elements, but this is not a substitute for backend protection.

### Backend Protected Routes

Examples:

* `GET /applications`
* `POST /applications`
* `PUT /applications/{id}`
* `DELETE /applications/{id}`

Rules:

* Protected endpoints must require authentication.
* The backend must validate the user's token or session before processing the request.
* If authentication fails, the server must return `401 Unauthorized`.
* If authentication succeeds but the user does not own the resource, the server must deny access.

## 4. Prohibited Cross-User Access Patterns

The system must prevent any behavior that allows one user to access, modify, or infer another user's data.

Prohibited patterns include:

* Accessing another user's record by changing an ID in the URL
* Updating or deleting another user's applications
* Returning all records without filtering by `user_id`
* Trusting a user-submitted `user_id` from the frontend
* Exposing sensitive account data in shared responses, logs, or client-side code

Examples of prohibited behavior:

* A request like `/applications/22` should not return data unless application `22` belongs to the current user.
* The backend must not accept `user_id` from the frontend as proof of ownership.
* Queries such as `SELECT * FROM applications` without user filtering must not be used for user-specific endpoints.

## 5. Backend Enforcement Rules

The backend is the primary enforcement layer for data security.

Rules:

* Always derive the current user from the authenticated session, token, or request context.
* Always filter database queries by the authenticated user's ID for user-owned resources.
* Never trust frontend-provided ownership information.
* Use consistent error responses for unauthorized and forbidden access.
* Validate request data before processing.

Example secure pattern:

```python
application = db.query(Application).filter(
    Application.id == application_id,
    Application.user_id == current_user.id
).first()
```

## 6. Database Guardrails

The database must support secure ownership and data integrity.

Rules:

* User-owned tables must include a `user_id` foreign key.
* Relationships must be clearly defined between users and their records.
* Constraints should be used where appropriate to preserve integrity.
* Queries must be written to return only data for the current user when applicable.

Example:

* `applications.user_id` references `users.id`
* `saved_jobs.user_id` references `users.id`

## 7. Frontend Guardrails

Frontend safeguards improve user experience but do not replace backend security.

Rules:

* Hide protected pages from unauthenticated users.
* Do not display data until authentication state is confirmed.
* Do not rely on frontend route protection alone.
* Handle authorization errors gracefully by redirecting users or showing an appropriate message.

Example:

* If an API request returns `401`, redirect the user to the login page.
* If an API request returns `403`, show an access denied message.

## 8. Error Response Conventions

Security-related errors should follow consistent API response patterns.

Example unauthorized response:

```json
{
  "success": false,
  "error": "Unauthorized",
  "message": "Authentication is required to access this resource."
}
```

Example forbidden response:

```json
{
  "success": false,
  "error": "Forbidden",
  "message": "You do not have permission to access this resource."
}
```

Rules:

* Use `401 Unauthorized` when the user is not authenticated.
* Use `403 Forbidden` when the user is authenticated but not allowed to access the resource.
* Do not expose internal stack traces or system details in responses.

## 9. Team Responsibility

Security is a shared responsibility across the team.

* **Backend developers** enforce authentication and authorization.
* **Database developers** design ownership relationships and integrity constraints.
* **Frontend developers** protect routes and handle auth-related UI behavior.
* **Deployment and environment setup** must protect secrets such as API keys and database credentials.

## Conclusion

These guardrails ensure that each user's data remains private and protected. The system must enforce ownership at the backend and database level, protect routes that require authentication, and prevent all forms of cross-user access. Following these rules will help the project remain secure, predictable, and maintainable for both developers and users.

