from django.shortcuts import redirect


def get_user_tenant(request):
    if request.user.role == 'SUPER_ADMIN':
        return None

    return request.user.tenant