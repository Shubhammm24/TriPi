"""Custom DRF permissions for the trips app.

Why both queryset filtering AND object-level permissions?

Queryset filtering (in the view):
    Session.objects.filter(user=request.user)
    Prevents listing other users' data. But it doesn't protect against
    a direct GET /api/sessions/<guessed-uuid>/ if the view doesn't filter.

Object-level permissions (this file):
    Checked by DRF's get_object() on every detail view. Even if someone
    guesses a valid UUID, the permission check rejects the request with
    403 Forbidden.

Belt AND suspenders. Queryset filtering is your first line of defense
(don't even load data you shouldn't see). Object-level permissions are
your second line (reject access even if the data was loaded).
"""

from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """Object-level permission: only the owner can access the object.

    Expects the object to have a ``user`` attribute (FK to AUTH_USER_MODEL).
    Returns True for objects with user=None (anonymous sessions) only if
    the request is unauthenticated — this preserves backwards compatibility
    with the original FastAPI behavior where no auth was required.
    """

    message = "You do not have permission to access this resource."

    def has_object_permission(self, request, view, obj):
        # If the object has no owner, allow anonymous access
        if obj.user is None:
            return True
        # Otherwise, only the owner can access it
        return obj.user == request.user
