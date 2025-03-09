from rest_framework import serializers
from .models import Package, PackageStatusUpdate
from django.utils import timezone

class PackageStatusUpdateSerializer(serializers.ModelSerializer):
    updated_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PackageStatusUpdate
        fields = ['id', 'status', 'notes', 'updated_by', 'updated_by_name', 'created_at']
        read_only_fields = ['id', 'updated_by', 'updated_by_name', 'created_at']
    
    def get_updated_by_name(self, obj):
        if obj.updated_by:
            return f"{obj.updated_by.first_name} {obj.updated_by.last_name}"
        return None

class PackageSerializer(serializers.ModelSerializer):
    status_updates = PackageStatusUpdateSerializer(many=True, read_only=True)
    customer_email = serializers.SerializerMethodField()
    courier_email = serializers.SerializerMethodField()
    
    class Meta:
        model = Package
        fields = [
            'id', 'tracking_number', 'customer', 'customer_email', 'courier', 
            'courier_email', 'description', 'weight', 'dimensions', 
            'pickup_address', 'delivery_address', 'status', 
            'created_at', 'updated_at', 'is_deleted', 'status_updates'
        ]
        read_only_fields = ['id', 'tracking_number', 'created_at', 'updated_at', 'is_deleted', 'deleted_at']
    
    def get_customer_email(self, obj):
        return obj.customer.email if obj.customer else None
    
    def get_courier_email(self, obj):
        return obj.courier.email if obj.courier else None

class PackageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = [
            'description', 'weight', 'dimensions', 
            'pickup_address', 'delivery_address'
        ]
    
    def create(self, validated_data):
        # Set the customer as the current user
        validated_data['customer'] = self.context['request'].user
        return super().create(validated_data)

class PackageStatusUpdateCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackageStatusUpdate
        fields = ['status', 'notes']
    
    def create(self, validated_data):
        package = self.context['package']
        user = self.context['request'].user
        
        # Update the package status
        package.status = validated_data['status']
        package.save()
        
        # Create the status update record
        status_update = PackageStatusUpdate.objects.create(
            package=package,
            status=validated_data['status'],
            notes=validated_data.get('notes', ''),
            updated_by=user
        )
        
        return status_update

class PackageAssignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = ['courier']

class PackageSoftDeleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = ['is_deleted']
        
    def update(self, instance, validated_data):
        if validated_data.get('is_deleted'):
            instance.is_deleted = True
            instance.deleted_at = timezone.now()
        else:
            instance.is_deleted = False
            instance.deleted_at = None
        
        instance.save()
        return instance