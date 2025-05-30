"""
Tests for recipe APIs
"""
from decimal import Decimal
import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Recipe,
    Tag,
    Ingredient
)
from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)

User = get_user_model()
RECIPES_URL = reverse("recipe:recipe-list")


def detail_url(recipe_id):
    """Create and return a recipe detail URL"""
    return reverse('recipe:recipe-detail', args=[recipe_id])

def image_upload_url(recipe_id):
    """Create and return an image upload URL"""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])

# ** params lets the func accept any number of keyword arguments
def create_recipe(user, **params):
    """Create and return a simple recipe """
    defaults = {
        'title': 'Sample recipe title',
        'time_minutes': 22,
        'price': Decimal('5.25'),
        'description': 'Sample description',
        'link': 'http://example.com/recipe.pdf'
    }
    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


class PublicRecipeAPITests(TestCase):
    """Test unauthenticated API requests"""

    def seUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that auth is required to call the recipe API"""
        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """Class to test authenticated API requests"""

    def setUp(self):
        user_details = {
            "email": "test1@example.com",
            "password": "test12345",
            "name": "John Doe"
        }
        self.user = User.objects.create_user(**user_details)

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_recipes(self):
        """Test that the requested endpoint retrieve a list recipes"""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """Test the list of recipes is limited to the authenticated user"""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        # Use another user, for a new recipe list
        new_user = User.objects.create(
            email="test2@example.com",
            password="pass12345"
        )
        create_recipe(user=new_user)
        create_recipe(user=new_user)

        recipes = Recipe.objects.all().filter(user=self.user).order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test get recipe detail"""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """Test recipe creation endpoint"""
        payload = {
            'title': 'Sample recipe title',
            'time_minutes': 5,
            'price': Decimal('5.99'),
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)

        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """Test partial update of a recipe"""
        original_link = "https://example.com/recipe.pdf"
        recipe = create_recipe(
            user=self.user,
            title="My sample title",
            link=original_link,
        )

        payload = {'title': 'New title!'}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        """Test full update of a recipe"""
        recipe = create_recipe(
            user=self.user,
            title="My sample title",
            link="https://example.com/recipe.pdf",
            description="Sample recipe description",
        )

        payload = {
            'title': 'New title!',
            'link': 'https://example.com/new-recipe.pdf',
            'description': 'New recipe description',
            'time_minutes': 10,
            'price': Decimal('2.50'),
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        """Test that updating the recipe user returns an error"""
        new_user = User.objects.create_user(
            email="test2@example.com",
            password="pass12345"
        )
        recipe = create_recipe(user=self.user)

        payload = {'user': new_user.id}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test deleting a recipe successful"""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_deleting_other_user_recipe_error(self):
        """Test deleting other user recipe gives error"""
        new_user = User.objects.create_user(
            email="test2@example.com",
            password="pass12345"
        )
        recipe = create_recipe(user=new_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_tags(self):
        """Test creating a recipe with tags"""
        payload = {
            'title': 'Thai Pwan Curry',
            'time_minutes': 30,
            'price': Decimal('2.50'),
            'tags': [{'name':'Thai'}, {'name': 'Dinner'}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'], 
                user=self.user).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        """Test creating a recipe with existing tag."""
        tag_indian = Tag.objects.create(name='Indian', user=self.user)
        payload = {
            'title': 'Pongai',
            'time_minutes': 30,
            'price': Decimal('2.50'),
            'tags': [{'name':'Indian'}, {'name': 'Dinner'}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_indian, recipe.tags.all())
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'], 
                user=self.user).exists()
            self.assertTrue(exists)
    
    def test_create_tag_on_update(self):
        """Test creating tag when updating a recipe"""
        recipe = create_recipe(user=self.user)

        payload = {'tags': [{'name': 'Lunch'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='Lunch')
        self.assertIn(new_tag, recipe.tags.all())
    
    def test_update_recipe_assign_tag(self):
        """Test assigning an existing tag when updating a recipe"""
        tag_breakfast = Tag.objects.create(name='Breakfast', user=self.user)
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(name='Lunch', user=self.user)

        payload = {'tags': [{'name': 'Lunch'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())
    
    def test_clear_recipe_tags(self):
        """Test clearing a recipes tags"""
        tag = Tag.objects.create(name='Dinner', user=self.user)
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {'tags': []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_ingredient_on_update(self):
        """Test creating an ingredient when updating a recipe"""
        recipe = create_recipe(user=self.user)
        payload = {
            'ingredients': [{'name': 'Lemon'}]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingredient = Ingredient.objects.get(user=self.user, name='Lemon')
        self.assertIn(new_ingredient, recipe.ingredients.all())
    
    def test_create_recipe_with_new_ingredients(self):
        """Test creating a recipe with new ingredients"""
        payload = {
            'title': 'Cauliflower Tacos',
            'time_minutes': 60,
            'price': Decimal('4.30'),
            'ingredients': [{'name':'Cauliflower'}, {'name':'Salt'}]
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                user=self.user,
                name=ingredient['name']
            ).exists()
            self.assertTrue(exists)
    
    def test_create_recipe_with_existing_ingredient(self):
        """Test creating a new recipe with existing ingredient"""
        ingredient = Ingredient.objects.create(name='Lemon', user=self.user)
        payload = {
            'title': 'Cauliflower Tacos',
            'time_minutes': 60,
            'price': Decimal('4.30'),
            'ingredients': [{'name':'Lemon'}, {'name':'Salt'}]
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient, recipe.ingredients.all())

        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                user=self.user,
                name=ingredient['name']
            ).exists()
            self.assertTrue(exists)

    def test_update_recipe_assign_ingredient(self):
        """Test assigning an existing ingredient when updating a recipe"""
        ingredient = Ingredient.objects.create(name='Lemon', user=self.user)
        recipe = Recipe.objects.create(
            title='Cauliflower Tacos', 
            time_minutes=30, 
            price=5.00, 
            user=self.user
        )
        recipe.ingredients.add(ingredient)

        new_ingredient = Ingredient.objects.create(name='Salt', user=self.user)

        # Overwrite with new_ingredient
        payload = {
            'ingredients': [{'name': 'Salt'}]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(new_ingredient, recipe.ingredients.all())
        self.assertNotIn(ingredient, recipe.ingredients.all())
    
    def test_clear_recipe_ingredients(self):
        """Test clearing a recipe ingredients"""
        recipe = Recipe.objects.create(
            title='Steak and mushroom sauce', 
            time_minutes=5, price=5.00, 
            user=self.user
        )
        recipe.ingredients.add(Ingredient.objects.create(name='Lemon', user=self.user))
        recipe.ingredients.add(Ingredient.objects.create(name='Salt', user=self.user))

        payload = {
            'ingredients': []
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)
    
    def test_filter_by_tags(self):
        """Test that recipes are filtered by tags"""
        r1 = create_recipe(user=self.user, title="Thai Vegetable Curry")
        r2 = create_recipe(user=self.user, title="Aubergine with Tahini")
        r3 = create_recipe(user=self.user, title="Fish and chips")

        tag1 = Tag.objects.create(user=self.user, name="Vegan")
        tag2 = Tag.objects.create(user=self.user, name="Vegetarian")
        r1.tags.add(tag1)
        r2.tags.add(tag2)

        params = {'tags':f'{tag1.id},{tag2.id}'}
        res = self.client.get(RECIPES_URL, params)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)
    
    def test_filter_by_ingredients(self):
        r1 = create_recipe(user=self.user, title="Posh Beans on Toast")
        r2 = create_recipe(user=self.user, title="Chicken Cacciatore")
        in1 = Ingredient.objects.create(user=self.user, name='Feta cheese')
        in2 = Ingredient.objects.create(user=self.user, name='Chicken')
        
        r1.ingredients.add(in1)
        r2.ingredients.add(in2)
        r3 = create_recipe(user=self.user, title="Red Lentil Dal")

        params = {'ingredients':f'{in1.id},{in2.id}'}
        res = self.client.get(RECIPES_URL, params)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)


class ImageUploadTests(TestCase):
    """Tests for the image upload API"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='user@example.com',
            password='pass12345'
        )
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        """Test uploading an image to a recipe"""
        url = image_upload_url(self.recipe.id)
        # Create a temp fake image file
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            # Creates a tiny 10x10 black square img
            img = Image.new('RGB', (10,10))
            img.save(image_file, format='JPEG')
            # Reset file pointer to start
            image_file.seek(0)
            payload = {'image':image_file}
            res = self.client.post(url, payload, format='multipart')
        
        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.recipe.id)
        payload = {'image':'notanimg'}
        res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)