"""
Tests for ingredients API.
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from core.models import (
    Ingredient,
    Recipe
)

from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')

def create_detail_url(ingredient_id):
    """Create and return an ingredient detail URL"""
    return reverse('recipe:ingredient-detail', args=[ingredient_id])

def create_user(email='user@example.com', password='testpass12345'):
    return get_user_model().objects.create_user(email, password)


class PublicIngredientsApiTests(TestCase):
    """Test unauthenticated API requests"""

    def setUp(self):
        self.client = APIClient()
    
    def test_auth_required(self):
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTest(TestCase):
    """Test unauthenticated API requests"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)
    
    def test_retrieve_ingredients_list(self):
        """Test retrieving a list of ingredients"""
        ingredient = Ingredient.objects.create(
            name='Ingredient1',
            user = self.user
        )
        another_ingredient = Ingredient.objects.create(
            name='Ingredient2',
            user = self.user
        )
        ingredients = Ingredient.objects.all().order_by('-name')
        # Convert ingredients into json using serializer
        serializer = IngredientSerializer(ingredients, many=True)

        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
    
    def test_ingredients_limited_to_user(self):
        """Test than an user only retrieves their ingredients"""
        ingredient = Ingredient.objects.create(
            name='Ingredient1',
            user = self.user
        )
        new_user = create_user(email='test2@example.com', password='pass12345')
        ingredient2 = Ingredient.objects.create(
            name='Ingredient2',
            user = new_user
        )
        # Get ingredients for self.user
        ingredients = Ingredient.objects.all().filter(user=self.user)
        serializer = IngredientSerializer(ingredients)

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data),1)
        self.assertEqual(res.data[0]['name'], ingredient.name)
        
    def test_update_ingredient(self):
        """Test updating an ingredient"""
        ingredient = Ingredient.objects.create(
            name='Pepper',
            user = self.user
        )
        payload = {
            'name':'Black Pepper'
        }
        ingredient_url = create_detail_url(ingredient.id)
        res = self.client.patch(ingredient_url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])

    def test_delete_ingredient(self):
        """Test deleting and ingredient"""
        ingredient = Ingredient.objects.create(
            name='Pepper',
            user = self.user
        )
        ingredient_url = create_detail_url(ingredient.id)
        res = self.client.delete(ingredient_url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertFalse(ingredients.exists())
        
    
    
 