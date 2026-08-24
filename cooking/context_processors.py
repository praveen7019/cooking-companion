from .models import chef

def role_check(request):
    email = request.session.get('email')
    is_chef = False
    if email:
        # Silently verify the role for the navbar
        is_chef = chef.objects.filter(email=email).exists()
    return {'is_chef': is_chef}