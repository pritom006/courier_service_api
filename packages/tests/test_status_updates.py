from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from unittest.mock import patch, MagicMock
from packages.models import Package, PackageStatusUpdate
from packages.views import PackageStatusUpdateViewSet

class PackageStatusUpdateViewSetTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()

        self.mock_admin_user = MagicMock()
        self.mock_admin_user.is_admin = True
        self.mock_admin_user.is_courier = False
        self.mock_admin_user.is_customer = False
        self.mock_admin_user.pk = 1

        self.mock_courier_user = MagicMock()
        self.mock_courier_user.is_admin = False
        self.mock_courier_user.is_courier = True
        self.mock_courier_user.is_customer = False
        self.mock_courier_user.pk = 2

        self.mock_customer_user = MagicMock()
        self.mock_customer_user.is_admin = False
        self.mock_customer_user.is_courier = False
        self.mock_customer_user.is_customer = True
        self.mock_customer_user.pk = 3

        self.mock_package = MagicMock()
        self.mock_package.pk = 1
        self.mock_package.customer = self.mock_customer_user
        self.mock_package.courier = self.mock_courier_user

        self.mock_status_update = MagicMock()
        self.mock_status_update.pk = 1
        self.mock_status_update.package = self.mock_package
        self.mock_status_update.status = "pending"
        self.mock_status_update.notes = "Initial status"
        self.mock_status_update.updated_by = self.mock_admin_user

        self.serialized_status_update_data = {
            'id': 1,
            'status': 'pending',
            'notes': 'Initial status',
            'updated_by': 1,
            'created_at': '2025-03-07T13:51:47.752280Z'
        }

        self.mock_queryset = MagicMock()
        self.mock_queryset.all.return_value = [self.mock_status_update]
        self.mock_queryset.filter.return_value = self.mock_queryset
        self.mock_queryset.__iter__.return_value = iter([self.mock_status_update])

    @patch('packages.views.Package.objects.get')
    @patch('packages.views.PackageStatusUpdateSerializer')
    def test_get_queryset_admin_access(self, mock_serializer, mock_get):
        """Test that admin can see all status updates for a package"""
        self.client.force_authenticate(user=self.mock_admin_user)

        # Mock package retrieval
        mock_get.return_value = self.mock_package

        # Mock serializer
        mock_serializer_instance = MagicMock()
        mock_serializer_instance.data = [self.serialized_status_update_data]
        mock_serializer.return_value = mock_serializer_instance

        url = reverse('package-status-list', args=[1])
        response = self.client.get(url)

        # Assertions
        mock_get.assert_called_once_with(pk='1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('packages.views.Package.objects.get')
    @patch('packages.views.PackageStatusUpdateSerializer')
    def test_get_queryset_courier_access(self, mock_serializer, mock_get):
        """Test that assigned courier can see status updates for their package"""
        self.client.force_authenticate(user=self.mock_courier_user)
        mock_get.return_value = self.mock_package

        mock_serializer_instance = MagicMock()
        mock_serializer_instance.data = [self.serialized_status_update_data]
        mock_serializer.return_value = mock_serializer_instance

        url = reverse('package-status-list', args=[1])
        response = self.client.get(url)

        mock_get.assert_called_once_with(pk='1')  # Fixed integer PK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('packages.views.Package.objects.get')
    @patch('packages.views.PackageStatusUpdateSerializer')
    def test_get_queryset_customer_access(self, mock_serializer, mock_get):
        """Test that package customer can see status updates for their package"""
        self.client.force_authenticate(user=self.mock_customer_user)
        mock_get.return_value = self.mock_package

        mock_serializer_instance = MagicMock()
        mock_serializer_instance.data = [self.serialized_status_update_data]
        mock_serializer.return_value = mock_serializer_instance

        url = reverse('package-status-list', args=[1])
        response = self.client.get(url)

        mock_get.assert_called_once_with(pk='1')  # Fixed integer PK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('packages.views.Package.objects.get')
    def test_get_queryset_unauthorized_access(self, mock_get):
        """Test that unauthorized users cannot see status updates for a package"""
        mock_unrelated_user = MagicMock()
        mock_unrelated_user.is_admin = False
        mock_unrelated_user.is_courier = False
        mock_unrelated_user.is_customer = True
        mock_unrelated_user.pk = 4

        self.client.force_authenticate(user=mock_unrelated_user)
        mock_get.return_value = self.mock_package

        self.mock_package.status_updates.all.return_value = []

        url = reverse('package-status-list', args=[1])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    @patch('packages.views.Package.objects.get')
    def test_get_queryset_package_not_found(self, mock_get):
        """Test behavior when the requested package does not exist"""
        self.client.force_authenticate(user=self.mock_admin_user)
        mock_get.side_effect = Package.DoesNotExist

        url = reverse('package-status-list', args=[999])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

   
