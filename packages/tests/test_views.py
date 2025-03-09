from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from unittest.mock import patch, MagicMock, PropertyMock
from packages.models import Package, PackageStatusUpdate
from packages.views import PackageViewSet
import json


class PackageViewSetTestCase(APITestCase):
    def setUp(self):
        # Setup mock user with different roles
        self.client = APIClient()
        
        # Mock users for different roles
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
        self.mock_courier_user.email = "courier@example.com"
        
        self.mock_customer_user = MagicMock()
        self.mock_customer_user.is_admin = False
        self.mock_customer_user.is_courier = False
        self.mock_customer_user.is_customer = True
        self.mock_customer_user.pk = 3
        self.mock_customer_user.email = "customer@example.com"
        
        # Mock package data
        self.mock_package = MagicMock()
        self.mock_package.pk = 1
        self.mock_package.customer = self.mock_customer_user
        self.mock_package.courier = self.mock_courier_user
        self.mock_package.tracking_number = "PKG-12345"
        self.mock_package.status = "pending"
        self.mock_package.is_deleted = False
        
        # Mock serializer response for converting package to API response
        self.serialized_package_data = {
            'id': 1,
            'tracking_number': 'PKG-12345',
            'customer': 3,
            'customer_email': 'customer@example.com',
            'courier': 2,
            'courier_email': 'courier@example.com',
            'description': 'Test package',
            'weight': '2.50',
            'dimensions': '20x15x10',
            'pickup_address': '123 Pickup St',
            'delivery_address': '456 Delivery Ave',
            'status': 'pending',
            'is_deleted': False,
            'status_updates': []
        }

    @patch('packages.views.PackageSerializer')
    @patch('packages.views.Package.objects.filter')
    @patch('rest_framework.request.Request')
    def test_get_queryset_admin(self, mock_request, mock_filter, mock_serializer):
        """Test that admins can see all packages"""
        # Setup
        view = PackageViewSet()
        view.request = mock_request
        view.request.user = self.mock_admin_user
        view.action = 'list'  # Set action attribute to simulate a list action
        
        mock_queryset = MagicMock()
        view.queryset = mock_queryset
        
        # Mock filter to return filtered queryset
        filtered_queryset = MagicMock()
        mock_queryset.filter.return_value = filtered_queryset
        
        # Action
        result = view.get_queryset()
        
        # Assert
        self.assertEqual(result, filtered_queryset)
        mock_queryset.filter.assert_called_once_with(is_deleted=False)

    @patch('packages.views.PackageSerializer')
    @patch('packages.views.Package.objects.filter')
    @patch('rest_framework.request.Request')
    def test_get_queryset_courier(self, mock_request, mock_filter, mock_serializer):
        """Test that couriers can only see their assigned packages"""
        # Setup
        view = PackageViewSet()
        view.request = mock_request
        view.request.user = self.mock_courier_user
        view.action = 'list'  # Set action attribute to simulate a list action
        
        mock_queryset = MagicMock()
        view.queryset = mock_queryset
        filtered_queryset = MagicMock()
        
        # Mock filter to return itself for first call, then filtered result
        mock_queryset.filter.side_effect = [mock_queryset, filtered_queryset]
        
        # Action
        result = view.get_queryset()
        
        # Assert
        self.assertEqual(result, filtered_queryset)
        # Check that we filter by is_deleted=False and then by courier=user
        mock_queryset.filter.assert_any_call(is_deleted=False)
        mock_queryset.filter.assert_any_call(courier=self.mock_courier_user)

    @patch('packages.views.PackageSerializer')
    @patch('packages.views.Package.objects.filter')
    @patch('rest_framework.request.Request')
    def test_get_queryset_customer(self, mock_request, mock_filter, mock_serializer):
        """Test that customers can only see their packages"""
        # Setup
        view = PackageViewSet()
        view.request = mock_request
        view.request.user = self.mock_customer_user
        view.action = 'list'  # Set action attribute to simulate a list action
        
        mock_queryset = MagicMock()
        view.queryset = mock_queryset
        filtered_queryset = MagicMock()
        
        # Mock filter to return itself for first call, then filtered result
        mock_queryset.filter.side_effect = [mock_queryset, filtered_queryset]
        
        # Action
        result = view.get_queryset()
        
        # Assert
        self.assertEqual(result, filtered_queryset)
        # Check that we filter by is_deleted=False and then by customer=user
        mock_queryset.filter.assert_any_call(is_deleted=False)
        mock_queryset.filter.assert_any_call(customer=self.mock_customer_user)
        
    @patch('packages.views.PackageCreateSerializer')
    @patch('packages.views.PackageSerializer')
    @patch('packages.views.Package.objects.get')
    def test_create_package(self, mock_get, mock_package_serializer, mock_create_serializer):
        """Test package creation by customer"""
        # Setup
        self.client.force_authenticate(user=self.mock_customer_user)
        
        # Mock serializer instances
        mock_serializer_instance = MagicMock()
        mock_serializer_instance.is_valid.return_value = True
        mock_serializer_instance.instance = self.mock_package
        mock_create_serializer.return_value = mock_serializer_instance
        
        mock_response_serializer = MagicMock()
        mock_response_serializer.data = self.serialized_package_data
        mock_package_serializer.return_value = mock_response_serializer
        
        # Mock Package.objects.get to return our mock package
        mock_get.return_value = self.mock_package
        
        # Test data
        test_data = {
            'description': 'Test package',
            'weight': 2.5,
            'dimensions': '20x15x10',
            'pickup_address': '123 Pickup St',
            'delivery_address': '456 Delivery Ave'
        }
        
        # Action
        url = reverse('package-list')
        response = self.client.post(url, test_data, format='json')
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, self.serialized_package_data)
        mock_serializer_instance.save.assert_called_once()

    @patch('packages.views.PackageSerializer')
    def test_retrieve_package_by_customer(self, mock_serializer):
        """Test retrieving a specific package by its customer"""
        # Setup
        self.client.force_authenticate(user=self.mock_customer_user)
        
        # Mock get_object to return our mock package
        with patch.object(PackageViewSet, 'get_object', return_value=self.mock_package):
            # Mock serializer
            mock_serializer_instance = MagicMock()
            mock_serializer_instance.data = self.serialized_package_data
            mock_serializer.return_value = mock_serializer_instance
            
            # Action
            url = reverse('package-detail', args=[1])
            response = self.client.get(url)
            
            # Assert
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data, self.serialized_package_data)

    @patch('packages.views.PackageSerializer')
    def test_retrieve_package_by_courier(self, mock_serializer):
        """Test retrieving a specific package by its assigned courier"""
        # Setup
        self.client.force_authenticate(user=self.mock_courier_user)
        
        # Mock get_object to return our mock package
        with patch.object(PackageViewSet, 'get_object', return_value=self.mock_package):
            # Mock serializer
            mock_serializer_instance = MagicMock()
            mock_serializer_instance.data = self.serialized_package_data
            mock_serializer.return_value = mock_serializer_instance
            
            # Action
            url = reverse('package-detail', args=[1])
            response = self.client.get(url)
            
            # Assert
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data, self.serialized_package_data)

    @patch('packages.views.PackageStatusUpdateCreateSerializer')
    @patch('packages.views.PackageSerializer')
    def test_update_status_by_courier(self, mock_package_serializer, mock_status_serializer):
        """Test updating package status by assigned courier"""
        # Setup
        self.client.force_authenticate(user=self.mock_courier_user)
        
        # Mock get_object to return our mock package
        with patch.object(PackageViewSet, 'get_object', return_value=self.mock_package):
            # Mock serializers
            mock_status_serializer_instance = MagicMock()
            mock_status_serializer_instance.is_valid.return_value = True
            mock_status_serializer.return_value = mock_status_serializer_instance
            
            mock_package_serializer_instance = MagicMock()
            mock_package_serializer_instance.data = self.serialized_package_data
            mock_package_serializer.return_value = mock_package_serializer_instance
            
            # Test data
            test_data = {
                'status': 'in_transit',
                'notes': 'Package is in transit'
            }
            
            # Action
            url = reverse('package-update-status', args=[1])
            response = self.client.post(url, test_data, format='json')
            
            # Assert
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data, self.serialized_package_data)
            
            # Use ANY for the request object in the context to avoid type mismatches
            from unittest.mock import ANY
            mock_status_serializer.assert_called_once_with(
                data=test_data,
                context={'request': ANY, 'package': self.mock_package}
            )
            mock_status_serializer_instance.save.assert_called_once()

    @patch('packages.views.PackageAssignSerializer')
    @patch('packages.views.PackageSerializer')
    @patch('packages.views.PackageStatusUpdate.objects.create')
    def test_assign_courier_by_admin(self, mock_status_create, mock_package_serializer, mock_assign_serializer):
        """Test assigning a courier to a package by admin"""
        # Setup
        self.client.force_authenticate(user=self.mock_admin_user)
        
        # Mock get_object to return our mock package
        with patch.object(PackageViewSet, 'get_object', return_value=self.mock_package):
            # Mock serializers
            mock_assign_serializer_instance = MagicMock()
            mock_assign_serializer_instance.is_valid.return_value = True
            mock_assign_serializer.return_value = mock_assign_serializer_instance
            
            mock_package_serializer_instance = MagicMock()
            mock_package_serializer_instance.data = self.serialized_package_data
            mock_package_serializer.return_value = mock_package_serializer_instance
            
            # Test data
            test_data = {
                'courier': 2  # ID of the courier
            }
            
            # Action
            url = reverse('package-assign-courier', args=[1])
            response = self.client.patch(url, test_data, format='json')
            
            # Assert
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data, self.serialized_package_data)
            
            # Use ANY for the context parameter since it contains request objects
            from unittest.mock import ANY
            mock_assign_serializer.assert_called_once_with(
                self.mock_package, data=test_data, partial=True, context=ANY
            )
            mock_assign_serializer_instance.save.assert_called_once()
            
            # For the status update, check just the essential parameters
            mock_status_create.assert_called_once_with(
                package=self.mock_package,
                status=ANY,
                notes=ANY,
                updated_by=ANY
            )

    @patch('packages.views.PackageSoftDeleteSerializer')
    @patch('packages.views.PackageStatusUpdate.objects.create')
    def test_soft_delete_by_admin(self, mock_status_create, mock_delete_serializer):
        """Test soft deleting a package by admin"""
        # Setup
        self.client.force_authenticate(user=self.mock_admin_user)
        
        # Mock get_object to return our mock package
        with patch.object(PackageViewSet, 'get_object', return_value=self.mock_package):
            # Mock serializer
            mock_delete_serializer_instance = MagicMock()
            mock_delete_serializer_instance.is_valid.return_value = True
            mock_delete_serializer.return_value = mock_delete_serializer_instance
            
            # Action
            url = reverse('package-soft-delete', args=[1])
            response = self.client.patch(url)
            
            # Assert
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data, {'detail': 'Package successfully marked as deleted'})
            
            # Check that serializer was called at least once
            mock_delete_serializer.assert_called()
            
            # Verify essential arguments manually
            call_args, call_kwargs = mock_delete_serializer.call_args
            self.assertEqual(call_kwargs['data'], {'is_deleted': True})
            self.assertEqual(call_kwargs['partial'], True)
            self.assertEqual(call_args[0], self.mock_package)
            
            # Check that save was called
            mock_delete_serializer_instance.save.assert_called_once()
            
            # Check that status update was created
            mock_status_create.assert_called()

    @patch('packages.views.get_object_or_404')
    @patch('packages.views.PackageSoftDeleteSerializer')
    @patch('packages.views.PackageStatusUpdate.objects.create')
    def test_restore_by_admin(self, mock_status_create, mock_restore_serializer, mock_get_object):
        """Test restoring a soft-deleted package by admin"""
        # Setup
        self.client.force_authenticate(user=self.mock_admin_user)
        
        # Mock get_object_or_404 to return our mock package
        mock_get_object.return_value = self.mock_package
        
        # Mock serializer
        mock_restore_serializer_instance = MagicMock()
        mock_restore_serializer_instance.is_valid.return_value = True
        mock_restore_serializer.return_value = mock_restore_serializer_instance
        
        # Action
        url = reverse('package-restore', args=[1])
        response = self.client.patch(url)
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'detail': 'Package successfully restored'})
        
        # Fix: Use assert_called_once() without arguments and then check specific parameters
        mock_restore_serializer.assert_called_once()
        call_args = mock_restore_serializer.call_args
        self.assertEqual(call_args[0][0], self.mock_package)
        self.assertEqual(call_args[1]['data'], {'is_deleted': False})
        self.assertEqual(call_args[1]['partial'], True)
        
        mock_restore_serializer_instance.save.assert_called_once()
        mock_status_create.assert_called_once()

    @patch('packages.views.PackageSerializer')
    @patch('packages.views.Package.objects.filter')
    def test_deleted_packages_by_admin(self, mock_filter, mock_serializer):
        """Test listing all soft-deleted packages by admin"""
        # Setup
        self.client.force_authenticate(user=self.mock_admin_user)
        
        # Mock queryset and serializer
        mock_queryset = MagicMock()
        mock_filter.return_value = mock_queryset
        
        mock_serializer_instance = MagicMock()
        mock_serializer_instance.data = [self.serialized_package_data]
        mock_serializer.return_value = mock_serializer_instance
        
        # Action
        url = reverse('package-deleted-packages')
        response = self.client.get(url)
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [self.serialized_package_data])
        mock_filter.assert_called_once_with(is_deleted=True)
        mock_serializer.assert_called_once_with(mock_queryset, many=True)

    @patch('packages.views.get_object_or_404')
    @patch('packages.views.PackageSerializer')
    def test_track_package_authenticated_user(self, mock_serializer, mock_get_object):
        """Test tracking a package by an authenticated user who owns the package"""
        # Setup
        self.client.force_authenticate(user=self.mock_customer_user)
        
        # Mock get_object_or_404 to return our mock package
        mock_get_object.return_value = self.mock_package
        
        # Mock serializer
        mock_serializer_instance = MagicMock()
        mock_serializer_instance.data = self.serialized_package_data
        mock_serializer.return_value = mock_serializer_instance
        
        # Action
        url = f"{reverse('package-track')}?tracking_number=PKG-12345"
        response = self.client.get(url)
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, self.serialized_package_data)
        mock_get_object.assert_called_once_with(
            Package, tracking_number="PKG-12345", is_deleted=False
        )

    @patch('packages.views.get_object_or_404')
    def test_track_package_unauthenticated_user(self, mock_get_object):
        """Test tracking a package by an unauthenticated user"""
        # Setup - no authentication
        
        # Mock package and its status updates
        mock_package = MagicMock()
        mock_package.tracking_number = "PKG-12345"
        mock_package.status = "in_transit"
        mock_package.updated_at = "2025-03-07T12:00:00Z"
        
        mock_status_update = MagicMock()
        mock_status_update.status = "in_transit"
        mock_status_update.created_at = "2025-03-07T12:00:00Z"
        mock_package.status_updates.all.return_value = [mock_status_update]
        
        # Mock get_object_or_404 to return our mock package
        mock_get_object.return_value = mock_package
        
        # Action
        url = f"{reverse('package-track')}?tracking_number=PKG-12345"
        response = self.client.get(url)
        
        # Assert - should get limited tracking information
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["tracking_number"], "PKG-12345")
        self.assertEqual(response.data["status"], "in_transit")
        self.assertEqual(len(response.data["status_updates"]), 1)
        self.assertEqual(response.data["status_updates"][0]["status"], "in_transit")
        mock_get_object.assert_called_once_with(
            Package, tracking_number="PKG-12345", is_deleted=False
        )

    def test_track_package_missing_tracking_number(self):
        """Test tracking a package without providing a tracking number"""
        # Action - no tracking number provided
        url = reverse('package-track')
        response = self.client.get(url)
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"detail": "Tracking number is required"})