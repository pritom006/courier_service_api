import uuid
from django.db import models
from django.conf import settings

class Package(models.Model):
    """
    Package model to represent a package in the courier service
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
    )
    
    tracking_number = models.CharField(max_length=50, unique=True, editable=False)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='packages'
    )
    courier = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        related_name='assigned_packages',
        null=True,
        blank=True
    )
    description = models.TextField()
    weight = models.DecimalField(max_digits=5, decimal_places=2, help_text="Weight in kg")
    dimensions = models.CharField(max_length=50, help_text="Format: LxWxH in cm")
    
    # Addresses
    pickup_address = models.TextField()
    delivery_address = models.TextField()
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Soft delete implementation
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Package {self.tracking_number} - {self.status}"
    
    def save(self, *args, **kwargs):
        if not self.tracking_number:
            self.tracking_number = self.generate_tracking_number()
        super().save(*args, **kwargs)
    
    def generate_tracking_number(self):
        """Generate a unique tracking number for the package"""
        return f"PKG-{uuid.uuid4().hex[:8].upper()}"


class PackageStatusUpdate(models.Model):
    """
    Model to keep track of all status updates for a package
    """
    package = models.ForeignKey(
        Package, 
        on_delete=models.CASCADE, 
        related_name='status_updates'
    )
    status = models.CharField(max_length=20, choices=Package.STATUS_CHOICES)
    notes = models.TextField(blank=True, null=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.package.tracking_number} - {self.status} - {self.created_at}"