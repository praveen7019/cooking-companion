from django.db import models

class user(models.Model):
    name = models.TextField()
    email = models.CharField(max_length=254)
    contact = models.TextField()
    password = models.TextField()
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    
    # Followers: users who follow this user
    followers = models.ManyToManyField(
        'self', 
        symmetrical=False, 
        related_name='following', 
        blank=True
    )

    def __str__(self):
        return self.name

class admin(models.Model):
    admin_email = models.TextField(max_length=255)
    admin_password = models.TextField(max_length=50)

class chef(models.Model):
    name = models.TextField(max_length=255)
    email = models.TextField(max_length=255)
    contact = models.TextField(max_length=255)
    password = models.TextField(max_length=255)
    experince = models.TextField(max_length=50)
    chef_image = models.FileField(upload_to="chef_image/")

class Recipe(models.Model):
    recipe_name = models.CharField(max_length=200)
    recipe_image = models.ImageField(
        upload_to='recipe_images/',
        blank=True,
        null=True,
        default='recipe_images/default.png'
    )
    recipe_video = models.FileField(upload_to='recipes_video/', blank=True, null=True)
    youtube_url = models.CharField(max_length=500, blank=True, null=True)
    category = models.CharField(max_length=100)
    cooking_time = models.IntegerField()
    ingredients = models.TextField()
    description = models.CharField(max_length=200)
    steps = models.TextField()
    user_name = models.CharField(max_length=200)
    user_email = models.CharField(max_length=200)
    status = models.TextField(default='Pending')
    views = models.IntegerField(default=0)

class SavedRecipe(models.Model):
    user = models.ForeignKey(user, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'recipe')


class Recommendation(models.Model):
    # Both user and chef can be null, allowing either one to leave a review
    user = models.ForeignKey(user, on_delete=models.CASCADE, null=True, blank=True)
    chef = models.ForeignKey(chef, on_delete=models.CASCADE, null=True, blank=True)
    
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE) 
    rating = models.IntegerField(default=0) 
    comment = models.TextField(blank=True, null=True) 
    created_at = models.DateTimeField(auto_now_add=True) 

    # Removed unique_together here to prevent database conflicts with null values

    def __str__(self):
        # Prevent the "NoneType has no attribute 'name'" crash
        if self.user:
            return f"User: {self.user.name} rated {self.recipe.recipe_name}"
        elif self.chef:
            return f"Chef: {self.chef.name} rated {self.recipe.recipe_name}"
        return f"Unknown rated {self.recipe.recipe_name}"

    class Meta:
        unique_together = ('user', 'recipe')  # one user can rate a recipe only once

    def __str__(self):
        return f"{self.user.name} rated {self.recipe.recipe_name}"
    
class Booking(models.Model):
    chef_email = models.EmailField()
    user_email = models.EmailField()
    user_name = models.CharField(max_length=255)
    chef_name = models.CharField(max_length=255)
    event_date = models.DateField()
    event_location = models.CharField(max_length=255)
    number_of_people = models.IntegerField()
    special_instructions = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status=models.TextField(default='Pending')

    class Meta:
        unique_together = ('chef_email', 'event_date')


class ChefFollow(models.Model):
    """Tracks follows where the follower OR the followed is a chef.
    Also used for user→chef follows (since user.followers M2M only covers user→user)."""
    follower_email = models.EmailField()
    followed_email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower_email', 'followed_email')

    def __str__(self):
        return f"{self.follower_email} → {self.followed_email}"

