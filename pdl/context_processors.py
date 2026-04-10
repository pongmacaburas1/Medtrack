"""
Context processor that injects `user_role` into every template context.
Templates can use:
    {% if user_role == 'admin' %}  ...  {% endif %}
    {% if user_role in 'admin,staff' %}  ...  {% endif %}  (not reliable)

Prefer:
    {% if user_role == 'admin' or user_role == 'staff' %}
"""


def user_role(request):
    if not request.user.is_authenticated:
        return {'user_role': None}

    if request.user.is_superuser:
        return {'user_role': 'admin'}

    try:
        return {'user_role': request.user.userprofile.role}
    except Exception:
        return {'user_role': 'staff'}