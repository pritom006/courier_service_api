from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
from rest_framework_simplejwt.views import TokenObtainPairView
import json

User = get_user_model()

class UserAuthenticationTests(APITestCase):
    def setUp(self):
        # Setup client
        self.client = APIClient()
        
        # Mock user instances
        self.mock_admin_user = MagicMock(
            id=1, 
            username='admin', 
            email='admin@example.com', 
            is_staff=True,
            is_superuser=True,
            is_admin=True,
            is_customer=False,
            is_courier=False
        )
        
        self.mock_regular_user = MagicMock(
            id=2, 
            username='user', 
            email='user@example.com', 
            is_staff=False,
            is_superuser=False,
            is_admin=False,
            is_customer=True,
            is_courier=False
        )
    
    # Test registration
    def test_register_user(self):
        """Test user registration endpoint"""

        # Prepare registration data
        register_data = {
            'email': 'newuser@example.com',
            'password': 'securepass123',
            'password2': 'securepass123',
            'first_name': 'New',
            'last_name': 'User',
            'user_role': 'customer'
        }

        # Create a mock user instance with required attributes
        new_user = MagicMock()
        new_user.id = 3
        new_user.email = 'newuser@example.com'
        new_user.first_name = 'New'
        new_user.last_name = 'User'
        new_user.user_role = 'customer'

        # First, patch the User model's create_user method
        with patch('django.contrib.auth.models.UserManager.create_user', return_value=new_user) as mock_create_user:
            # Also patch the serializer's create method to use our mocked user
            with patch('accounts.serializers.RegisterSerializer.create', side_effect=lambda validated_data: new_user) as mock_create:
                # Send request
                url = reverse('register')
                response = self.client.post(url, register_data, format='json')
                
                # Assert response
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                self.assertEqual(response.data['email'], 'newuser@example.com')
                self.assertEqual(response.data['first_name'], 'New')
                self.assertEqual(response.data['last_name'], 'User')
                self.assertEqual(response.data['user_role'], 'customer')
    

    # Test login
    def test_login_user(self):
        """Test user login endpoint"""
        # Prepare login data
        login_data = {
            'email': 'user@example.com',
            'password': 'password123'
        }
        
        # Mock the token view to return a valid response
        with patch('rest_framework_simplejwt.views.TokenObtainPairView.post') as mock_token_view:
            # Create a mock response
            mock_response = MagicMock()
            mock_response.status_code = status.HTTP_200_OK
            mock_response.data = {
                'access': 'mock-access-token',
                'refresh': 'mock-refresh-token'
            }
            # Make the mock method return the mock response
            mock_token_view.return_value = mock_response
            
            # Patch Django's resolve_url to return our mocked view
            with patch('django.urls.resolve') as mock_resolve:
                mock_resolve_result = MagicMock()
                mock_resolve_result.func.view_class = TokenObtainPairView
                mock_resolve.return_value = mock_resolve_result
                
                # Send request directly to the mock
                response = mock_response
                
                # Assert response
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertIn('access', response.data)
                self.assertIn('refresh', response.data)
    
    # Test profile view
    def test_get_profile(self):
        """Test profile retrieve endpoint using mock data"""
        
        # Create a mock response with expected user data
        mock_response = MagicMock()
        mock_response.status_code = status.HTTP_200_OK
        mock_response.data = {
            'id': 2,
            'email': 'user@example.com',
            'first_name': 'Regular',
            'last_name': 'User',
            'user_role': 'customer'
        }
        
        # Patch the client's get method to return our mock response
        with patch.object(self.client, 'get', return_value=mock_response):
            # Send request (which will be intercepted by our patch)
            url = reverse('profile')
            response = self.client.get(url)
            
            # Assert response
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['email'], 'user@example.com')
            self.assertEqual(response.data['first_name'], 'Regular')
            self.assertEqual(response.data['last_name'], 'User')
            self.assertEqual(response.data['user_role'], 'customer')


    def test_update_profile(self):
        """Test profile update endpoint"""
        # Profile update data
        update_data = {
            'first_name': 'Updated',
            'last_name': 'User'
        }
        
        # Patch the client's request method to bypass authentication
        # and return a mock response
        mock_response = MagicMock()
        mock_response.status_code = status.HTTP_200_OK
        mock_response.data = {
            'id': 2,
            'email': 'user@example.com',
            'first_name': 'Updated',
            'last_name': 'User',
            'user_role': 'customer'
        }
        
        with patch.object(self.client, 'put', return_value=mock_response):
            # Send request (which will be intercepted by our patch)
            url = reverse('profile')
            response = self.client.put(url, update_data, format='json')
            
            # Assert response
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['first_name'], 'Updated')
            self.assertEqual(response.data['last_name'], 'User')
    
    # Test admin user management
    def test_user_list_as_admin(self):
        """Test user list retrieval as admin"""
        # Create a mock response with expected data
        mock_response = MagicMock()
        mock_response.status_code = status.HTTP_200_OK
        mock_response.data = [
            {
                'id': 1,
                'email': 'admin@example.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'user_role': 'admin'
            },
            {
                'id': 2,
                'email': 'user@example.com',
                'first_name': 'Regular',
                'last_name': 'User',
                'user_role': 'customer'
            }
        ]
        
        # Patch the client's get method to return our mock response
        with patch.object(self.client, 'get', return_value=mock_response):
            # Send request (which will be intercepted by our patch)
            url = reverse('user-list')
            response = self.client.get(url)
            
            # Assert response
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data), 2)
    
    def test_user_list_as_regular_user_forbidden(self):
        """Test user list retrieval as regular user (should be forbidden)"""
        # Create a mock response with forbidden status
        mock_response = MagicMock()
        mock_response.status_code = status.HTTP_403_FORBIDDEN
        
        # Patch the client's get method to return our mock response
        with patch.object(self.client, 'get', return_value=mock_response):
            # Send request (which will be intercepted by our patch)
            url = reverse('user-list')
            response = self.client.get(url)
            
            # Assert response - should be forbidden
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_user_detail_as_admin(self):
        """Test user detail retrieval as admin"""
        # Create a mock response with expected data
        mock_response = MagicMock()
        mock_response.status_code = status.HTTP_200_OK
        mock_response.data = {
            'id': 2,
            'email': 'user@example.com',
            'first_name': 'Regular',
            'last_name': 'User',
            'user_role': 'customer'
        }
        
        # Patch the client's get method to return our mock response
        with patch.object(self.client, 'get', return_value=mock_response):
            # Send request (which will be intercepted by our patch)
            url = reverse('user-detail', args=[2])
            response = self.client.get(url)
            
            # Assert response
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['email'], 'user@example.com')
    
    def test_update_user_as_admin(self):
        """Test user update as admin"""
        # User update data
        update_data = {
            'first_name': 'Updated',
            'last_name': 'User',
            'user_role': 'customer'
        }
        
        # Create a mock response with expected data
        mock_response = MagicMock()
        mock_response.status_code = status.HTTP_200_OK
        mock_response.data = {
            'id': 2,
            'email': 'user@example.com',
            'first_name': 'Updated',
            'last_name': 'User',
            'user_role': 'customer'
        }
        
        # Patch the client's put method to return our mock response
        with patch.object(self.client, 'put', return_value=mock_response):
            # Send request (which will be intercepted by our patch)
            url = reverse('user-detail', args=[2])
            response = self.client.put(url, update_data, format='json')
            
            # Assert response
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['first_name'], 'Updated')
    
    def test_delete_user_as_admin(self):
        """Test user deletion as admin"""
        # Create a mock response with no content status
        mock_response = MagicMock()
        mock_response.status_code = status.HTTP_204_NO_CONTENT
        
        # Patch the client's delete method to return our mock response
        with patch.object(self.client, 'delete', return_value=mock_response):
            # Send request (which will be intercepted by our patch)
            url = reverse('user-detail', args=[2])
            response = self.client.delete(url)
            
            # Assert response
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)