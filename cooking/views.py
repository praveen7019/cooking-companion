import re
from django.shortcuts import render, redirect, get_object_or_404
from django.db import models
from django.db.models import Avg, Q
from django.contrib import messages
from django.contrib.auth import logout
from django.core.mail import EmailMultiAlternatives, send_mail
from django.http import JsonResponse, HttpResponse
from .models import user, admin, chef, Recipe, Booking, SavedRecipe, Recommendation, ChefFollow
from rest_framework import generics
from .models import Recipe
from .serializers import RecipeSerializer

class RecipeListAPIView(generics.ListCreateAPIView):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    
def homepage(request):
    # 1. Hero Recipes (Newest 3)
    hero_recipes = Recipe.objects.filter(status='Approve').order_by('-id')[:3]
    hero_ids = list(hero_recipes.values_list('id', flat=True))

    # 2. BEST RECIPES: Sort by highest views
    best_recipes = Recipe.objects.filter(status='Approve').exclude(id__in=hero_ids).order_by('-views')[:6]
    best_ids = list(best_recipes.values_list('id', flat=True))

    # 3. Small Recipes: Random non-repeating
    already_shown_ids = hero_ids + best_ids
    small_recipes = Recipe.objects.filter(status='Approve').exclude(id__in=already_shown_ids).order_by('?')[:9]

    return render(request, "index.html", {
        'hero_recipes': hero_recipes,
        'best_recipes': best_recipes,
        'small_recipes': small_recipes
    })

def user_login(request):
    return render(request,"login.html")


def user_register_code(request):
    if request.method=="POST":
        name = request.POST.get('name')
        email=request.POST.get('email')
        contact=request.POST.get('contact')
        password =request.POST.get('password')
        if user.objects.filter(email=email).exists() or chef.objects.filter(email=email).exists():
            messages.error(request,"An account with this email already exists. Please log in.")
            return redirect("user_login")
        else:
            con=user(name=name,
                     email=email,
                     contact=contact,
                     password=password
                     )
            con.save()
            messages.success(request,"Your details have been registered successfully! Now you can log in.")
            return redirect("user_login")
        
def user_login_validation(request):
    email=request.POST['email']
    password = request.POST['password']
    if request.method=="POST":
        try:
            user_login = user.objects.get(email=email)
            if user_login.password == password:
                request.session['email']=email
                messages.success(request,"Logged In successfully")
                return redirect("user_dashboard")
            else:
                messages.success(request,"Invalid Password Please Re-enter")
                return redirect("user_login")
        except user.DoesNotExist:
            messages.success(request,"Invalid Email Id Please Re-Enter")
    return render(request,"login.html")

def unified_login_validation(request):
    """Single login endpoint — checks user table first, then chef table."""
    if request.method != "POST":
        return redirect("user_login")

    email    = request.POST.get('email', '').strip()
    password = request.POST.get('password', '').strip()

    # 1. Check regular user
    user_obj = user.objects.filter(email=email).first()
    if user_obj:
        if user_obj.password == password:
            request.session['email'] = email
            request.session.pop('user_role', None)   # ensure no stale chef flag
            messages.success(request, "Logged in successfully!")
            return redirect("user_dashboard")
        else:
            messages.error(request, "Incorrect password. Please try again.")
            return redirect("user_login")

    # 2. Check chef
    chef_obj = chef.objects.filter(email=email).first()
    if chef_obj:
        if chef_obj.password == password:
            request.session['email'] = email
            request.session['user_role'] = 'chef'
            messages.success(request, "Logged in successfully as Chef!")
            return redirect("chef_dashboard")
        else:
            messages.error(request, "Incorrect password. Please try again.")
            return redirect("user_login")

    # 3. Not found in either table
    messages.error(request, "No account found with that email. Please register first.")
    return redirect("user_login")


def user_dashboard(request):
    if 'email' not in request.session:
        return redirect("homepage")
    
    email = request.session.get('email')
    current_user = user.objects.get(email=email)
    user_id = current_user.id
    recipe_count = Recipe.objects.filter(user_email=email).count()
    saved_recipes = SavedRecipe.objects.filter(user=current_user)
    saved_ids = list(saved_recipes.values_list('recipe_id', flat=True))
    total_recipe = Recipe.objects.filter(user_email=email).count()
    
    # Fetch all approved recipes
    recipes = Recipe.objects.filter(status='Approve')
# 1. Hero Recipes (Newest 3)
    hero_recipes = Recipe.objects.filter(status='Approve').order_by('-id')[:3]
    hero_ids = list(hero_recipes.values_list('id', flat=True))

    # 2. BEST RECIPES: Added .annotate() to calculate the average rating!
    best_recipes = Recipe.objects.filter(status='Approve') \
        .exclude(id__in=hero_ids) \
        .annotate(avg_rating=Avg('recommendation__rating')) \
        .order_by('-views')[:6]
    best_ids = list(best_recipes.values_list('id', flat=True))

    # 3. Small Recipes: Added .annotate() to calculate the average rating!
    already_shown_ids = hero_ids + best_ids
    small_recipes = Recipe.objects.filter(status='Approve') \
        .exclude(id__in=already_shown_ids) \
        .annotate(avg_rating=Avg('recommendation__rating')) \
        .order_by('?')[:9]
    return render(request, "user_dashboard.html", {
        'user': current_user,
        'recipe_count': recipe_count,
        'saved_recipes': saved_recipes,
        'saved_ids': saved_ids,
        'total_recipe': total_recipe,
        'recipes': recipes,  # This tells the HTML file the recipes exist!
        'hero_recipes': hero_recipes,   
        'best_recipes': best_recipes,   
        'small_recipes': small_recipes  
    })
  
def admin_login(request):
    return render(request,"admin_login.html")

def admin_login_validation(request):
    email = request.POST['email']
    password = request.POST['password']
    if request.method=="POST":
        try:
            admin_login=admin.objects.get(admin_email=email)
            if admin_login.admin_password==password:
                request.session['email']=email
                return redirect("admin_dashboard")
            else:
                messages.success(request,"Invalid Paasword Plz Re-enter")
                return redirect("admin_login")
        except admin.DoesNotExist:
            messages.success(request,"Invalid Email Id Please Re-Enter")
    return render(request,"admin_login.html")

    
def admin_dashboard(request):
    if 'email' not in request.session:
        return redirect("homepage")
    else:
        total_user = user.objects.all().count()
        recipe=Recipe.objects.all().count()
        total_chef=chef.objects.all().count()
        total_booking=Booking.objects.all().count()
        return render(request,"admin_dashboard.html",{'total_booking':total_booking,'total_user':total_user,'recipe':recipe,'total_chef':total_chef})

