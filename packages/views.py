from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q

from .models import Package, PackageStatusUpdate
from .serializers import (
    PackageSerializer, PackageCreateSerializer, 
    PackageStatusUpdateSerializer, PackageStatusUpdateCreateSerializer,
    PackageAssignSerializer, PackageSoftDeleteSerializer
)
from accounts.permissions import IsCustomer, IsCourier, IsAdmin, IsOwnerOrStaff

class PackageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Package model that handles different user roles and permissions
    """
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['tracking_number', 'status', 'description']
    ordering_fields = ['created_at', 'updated_at', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Filter packages based on user role:
        - Customers see only their packages
        - Couriers see only packages assigned to them
        - Admins see all packages
        """
        user = self.request.user
        queryset = super().get_queryset()
        
        # By default, don't show soft-deleted packages except in specific actions
        if self.action != 'deleted_packages':
            queryset = queryset.filter(is_deleted=False)
        
        if user.is_customer:
            return queryset.filter(customer=user)
        elif user.is_courier:
            return queryset.filter(courier=user)
        elif user.is_admin:
            return queryset
        return Package.objects.none()
    
    def get_permissions(self):
        """
        Set up permissions based on action:
        - create: only customers
        - update_status: courier staff or admin
        - assign_courier, soft_delete, restore: admin only
        - list, retrieve: owner or staff
        """
        if self.action == 'create':
            permission_classes = [IsCustomer]
        elif self.action == 'update_status':
            permission_classes = [IsCourier | IsAdmin]
        elif self.action in ['assign_courier', 'soft_delete', 'restore', 'deleted_packages']:
            permission_classes = [IsAdmin]
        else:
            permission_classes = [IsOwnerOrStaff]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        """Return appropriate serializer class based on action"""
        if self.action == 'create':
            return PackageCreateSerializer
        elif self.action == 'update_status':
            return PackageStatusUpdateCreateSerializer
        elif self.action == 'assign_courier':
            return PackageAssignSerializer
        elif self.action in ['soft_delete', 'restore']:
            return PackageSoftDeleteSerializer
        return PackageSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new package for the current user"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Fetch the complete package with proper serializer
        package = Package.objects.get(pk=serializer.instance.pk)
        response_serializer = PackageSerializer(package)
        
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def perform_create(self, serializer):
        """Save the package with customer set to current user"""
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update package status and create status update record"""
        package = self.get_object()
        
        # Courier can only update assigned packages
        if request.user.is_courier and package.courier != request.user:
            return Response(
                {"detail": "You can only update status for packages assigned to you."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(
            data=request.data,
            context={'request': request, 'package': package}
        )
        serializer.is_valid(raise_exception=True)
        status_update = serializer.save()
        
        # Return the updated package
        package_serializer = PackageSerializer(package)
        return Response(package_serializer.data)
    
    @action(detail=True, methods=['patch'])
    def assign_courier(self, request, pk=None):
        """Assign a courier to the package (admin only)"""
        package = self.get_object()
        serializer = self.get_serializer(package, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Create a status update record
        PackageStatusUpdate.objects.create(
            package=package,
            status=package.status,
            notes=f"Package assigned to courier: {package.courier.email}",
            updated_by=request.user
        )
        
        # Return the updated package
        package_serializer = PackageSerializer(package)
        return Response(package_serializer.data)
    
    @action(detail=True, methods=['patch'])
    def soft_delete(self, request, pk=None):
        """Soft delete a package (admin only)"""
        package = self.get_object()
        serializer = self.get_serializer(package, data={'is_deleted': True}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Create a status update record
        PackageStatusUpdate.objects.create(
            package=package,
            status=package.status,
            notes=f"Package marked as deleted by admin",
            updated_by=request.user
        )
        
        return Response({"detail": "Package successfully marked as deleted"})
    
    @action(detail=True, methods=['patch'])
    def restore(self, request, pk=None):
        """Restore a soft-deleted package (admin only)"""
        # Override queryset to include deleted packages
        package = get_object_or_404(Package, pk=pk)
        serializer = self.get_serializer(package, data={'is_deleted': False}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Create a status update record
        PackageStatusUpdate.objects.create(
            package=package,
            status=package.status,
            notes=f"Package restored by admin",
            updated_by=request.user
        )
        
        return Response({"detail": "Package successfully restored"})
    
    @action(detail=False, methods=['get'])
    def deleted_packages(self, request):
        """List all soft-deleted packages (admin only)"""
        queryset = Package.objects.filter(is_deleted=True)
        serializer = PackageSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def track(self, request):
        """Track a package by tracking number (publicly accessible)"""
        tracking_number = request.query_params.get('tracking_number', None)
        if not tracking_number:
            return Response(
                {"detail": "Tracking number is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        package = get_object_or_404(Package, tracking_number=tracking_number, is_deleted=False)
        
        # For security, return limited information for non-authenticated users
        # or users who are not the package owner/courier/admin
        if (not request.user.is_authenticated or 
            (request.user != package.customer and 
             request.user != package.courier and 
             not request.user.is_admin)):
            # Return limited tracking information
            return Response({
                "tracking_number": package.tracking_number,
                "status": package.status,
                "updated_at": package.updated_at,
                "status_updates": [
                    {
                        "status": update.status,
                        "created_at": update.created_at
                    } for update in package.status_updates.all()
                ]
            })
        
        serializer = PackageSerializer(package)
        return Response(serializer.data)


class PackageStatusUpdateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing package status updates
    """
    serializer_class = PackageStatusUpdateSerializer
    
    def get_queryset(self):
        """
        Filter status updates based on user role and package
        """
        package_id = self.kwargs.get('package_pk')
        user = self.request.user
        
        if not package_id:
            return PackageStatusUpdate.objects.none()
        
        try:
            package = Package.objects.get(pk=package_id)
        except Package.DoesNotExist:
            return PackageStatusUpdate.objects.none()
        
        # Check if user has permission to view package status updates
        if user.is_admin:
            return package.status_updates.all()
        elif user.is_courier and package.courier == user:
            return package.status_updates.all()
        elif user.is_customer and package.customer == user:
            return package.status_updates.all()
        
        return PackageStatusUpdate.objects.none()
