# serializers.py
from rest_framework import serializers
from .models import Recipe

class RecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = [
            'id', 'recipe_name', 'recipe_image', 'youtube_url',
            'category', 'cooking_time', 'ingredients',
            'description', 'steps', 'user_name', 'user_email',
            'status', 'views',
        ]