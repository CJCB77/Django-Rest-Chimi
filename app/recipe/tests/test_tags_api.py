"""
Test Tags API
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag
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