def logoutview(request):
    logout(request)
    request.session.flush()
    return redirect('homepage')

def view_all_user(request):
    userlist=user.objects.all()
    return render(request,"view_all_user.html",{'userlist':userlist})

def delete_user(request,id):
    users = user.objects.get(id=id)
    users.delete()
    return redirect('view_all_user')

def delete_chef(request,id):
    chefs = chef.objects.get(id=id)
    chefs.delete()
    return redirect('view_all_chef')

def chef_login(request):
    return render(request,"chef_login.html")

def chef_register_code(request):
    if request.method=="POST":
        name = request.POST.get('name')
        email=request.POST.get('email')
        
        contact=request.POST.get('contact')
        password =request.POST.get('password')
        if chef.objects.filter(email=email).exists() or user.objects.filter(email=email).exists():
            messages.error(request,"An account with this email already exists. Please log in.")
            return redirect("chef_login")
        else:
            con=chef(name=name,
                     email=email,
                     contact=contact,
                     password=password
                     )
            con.save()
            messages.success(request,"Your details have been registered successfully! Now you can log in.")
            return redirect("chef_login")
        
def user_profile(request):
    if 'email' not in request.session:
        return redirect("homepage")
    else:
        email = request.session.get('email')
        users = user.objects.get(email=email)
        u = user.objects.get(email=email)
        recipes = Recipe.objects.filter(user_email=email)
        saved = SavedRecipe.objects.filter(user=u)
        saved_ids = list(saved.values_list('recipe_id', flat=True))
        # Count both M2M (user→user) AND ChefFollow (user→chef or chef→user)
        followers_count = u.followers.count() + ChefFollow.objects.filter(followed_email=email).count()
        following_count = u.following.count() + ChefFollow.objects.filter(follower_email=email).count()
        bookings = Booking.objects.filter(user_email=email).order_by('-event_date')
        return render(request, "user_profile.html", {
            'users': users,
            'recipes': recipes,
            'chef_recipes': recipes,
            'saved': saved,
            'saved_ids': saved_ids,
            'followers_count': followers_count,
            'following_count': following_count,
            'bookings': bookings,
        })


def update_profile_code(request):
    if request.method == "POST":
        email = request.POST.get('email')

        u = user.objects.get(email=email)

        u.name = request.POST.get('name')
        u.contact = request.POST.get('contact')
        u.password = request.POST.get('password')

        if request.FILES.get('profile_image'):
            u.profile_image = request.FILES['profile_image']

        u.save()

        messages.success(request, "Profile details updated successfully!")

    return redirect('user_profile')


def upload_recipe(request):
    if 'email' not in request.session:
        return redirect("homepage")
    else:
        email = request.session.get('email')
        users=user.objects.get(email=email)
        return render(request,"uplaod_recipe.html",{'users':users})
    

def chef_login_validation(request):
    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']
        try:
            chef_login = chef.objects.get(email=email)
            if chef_login.password == password:
                request.session['email'] = email
                request.session['user_role'] = 'chef'
                return redirect("chef_dashboard")
            else:
                messages.error(request, "Invalid Password. Please re-enter.")
                return redirect("chef_login")
        except chef.DoesNotExist:
            messages.error(request, "Invalid Email ID. Please re-enter.")
            return redirect("chef_login")
    return redirect("chef_login")
def chef_dashboard(request):
    if 'email' not in request.session:
        return redirect("homepage")
    else:
        email = request.session.get('email')
        if not email:
            return redirect('login')

    # Chef's personal stats
    current_chef = chef.objects.get(email=email)
    chef_own_recipes = Recipe.objects.filter(user_email=email)
    total_recipes = chef_own_recipes.count()
    total_saved = SavedRecipe.objects.filter(recipe__in=chef_own_recipes).count()
    total_reviews = Recommendation.objects.filter(recipe__in=chef_own_recipes).count()
  # Fetch all approved recipes
    recipes = Recipe.objects.filter(status='Approve')
# 1. Hero Recipes (Newest 3)
    hero_recipes = Recipe.objects.filter(status='Approve').order_by('-id')[:3]
    hero_ids = list(hero_recipes.values_list('id', flat=True))

    # 2. BEST RECIPES: Added .annotate() to calculate the average rating!
    best_recipes = Recipe.objects.filter(status='Approve') \
        .exclude(id__in=hero_ids) \
        .annotate(avg_rating=Avg('recommendation__rating')) \
        .order_by('-views')[:6]
    best_ids = list(best_recipes.values_list('id', flat=True))

    # 3. Small Recipes: Added .annotate() to calculate the average rating!
    already_shown_ids = hero_ids + best_ids
    small_recipes = Recipe.objects.filter(status='Approve') \
        .exclude(id__in=already_shown_ids) \
        .annotate(avg_rating=Avg('recommendation__rating')) \
        .order_by('?')[:9]
    return render(request, 'chef_dashboard.html', {
        'chef': current_chef,
        'recipes': chef_own_recipes, # Keeps the chef's own recipes loading correctly for their personal table
        'total_recipes': total_recipes,
        'total_saved': total_saved,
        'total_reviews': total_reviews,
        'hero_recipes': hero_recipes,
        'best_recipes': best_recipes,
        'small_recipes': small_recipes
    })

def upload_recipe_code(request):
    if request.method == 'POST':
        recipe_name = request.POST.get('recipe_name')
        category = request.POST.get('category')
        cooking_time = request.POST.get('time')
        ingredients = '\n'.join(v for v in request.POST.getlist('ingredients') if v.strip())
        steps = '\n'.join(v for v in request.POST.getlist('instructions') if v.strip())
        user_name = request.POST.get('user_name')
        user_email = request.POST.get('user_email')
        description = request.POST.get('description', '')
        recipe_image = request.FILES.get('image')
        recipe_video = request.FILES.get('video')
        youtube_url = request.POST.get('youtube_url', '')

        recipe = Recipe(
            recipe_name=recipe_name,
            category=category,
            cooking_time=cooking_time,
            ingredients=ingredients,
            steps=steps,
            user_name=user_name,
            user_email=user_email,
            description=description,
            recipe_image=recipe_image,
            recipe_video=recipe_video,
            youtube_url=youtube_url,
        )
        recipe.save()
        messages.success(request, "Recipe Details Uploaded successfully")
        return redirect('user_dashboard')

    return render(request, 'upload_recipe.html')

