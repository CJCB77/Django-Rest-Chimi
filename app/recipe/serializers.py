"""
Serializers for recipe APIs
"""
from core.models import (
    Recipe,
    Tag,
)
from rest_framework import serializers


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer class for the recipe model"""

    class Meta():
        model = Recipe
        fields = ['id', 'title', 'time_minutes', 'price', 'link']
        read_only_fields = ['id']


class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for recipe detail view"""

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description']


class TagSerializer(serializers.ModelSerializer):
    """Serializer Class for the tag model"""

    class Meta():
        model = Tag
        fields = ['id', 'name']
        reado_only_fields = ['id']