from django.contrib import admin
from .models import Package, PackageStatusUpdate

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ('tracking_number', 'customer', 'courier', 'status', 'created_at', 'is_deleted')
    list_filter = ('status', 'is_deleted')
    search_fields = ('tracking_number', 'customer__email', 'courier__email', 'description')
    readonly_fields = ('tracking_number', 'created_at', 'updated_at', 'deleted_at')

@admin.register(PackageStatusUpdate)
class PackageStatusUpdateAdmin(admin.ModelAdmin):
    list_display = ('package', 'status', 'updated_by', 'created_at')
    list_filter = ('status',)
    search_fields = ('package__tracking_number', 'notes')
    readonly_fields = ('created_at',)