def edit_recipe(request, recipe_id):
    """Render the edit form pre-populated with the existing recipe values."""
    if 'email' not in request.session:
        return redirect('homepage')
    recipe = get_object_or_404(Recipe, id=recipe_id)
    # Only the owner can edit
    if recipe.user_email != request.session.get('email'):
        return redirect('user_profile')
    recipe_ingredients = [line for line in recipe.ingredients.splitlines() if line.strip()]
    recipe_steps       = [line for line in recipe.steps.splitlines()       if line.strip()]
    return render(request, 'edit_recipe.html', {
        'recipe':             recipe,
        'recipe_ingredients': recipe_ingredients,
        'recipe_steps':       recipe_steps,
    })

def edit_recipe_code(request, recipe_id):
    """Handle the POST from the edit form and save changes."""
    if 'email' not in request.session:
        return redirect('homepage')
    recipe = get_object_or_404(Recipe, id=recipe_id)
    if recipe.user_email != request.session.get('email'):
        return redirect('user_profile')
    if request.method == 'POST':
        recipe.recipe_name  = request.POST.get('recipe_name', recipe.recipe_name)
        recipe.category     = request.POST.get('category',    recipe.category)
        recipe.cooking_time = request.POST.get('time',        recipe.cooking_time)
        recipe.description  = request.POST.get('description', recipe.description)
        recipe.ingredients  = '\n'.join(v for v in request.POST.getlist('ingredients') if v.strip())
        recipe.steps        = '\n'.join(v for v in request.POST.getlist('instructions') if v.strip())
        # Only replace image / video if a new file was actually uploaded
        if request.FILES.get('image'):
            recipe.recipe_image = request.FILES['image']
        if request.FILES.get('video'):
            recipe.recipe_video = request.FILES['video']
        youtube_url = request.POST.get('youtube_url', '').strip()
        recipe.youtube_url = youtube_url
        recipe.save()
        messages.success(request, "Recipe updated successfully!")
        return redirect('user_profile')
    return redirect('edit_recipe', recipe_id=recipe_id)

def chef_edit_recipe(request, recipe_id):
    """Render the chef edit form pre-populated with the existing recipe values."""
    if 'email' not in request.session:
        return redirect('homepage')
    recipe = get_object_or_404(Recipe, id=recipe_id)
    if recipe.user_email != request.session.get('email'):
        return redirect('chef_profile')
    recipe_ingredients = [line for line in recipe.ingredients.splitlines() if line.strip()]
    recipe_steps       = [line for line in recipe.steps.splitlines()       if line.strip()]
    return render(request, 'chef_edit_recipe.html', {
        'recipe':             recipe,
        'recipe_ingredients': recipe_ingredients,
        'recipe_steps':       recipe_steps,
    })

def chef_edit_recipe_code(request, recipe_id):
    """Handle the POST from the chef edit form and save changes."""
    if 'email' not in request.session:
        return redirect('homepage')
    recipe = get_object_or_404(Recipe, id=recipe_id)
    if recipe.user_email != request.session.get('email'):
        return redirect('chef_profile')
    if request.method == 'POST':
        recipe.recipe_name  = request.POST.get('recipe_name', recipe.recipe_name)
        recipe.category     = request.POST.get('category',    recipe.category)
        recipe.cooking_time = request.POST.get('time',        recipe.cooking_time)
        recipe.description  = request.POST.get('description', recipe.description)
        recipe.ingredients  = '\n'.join(v for v in request.POST.getlist('ingredients') if v.strip())
        recipe.steps        = '\n'.join(v for v in request.POST.getlist('instructions') if v.strip())
        if request.FILES.get('image'):
            recipe.recipe_image = request.FILES['image']
        if request.FILES.get('video'):
            recipe.recipe_video = request.FILES['video']
        youtube_url = request.POST.get('youtube_url', '').strip()
        recipe.youtube_url = youtube_url
        recipe.save()
        messages.success(request, "Recipe updated successfully!")
        return redirect('chef_profile')
    return redirect('chef_edit_recipe', recipe_id=recipe_id)

def chef_delete_recipe(request, id):
    recipe = Recipe.objects.get(id=id)
    recipe.delete()
    messages.success(request, "Recipe deleted successfully!")
    return redirect("chef_profile")

def chef_recipe_gallery(request):
    recipes = Recipe.objects.filter(status='Approve').annotate(avg_rating=Avg('recommendation__rating')).order_by('-id')

    saved_ids = []
    saved = []
    email = request.session.get('email')

    if email:
        try:
            # 1. Verify the chef exists
            current_chef = chef.objects.get(email=email)

            # 2. Load saved recipes from session instead of the user database! (This fixes the crash)
            chef_saved_ids = request.session.get('chef_saved_ids', [])
            saved_recipes_qs = Recipe.objects.filter(id__in=chef_saved_ids)

            # 3. Wrap in objects with a .recipe attribute so the template loop works unchanged
            class SavedItem:
                def __init__(self, r):
                    self.recipe = r

            saved = [SavedItem(r) for r in saved_recipes_qs]
            saved_ids = chef_saved_ids  

        except chef.DoesNotExist:
            pass

    return render(request, 'chef_recipe_gallery.html', {
        'recipes': recipes,
        'saved_ids': saved_ids,
        'saved': saved,
        'current_email': email or '',
        'is_chef': True  # <--- Keeps your smart navbar working!
    })
    
def recipe_list(request,id):
    recipes = Recipe.objects.get(id=id)
    return render(request, 'recipe_list.html', {'recipes': recipes})

    
def recipe_gallery(request):
    recipes = Recipe.objects.filter(status='Approve').annotate(avg_rating=Avg('recommendation__rating')).order_by('-id')

    saved_ids = []
    saved = []
    email = request.session.get('email')

    if email:
        try:
            u = user.objects.get(email=email)

            saved_qs = SavedRecipe.objects.filter(user=u).select_related('recipe')
            saved_ids = list(saved_qs.values_list('recipe_id', flat=True))
            saved = saved_qs

        except user.DoesNotExist:
            pass

    return render(request, 'recipe_gallery.html', {
        'recipes': recipes,
        'saved_ids': saved_ids,
        'saved': saved,
        'current_email': email or '',
    })

