"""
Test Tags API
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Tag,
    Recipe,
)
from recipe.serializers import TagSerializer


TAGS_URL = reverse('recipe:tag-list')

def create_user(email='user@example.com', password='testpass12345'):
    return get_user_model().objects.create_user(email, password)

def detail_url(tag_id):
    """Create and return a tag detail url"""
    return reverse('recipe:tag-detail', args=[tag_id])


class PublicTagApiTests(TestCase):
    """Test unauthenticated tag API requests """

    def setUp(self):
        self.client = APIClient()
    
    def test_auth_required(self):
        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
    

class PrivateTagsApiTests(TestCase):
    """Test authenticated API requests"""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)
    
    def test_retrieve_tags(self):
        """Test retrieving a list of Tags"""
        Tag.objects.create(name="Healthy", user=self.user)
        Tag.objects.create(name="Dessert", user=self.user)
        
        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Confirms the API returns what’s actually in the database 
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test that an user tags are limited to their own"""
        tag = Tag.objects.create(name="Healthy", user=self.user)

        user2 = create_user('user2@exmaple.com','passwd12345')
        Tag.objects.create(name="One-Pot", user=user2)

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.data[0]['id'], tag.id)

    def test_update_tag(self):
        """Test Updating a tag"""
        tag = Tag.objects.create(user=self.user, name="Fitness")

        payload = {
            'name': 'Dessert'
        }
        url = detail_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])
    
    def test_delete_tag(self):
        """Test succesful deletion of a tag"""
        tag = Tag.objects.create(user=self.user, name="Fitness")
        url = detail_url(tag.id)

        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tags = Tag.objects.filter(user=self.user)
        self.assertFalse(tags.exists())
    
    def test_filter_tags_assigned_to_recipes(self):
        """Test listing tags to those assigned to recipes"""
        tag1 = Tag.objects.create(user=self.user, name='Breakfast')
        tag2 = Tag.objects.create(user=self.user, name='Lunch')
        recipe = Recipe.objects.create(
            title='Green Eggs on Toast',
            time_minutes=10,
            price=Decimal('2.50'),
            user=self.user
        )
        recipe.tags.add(tag1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)
    
    def test_filtered_tags_unique(self):
        """Test filtered tags return a unique list"""
        tag = Tag.objects.create(user=self.user, name='Breakfast')
        Tag.objects.create(user=self.user, name='Dinner')
        recipe1 = Recipe.objects.create(
            user= self.user,
            title='Pancakes',
            time_minutes=5,
            price=Decimal('5.00')
        )
        recipe2 = Recipe.objects.create(
            user= self.user,
            title='Porridge',
            time_minutes=3,
            price=Decimal('2.00')
        )
        recipe1.tags.add(tag)
        recipe2.tags.add(tag)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)