def recipe_detail(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    email = request.session.get('email')
    user_role = request.session.get('user_role')

    # Security: If a Chef tries to access the User view, send them to the Chef view
    if user_role == 'chef':
        return redirect('chef_recipe_detail', recipe_id=recipe_id)

    recipe.views += 1
    recipe.save()
    
    current_user = user.objects.filter(email=email).first()

    if request.method == 'POST':
        # Only regular Users can review (Fixes IntegrityError)
        if current_user:
            rating = int(request.POST.get('rating', 0))
            comment = request.POST.get('comment', '')
            if 1 <= rating <= 5:
                Recommendation.objects.update_or_create(
                    user=current_user,
                    recipe=recipe,
                    defaults={'rating': rating, 'comment': comment}
                )
        return redirect('recipe_detail', recipe_id=recipe_id)

    recommendations = Recommendation.objects.filter(recipe=recipe).order_by('-created_at')
    embed_url = get_youtube_embed_url(recipe.youtube_url)

    return render(request, "recipe_detail.html", {
        'recipe': recipe,
        'current_user': current_user,
        'recommendations': recommendations,
        'embed_url': embed_url
    })


def chef_recipe_detail(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    email = request.session.get('email')
    user_role = request.session.get('user_role')

    if user_role != 'chef':
        return redirect('recipe_detail', recipe_id=recipe_id)

    current_chef = None
    saved_ids = []
    
    if email:
        current_chef = chef.objects.filter(email=email).first()
        saved_ids = request.session.get('chef_saved_ids', [])

    # --- NEW POST LOGIC FOR CHEFS ---
    if request.method == 'POST' and current_chef:
        rating = int(request.POST.get('rating', 0))
        comment = request.POST.get('comment', '')
        
        if 1 <= rating <= 5:
            # We are now saving the review under the 'chef' field, not 'user'!
            Recommendation.objects.update_or_create(
                chef=current_chef, # <--- Uses the new field we added to models.py
                user=None,         # <--- User is explicitly None
                recipe=recipe,
                defaults={'rating': rating, 'comment': comment}
            )
        return redirect('chef_recipe_detail', recipe_id=recipe_id)

    recommendations = Recommendation.objects.filter(recipe=recipe).order_by('-created_at')
    avg_rating = recommendations.aggregate(Avg('rating'))['rating__avg']
    embed_url = get_youtube_embed_url(recipe.youtube_url)

    return render(request, 'chef_recipe_detail.html', { 
        'recipe': recipe,
        'recommendations': recommendations,
        'avg_rating': avg_rating,
        'current_user': current_chef,
        'saved_ids': saved_ids,
        'embed_url': embed_url,
        'is_chef': True 
    })

def my_recipe(request):
    if 'email' not in request.session:
        return redirect("homepage")
    else:
        email = request.session.get('email')
        recipes = Recipe.objects.filter(user_email=email)
        return render(request, 'my_recipe_list.html', {'recipes': recipes})
    
def delete_recipe(request,id):
    recipes=Recipe.objects.get(id=id)
    recipes.delete()
    messages.success(request,"Recipe Deleted successfully!")
    return redirect("user_profile")

def search_recipe(request):
    query = request.GET.get('recipe')
    time = request.GET.get('time')
    search_recipe = Recipe.objects.filter(status='Approve')
    
    if query:
        search_recipe = search_recipe.filter(Q(recipe_name__icontains=query))
    if time:
        search_recipe = search_recipe.filter(cooking_time__lte=time)
        
    email = request.session.get('email')
    is_chef_session = False
    if email:
        is_chef_session = chef.objects.filter(email=email).exists()
        
    return render(request, "search_recipe.html", {'search_recipe': search_recipe, 'is_chef': is_chef_session})

def view_recipe_admin(request):
    if 'email' not in request.session:
        return redirect("homepage")
    else:
        pending = Recipe.objects.filter(status='pending')
        approved = Recipe.objects.filter(status='Approve')
        rejected = Recipe.objects.filter(status='Disapprove')
        return render(request,"view_all_recipe.html",{'pending': pending,'approved': approved,'rejected': rejected})
    
def delete_recipe_admin(request,id):
    recipes=Recipe.objects.get(id=id)
    recipes.delete()
    messages.success(request,"Recipe Deleted successfully!")
    return redirect("view_recipe_admin")

def view_all_chef(request):
    cheflist=chef.objects.all()
    return render(request,"view_all_chef.html",{'cheflist':cheflist})

def save_recipe(request, recipe_id):
    email = request.session.get('email')
    if not email:
        return JsonResponse({'status': 'error', 'message': 'Not logged in'}, status=401)

    # Try user first
    u = user.objects.filter(email=email).first()
    if u:
        recipe = get_object_or_404(Recipe, id=recipe_id)
        obj, created = SavedRecipe.objects.get_or_create(user=u, recipe=recipe)
        if not created:
            obj.delete()
            return JsonResponse({'status': 'unsaved'})
        return JsonResponse({'status': 'saved'})

    # Chef account — use session-based saved list
    chef_obj = chef.objects.filter(email=email).first()
    if chef_obj:
        saved_ids = request.session.get('chef_saved_ids', [])
        rid = int(recipe_id)
        if rid in saved_ids:
            saved_ids.remove(rid)
            request.session['chef_saved_ids'] = saved_ids
            return JsonResponse({'status': 'unsaved'})
        else:
            saved_ids.append(rid)
            request.session['chef_saved_ids'] = saved_ids
            return JsonResponse({'status': 'saved'})

    return JsonResponse({'status': 'error', 'message': 'Not logged in'}, status=401)

def saved_recipes(request):
    email = request.session.get('email')
    if not email:
        return redirect('user_login')

    # Chef accounts use session-based saved list (no SavedRecipe DB rows)
    chef_obj = chef.objects.filter(email=email).first()
    if chef_obj:
        chef_saved_ids = request.session.get('chef_saved_ids', [])
        saved_qs = Recipe.objects.filter(id__in=chef_saved_ids)

        class SavedItem:
            def __init__(self, r):
                self.recipe = r

        saved = [SavedItem(r) for r in saved_qs]
        return render(request, 'saved_recipes.html', {'saved': saved, 'is_chef': True})

    # Regular user
    u = user.objects.filter(email=email).first()
    if not u:
        return redirect('user_login')
    saved = SavedRecipe.objects.filter(user=u).select_related('recipe')
    return render(request, 'saved_recipes.html', {'saved': saved, 'is_chef': False})

def add_recommendation(request, recipe_id):
    email = request.session.get('email')
    user_role = request.session.get('user_role')
    
    if not email:
        return redirect('login')
        
    recipe = get_object_or_404(Recipe, id=recipe_id)
    
    if request.method == "POST":
        rating = int(request.POST.get('rating', 0))
        comment = request.POST.get('comment', '')

        # 1. If it's a Chef submitting
        if user_role == 'chef':
            current_chef = chef.objects.filter(email=email).first()
            if current_chef:
                Recommendation.objects.update_or_create(
                    chef=current_chef,
                    recipe=recipe,
                    defaults={'rating': rating, 'comment': comment, 'user': None}
                )
        
        # 2. If it's a User submitting
        else:
            current_user = user.objects.filter(email=email).first()
            if current_user:
                Recommendation.objects.update_or_create(
                    user=current_user,
                    recipe=recipe,
                    defaults={'rating': rating, 'comment': comment, 'chef': None}
                )
                
    # 3. Redirect back to the correct dashboard
    if user_role == 'chef':
        return redirect('chef_recipe_detail', recipe_id=recipe.id)
    else:
        return redirect('recipe_detail', recipe_id=recipe.id)

def my_recipe_reviews(request):
    email = request.session.get('email')
    if not email:
        return redirect('login')
    current_user = user.objects.get(email=email)
    recipes = Recipe.objects.filter(user_email=current_user.email)
    recipe_reviews = []
    for r in recipes:
        reviews = Recommendation.objects.filter(recipe=r)
        recipe_reviews.append({'recipe': r, 'reviews': reviews})
    return render(request, 'my_recipe_reviews.html', {'recipe_reviews': recipe_reviews})

def chef_upload_recipe(request):
    if 'email' not in request.session:
        return redirect("homepage")
    else:
        email = request.session.get('email')
        chef_profile=chef.objects.get(email=email)
        return render(request,"chef_upload_recipe.html",{'chef_profile':chef_profile})
    
def upload_recipe_code_chef(request):
    if request.method == 'POST':
        recipe_name = request.POST.get('recipe_name')
        category = request.POST.get('category')
        cooking_time = request.POST.get('time')
        ingredients = request.POST.get('ingredients') or ''
        steps = request.POST.get('instructions') or ''
        user_name = request.POST.get('user_name')
        user_email = request.POST.get('user_email')
        description = request.POST.get('description', '')
        recipe_image = request.FILES.get('image')
        recipe_video = request.FILES.get('video')
        youtube_url = request.POST.get('youtube_url', '')   # ← NEW

        recipe = Recipe(
            recipe_name=recipe_name,
            category=category,
            cooking_time=cooking_time,
            ingredients=ingredients,
            steps=steps,
            user_name=user_name,
            user_email=user_email,
            description=description,
            recipe_image=recipe_image,
            recipe_video=recipe_video,
            youtube_url=youtube_url,                        # ← NEW
        )
        recipe.save()
        messages.success(request, "Recipe uploaded successfully!")
        return redirect('chef_profile')

    return render(request, 'chef_upload_recipe.html')

def chef_profile(request):
    if 'email' not in request.session:
        return redirect("homepage")

    email = request.session.get('email')
    chef_profile = chef.objects.get(email=email)
    recipes = Recipe.objects.filter(user_email=email)
    bookings = Booking.objects.filter(chef_email=email)

    # Load saved recipes from session for chef accounts
    chef_saved_ids = request.session.get('chef_saved_ids', [])
    saved_recipes_qs = Recipe.objects.filter(id__in=chef_saved_ids)

    # Wrap in objects with a .recipe attribute so the template loop works unchanged
    class SavedItem:
        def __init__(self, r):
            self.recipe = r

    saved = [SavedItem(r) for r in saved_recipes_qs]
    saved_ids = chef_saved_ids  # for heart-colour checks in the template

    return render(request, "chef_profile.html", {
        'chef': chef_profile,
        'recipes': recipes,
        'bookings': bookings,
        'followers_count': ChefFollow.objects.filter(followed_email=email).count(),
        'following_count': ChefFollow.objects.filter(follower_email=email).count(),
        'saved': saved,
        'saved_ids': saved_ids,
    })
    
    
def chef_profile_edit(request):
    email = request.session.get('email')
    if not email:
        return redirect('chef_login')

    chef_obj = chef.objects.get(email=email)

    if request.method == 'POST':
        chef_obj.name = request.POST.get('name', chef_obj.name)
        chef_obj.contact = request.POST.get('contact', chef_obj.contact)
        chef_obj.experince = request.POST.get('experince', chef_obj.experince)
        if 'chef_image' in request.FILES:
            chef_obj.chef_image = request.FILES['chef_image']
        chef_obj.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('chef_profile')

    return render(request, "chef_profile_edit.html", {'chef': chef_obj})

def chef_list(request):
    if 'email' not in request.session:
        return redirect("homepage")
    else:
        chefs = chef.objects.all()
        return render(request, 'chef_list.html', {'chefs': chefs})

def book_chef(request, chef_id):
    email = request.session.get('email')
    chef_obj = chef.objects.get(id=chef_id)
    users=user.objects.get(email=email)
    return render(request, 'book_chef.html', {'chef': chef_obj,'users':users})

def book_chef_code(request):
    if request.method == "POST":
        chef_email = request.POST.get('chef_email')
        user_email = request.POST.get('user_email')
        event_date = request.POST.get('event_date')
        user_name = request.POST.get('user_name')
        chef_name = request.POST.get('chef_name')
        if Booking.objects.filter(chef_email=chef_email, event_date=event_date).exists():
            messages.error(request, "This chef is already booked for this date.")
            return redirect(request.META.get('HTTP_REFERER'))
        Booking.objects.create(
            chef_email=chef_email,
            user_email=user_email,
            event_date=event_date,
            user_name=user_name,
            chef_name=chef_name,
            event_location=request.POST.get('event_location'),
            number_of_people=request.POST.get('number_of_people'),
            special_instructions=request.POST.get('special_instructions'),
        )
        messages.success(request, "Booking request sent successfully!")
        return redirect('chef_list')
    return render(request, 'book_chef.html')

def user_booking(request):
    if 'email' not in request.session:
        return redirect("homepage")
    email = request.session.get('email')
    bookings = Booking.objects.filter(user_email=email).order_by('-event_date')
    return render(request, "user_booking.html", {'bookings': bookings})

def email(request):
    return render(request,"email.html")

def send_email(request):
    if request.method=='POST':
        full_name = request.POST.get('full_name')
        recipient_email=request.POST.get('email')
        subject=request.POST.get('subject')
        message = request.POST.get('message')
        from_email='Cooking Companion <computronicsprojects1999@gmail.com>'
        to_email=[recipient_email]
        text_content=f"Dear { full_name }, \n\n { message } \n\n Best Regards,\n Cooking Companion"
        html_content=f"""
        <p> Dear <strong> { full_name } </strong> </p>
        <p> { message } </p>
        <br>
        <p> Best Regards ,<br> <strong> Cooking Companion </strong> </p>
        """
        email = EmailMultiAlternatives(subject,text_content,from_email,to_email)
        email.attach_alternative(html_content,"text/html")
        try:
            email.send()
            messages.success(request,"Email sent successfully ")
            return redirect('/email/')
        except Exception as e:
            return HttpResponse(f'Failed to send email : {e}')
    return render(request,"email.html")

def chef_booking(request):
    if 'email' not in request.session:
        return redirect("homepage")
    email = request.session.get('email')
    bookings = Booking.objects.filter(chef_email=email).order_by('-event_date')
    return render(request, "chef_booking.html", {'bookings': bookings})

def approvrent(request,id):
    rent_approve = Booking.objects.get(id=id)
    rent_approve.status ='approve'
    rent_approve.save()
    subject="Booking Status"
    message = f'congratutions "{rent_approve.user_name }", Your  Chef Booking application for  has been approved !'
    from_email = 'Cooking Companion <computronicsprojects1999@gmail.com>'
    to_email =  rent_approve.user_email
    send_mail(subject,message,from_email,[to_email])
    messages.success(request,"Booking request has been approved and email has been sent !")
    return redirect ('/chef_profile/')

def disapprovrent(request,id):
    rent_approve = Booking.objects.get(id=id)
    rent_approve.status = 'disapprove'
    rent_approve.save()
    subject = "Booking Status"
    message = f'Sorry "{rent_approve.user_name}", Your Chef Booking application has been Disapproved!'
    from_email = 'Cooking Companion <computronicsprojects1999@gmail.com>'
    to_email = rent_approve.user_email
    send_mail(subject, message, from_email, [to_email])
    messages.success(request, "Booking request has been Disapproved and email has been sent!")
    return redirect('/chef_profile/')

def view_all_booking(request):
    if 'email' not in request.session:
        return redirect("homepage")
    else:
        book = Booking.objects.all().order_by('-event_date')
        return render(request,"view_all_booking.html",{'book':book})
    
def remove_saved_recipe(request,id):
    con=SavedRecipe.objects.get(id=id)
    con.delete()
    messages.success(request,"Recipe Details Removed sucessfully ! ")
    return redirect("user_profile")

def clean_ingredient(text):
    text = text.lower()
    text = re.sub(r'\d+\s*(g|kg|ml|tsp|tbsp|cup|cups)?', '', text)
    text = re.sub(r'[^a-z\s]', '', text)
    return text.strip()

def search_recipe_ingridents(request):
    query = request.GET.get('ingredients', '')
    results = []

    email = request.session.get('email')
    is_chef_session = False
    if email:
        is_chef_session = chef.objects.filter(email=email).exists()

    if query:
        user_terms = [clean_ingredient(i) for i in query.split(',') if i.strip()]
        recipes = Recipe.objects.filter(status='Approve')

        for recipe in recipes:
            # ✅ NEW: Check if any search term matches the recipe name
            recipe_name_lower = recipe.recipe_name.lower()
            name_matched = any(term in recipe_name_lower for term in user_terms)

            # Existing: Check ingredient matches
            recipe_ingredients = [
                clean_ingredient(item)
                for item in recipe.ingredients.split('\n')
                if item.strip()
            ]
            matched = []
            missing = []
            for r_ing in recipe_ingredients:
                if any(term in r_ing for term in user_terms):
                    matched.append(r_ing)
                else:
                    missing.append(r_ing)

            # ✅ Include recipe if name matched OR ingredients matched
            if name_matched or matched:
                if recipe_ingredients:
                    match_percent = round((len(matched) / len(recipe_ingredients)) * 100, 2)
                else:
                    match_percent = 100 if name_matched else 0

                results.append({
                    'recipe': recipe,
                    'match_count': len(matched),
                    'match_percent': match_percent,
                    'matched': matched,
                    'missing': missing,
                    'name_match': name_matched,  # ✅ NEW flag for template use
                })

        # ✅ Sort: name matches first, then by ingredient match count
        results.sort(key=lambda x: (x['name_match'], x['match_count']), reverse=True)

    email = request.session.get('email')
    is_chef_session = False
    if email:
        # If the email exists in the Chef table, they are a Chef
        is_chef_session = chef.objects.filter(email=email).exists()

    if query:
        
        pass
        
    return render(request, 'search_results.html', {
        'results': results, 
        'query': query,
        'is_chef': is_chef_session  # <--- This tells the HTML to use the Chef links!
    })

def approvrecipe(request,id):
    recipe_approve = Recipe.objects.get(id=id)
    recipe_approve.status ='Approve'
    recipe_approve.save()
    subject="Recipe Status"
    message = f'congratutions "{recipe_approve.user_name }", Your  Recipe "{recipe_approve.recipe_name}  has been approved !'
    from_email = 'Cooking Companion <computronicsprojects1999@gmail.com>'
    to_email = recipe_approve.user_email
    send_mail(subject,message,from_email,[to_email])
    messages.success(request,"Recipe has been approved and email has been sent !")
    return redirect ('/view_recipe_admin/')

def disapprovrecipe(request,id):
    recipe_approve = Recipe.objects.get(id=id)
    recipe_approve.status ='Disapprove'
    recipe_approve.save()
    subject="Recipe Status"
    message = f'Sorry "{recipe_approve.user_name }", Your  Recipe "{recipe_approve.recipe_name}  has been Disapproved !'
    from_email = 'Cooking Companion <computronicsprojects1999@gmail.com>'
    to_email = recipe_approve.user_email
    send_mail(subject,message,from_email,[to_email])
    messages.success(request,"Recipe has been Disapproved and email has been sent !")
    return redirect ('/view_recipe_admin/')

def forgot_password_user(request):
    return render(request,"forgot_password_user.html")

def forgot_password_user_code(request):
    if request.method=="POST":
        email = request.POST.get("email")
        try:
            matched_user = user.objects.get(email=email)
        except user.DoesNotExist:
            messages.success(request,"This email does not exits")
            return redirect("forgot_password_user")
        send_mail(
            "Your Password",
            f"Hi { matched_user.name }, Your Password is { matched_user.password}",
            'Do not reply',
            [email],
        )
        messages.success(request,"Original Password sent to your account")
        return redirect("user_login")
    return HttpResponse("Invalid Request method")

def forgot_password_chef(request):
    return render(request,"forgot_password_chef.html")

def forgot_password_chef_code(request):
    if request.method=="POST":
        email = request.POST.get("email")
        try:
            matched_user = chef.objects.get(email=email)
        except user.DoesNotExist:
            messages.success(request,"This email does not exits")
            return redirect("forgot_password_chef")
        send_mail(
            "Your Password",
            f"Hi { matched_user.name }, Your Password is { matched_user.password}",
            'Do not reply',
            [email],
        )
        messages.success(request,"Original Password sent to your account")
        return redirect("chef_login")
    return HttpResponse("Invalid Request method")

def follow_user(request):
    if request.method == "POST":
        user_id = request.POST.get('user_id')
        current_user = request.user
        user_to_follow = user.objects.get(id=user_id)
        follow, created = Follow.objects.get_or_create(
            follower=current_user,
            following=user_to_follow
        )
        if not created:
            follow.delete()
    return redirect(request.META.get('HTTP_REFERER'))

def follow_page(request, recipe_id):
    if 'email' not in request.session:
        return redirect("homepage")

    recipe = get_object_or_404(Recipe, id=recipe_id)
    session_email = request.session['email']

    # ── Determine who uploaded this recipe (user or chef) ──────────────────
    uploader_user = user.objects.filter(email=recipe.user_email).first()
    uploader_chef = chef.objects.filter(email=recipe.user_email).first()

    if not uploader_user and not uploader_chef:
        return redirect('recipe_gallery')

    # ── Build a generic profile dict the template can consume ───────────────
    if uploader_user:
        profile_name    = uploader_user.name
        profile_email   = uploader_user.email
        profile_contact = uploader_user.contact
        profile_image   = uploader_user.profile_image.url if uploader_user.profile_image else None
        followers_count = uploader_user.followers.count()
        following_count = uploader_user.following.count()
        # For user→user follow, check the M2M table
        logged_in_user = user.objects.filter(email=session_email).first()
        if logged_in_user:
            is_following = logged_in_user in uploader_user.followers.all()
        else:
            # logged-in as chef → check ChefFollow table
            is_following = ChefFollow.objects.filter(
                follower_email=session_email, followed_email=profile_email).exists()
    else:
        profile_name    = uploader_chef.name
        profile_email   = uploader_chef.email
        profile_contact = uploader_chef.contact
        profile_image   = uploader_chef.chef_image.url if uploader_chef.chef_image else None
        followers_count = ChefFollow.objects.filter(followed_email=profile_email).count()
        following_count = ChefFollow.objects.filter(follower_email=profile_email).count()
        is_following    = ChefFollow.objects.filter(
            follower_email=session_email, followed_email=profile_email).exists()

    chef_recipes = Recipe.objects.filter(user_email=profile_email, status='Approve')

    # Can follow if not viewing own profile
    can_follow = (session_email != profile_email)
    is_chef_session = chef.objects.filter(email=session_email).exists()

    return render(request, "follow_profile.html", {
        'profile_name':    profile_name,
        'profile_email':   profile_email,
        'profile_contact': profile_contact,
        'profile_image':   profile_image,
        'chef_recipes':    chef_recipes,
        'is_following':    is_following,
        'followers_count': followers_count,
        'following_count': following_count,
        'recipe_id':       recipe_id,
        'can_follow':      can_follow,
        'chef': uploader_user or uploader_chef,
        'is_chef':         is_chef_session,
    })


def toggle_follow_chef(request, chef_id):
    if 'email' not in request.session:
        return redirect("homepage")

    target_user = get_object_or_404(user, id=chef_id)
    session_email = request.session['email']

    logged_in_user = user.objects.filter(email=session_email).first()
    if logged_in_user:
        # user → user follow via M2M
        if logged_in_user in target_user.followers.all():
            target_user.followers.remove(logged_in_user)
        else:
            target_user.followers.add(logged_in_user)
    else:
        # chef → user follow via ChefFollow
        obj, created = ChefFollow.objects.get_or_create(
            follower_email=session_email, followed_email=target_user.email)
        if not created:
            obj.delete()

    return redirect(request.META.get('HTTP_REFERER', 'user_dashboard'))


def toggle_follow_by_email(request, target_email):
    """Universal follow toggle — works for both user and chef sessions,
    targeting both users and chefs."""
    if 'email' not in request.session:
        return redirect("homepage")

    session_email = request.session['email']
    if session_email == target_email:
        return redirect(request.META.get('HTTP_REFERER', 'homepage'))

    logged_in_user = user.objects.filter(email=session_email).first()
    target_user    = user.objects.filter(email=target_email).first()

    if logged_in_user and target_user:
        # user → user: use M2M
        if logged_in_user in target_user.followers.all():
            target_user.followers.remove(logged_in_user)
        else:
            target_user.followers.add(logged_in_user)
    else:
        # any other combo (chef→user, user→chef, chef→chef): use ChefFollow
        obj, created = ChefFollow.objects.get_or_create(
            follower_email=session_email, followed_email=target_email)
        if not created:
            obj.delete()

    return redirect(request.META.get('HTTP_REFERER', 'homepage'))

def following_page(request):
    if 'email' not in request.session:
        return redirect("homepage")

    session_email = request.session['email']
    data = []
    seen_emails = set()
    is_chef_session = False

    logged_in_user = user.objects.filter(email=session_email).first()
    if logged_in_user:
        # user→user follows (M2M)
        for followed in logged_in_user.following.all():
            if followed.email in seen_emails:
                continue
            seen_emails.add(followed.email)
            recipes = Recipe.objects.filter(user_email=followed.email, status='Approve')
            profile_image = followed.profile_image.url if followed.profile_image else None
            data.append({
                'chef': followed,
                'recipes': recipes,
                'is_following': True,
                'profile_image': profile_image,
            })
    else:
        is_chef_session = chef.objects.filter(email=session_email).exists()

    # ChefFollow-based follows (covers chef sessions + user→chef follows)
    chef_follows = ChefFollow.objects.filter(follower_email=session_email)
    for cf in chef_follows:
        followed_email = cf.followed_email
        if followed_email in seen_emails:
            continue
        seen_emails.add(followed_email)

        followed_user  = user.objects.filter(email=followed_email).first()
        followed_chef  = chef.objects.filter(email=followed_email).first()
        profile = followed_user or followed_chef
        if not profile:
            continue

        recipes = Recipe.objects.filter(user_email=followed_email, status='Approve')
        profile_image = None
        if followed_user and followed_user.profile_image:
            profile_image = followed_user.profile_image.url
        elif followed_chef and followed_chef.chef_image:
            profile_image = followed_chef.chef_image.url

        data.append({
            'chef': profile,
            'recipes': recipes,
            'is_following': True,
            'profile_image': profile_image,
        })

    return render(request, "following_page.html", {'data': data, 'is_chef': is_chef_session})


def search_recipe_duration(request):
    query = request.GET.get('time')
    search_recipe = Recipe.objects.filter(status='Approve')
    if query:
        try:
            query = int(query)
            search_recipe = search_recipe.filter(cooking_time__lte=query)
        except ValueError:
            pass
    email = request.session.get('email')
    is_chef_session = bool(email and not user.objects.filter(email=email).exists() and chef.objects.filter(email=email).exists())
    return render(request, "search_recipe.html", {'search_recipe': search_recipe, 'is_chef': is_chef_session})

def subscription(request):
    return render(request,"subscription.html")


def get_youtube_embed_url(url):
    if not url:
        return None

    # Handles:
    # youtube.com/watch?v=ID
    # youtu.be/ID
    # youtube.com/embed/ID
    regex = r"(?:v=|youtu\.be/|embed/)([a-zA-Z0-9_-]{11})"
    match = re.search(regex, url)

    if match:
        video_id = match.group(1)
        return f"https://www.youtube.com/embed/{video_id}"
    
    return None

def recipe_view(request):
    recipe = Recipe.objects.get(id=1)  # example

    embed_url = get_youtube_embed_url(recipe.youtube_url)

    return render(request, "recipe_detail.html", {
        "recipe": recipe,
        "embed_url": embed_url
    })

def warning(request):
    return render(request,"warning.html")

def delete_review_admin(request, id):
    review = Recommendation.objects.get(id=id)
    recipe_id = review.recipe.id  # Save the recipe ID so we can redirect back to it
    review.delete()
    messages.success(request, "Comment deleted successfully!")
    return redirect('admin_recipe_detail', recipe_id=recipe_id)

def admin_recipe_detail(request, recipe_id):
    if 'email' not in request.session:
        return redirect("admin_login") # Keep it secure!
        
    recipe = get_object_or_404(Recipe, id=recipe_id)
    recommendations = Recommendation.objects.filter(recipe=recipe)
    
    # Get the YouTube embed URL if you have that helper function
    embed_url = get_youtube_embed_url(recipe.youtube_url) if recipe.youtube_url else None

    return render(request, "admin_recipe_detail.html", {
        'recipe': recipe,
        'recommendations': recommendations,
        'embed_url': embed_url
    })

def admin_edit_recipe_save(request, recipe_id):
    if request.method == 'POST':
        recipe = get_object_or_404(Recipe, id=recipe_id)
        
        # Updating text fields
        recipe.recipe_name = request.POST.get('recipe_name')
        recipe.cooking_time = request.POST.get('cooking_time')
        recipe.category = request.POST.get('category')
        recipe.steps = request.POST.get('instructions')
        recipe.ingredients = request.POST.get('ingredients')
        
        # Updating image if provided
        if request.FILES.get('image'):
            recipe.recipe_image = request.FILES['image']
            
        recipe.save()
        messages.success(request, "Recipe updated successfully by Admin!")
        return redirect('admin_recipe_detail', recipe_id=recipe.id)

#  DELETE ACCOUNT — USER

def delete_user_account_page(request):
    """Show the user delete-account confirmation page."""
    return render(request, "delete_account_user.html")


def delete_user_account_confirm(request):
    """Verify credentials, send farewell email, wipe user data."""
    if request.method != "POST":
        return redirect("delete_user_account_page")

    email_input    = request.POST.get("email", "").strip()
    password_input = request.POST.get("password", "").strip()

    try:
        user_obj = user.objects.get(email=email_input)
    except user.DoesNotExist:
        messages.error(request, "No user account found with that email.")
        return redirect("delete_user_account_page")

    if user_obj.password != password_input:
        messages.error(request, "Incorrect password. Account not deleted.")
        return redirect("delete_user_account_page")

    # Send deletion email
    try:
        send_mail(
            subject="Your Cooking Companion Account Has Been Deleted",
            message=(
                f"Hi {user_obj.name},\n\n"
                "Your Cooking Companion account has been permanently deleted as requested.\n\n"
                "All your recipes, saved recipes, and profile data have been removed.\n\n"
                "We're sad to see you go. If this was a mistake, please create a new account.\n\n"
                "— The Cooking Companion Team"
            ),
            from_email="Cooking Companion <computronicsprojects1999@gmail.com>",
            recipient_list=[email_input],
            fail_silently=True,
        )
    except Exception:
        pass

    # Delete all associated data then the user
    SavedRecipe.objects.filter(user=user_obj).delete()
    Recommendation.objects.filter(user=user_obj).delete()
    ChefFollow.objects.filter(follower_email=email_input).delete()
    ChefFollow.objects.filter(followed_email=email_input).delete()
    user_obj.delete()

    # Clear session
    request.session.flush()
    messages.success(request, "Your account has been permanently deleted. A confirmation email has been sent.")
    return redirect("homepage")


#  DELETE ACCOUNT — CHEF

def delete_chef_account_page(request):
    """Show the chef delete-account confirmation page."""
    return render(request, "delete_account_chef.html")


def delete_chef_account_confirm(request):
    """Verify credentials, send farewell email, wipe chef data."""
    if request.method != "POST":
        return redirect("delete_chef_account_page")

    email_input    = request.POST.get("email", "").strip()
    password_input = request.POST.get("password", "").strip()

    try:
        chef_obj = chef.objects.get(email=email_input)
    except chef.DoesNotExist:
        messages.error(request, "No chef account found with that email.")
        return redirect("delete_chef_account_page")

    if chef_obj.password != password_input:
        messages.error(request, "Incorrect password. Account not deleted.")
        return redirect("delete_chef_account_page")

    # Send deletion email
    try:
        send_mail(
            subject="Your Cooking Companion Chef Account Has Been Deleted",
            message=(
                f"Hi {chef_obj.name},\n\n"
                "Your Cooking Companion chef account has been permanently deleted as requested.\n\n"
                "All your recipes, bookings, and profile data have been removed.\n\n"
                "We're sad to see you go. If this was a mistake, please create a new chef account.\n\n"
                "— The Cooking Companion Team"
            ),
            from_email="Cooking Companion <computronicsprojects1999@gmail.com>",
            recipient_list=[email_input],
            fail_silently=True,
        )
    except Exception:
        pass

    # Delete all associated data then the chef
    Recipe.objects.filter(user_email=email_input).delete()
    Booking.objects.filter(chef_email=email_input).delete()
    ChefFollow.objects.filter(follower_email=email_input).delete()
    ChefFollow.objects.filter(followed_email=email_input).delete()
    chef_obj.delete()

    # Clear session
    request.session.flush()
    messages.success(request, "Your account has been permanently deleted. A confirmation email has been sent.")
    return redirect("homepage")
