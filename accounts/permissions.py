from rest_framework import permissions

class IsCustomer(permissions.BasePermission):
    """
    Allow access only to customer users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_customer

class IsCourier(permissions.BasePermission):
    """
    Allow access only to courier staff users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_courier

class IsAdmin(permissions.BasePermission):
    """
    Allow access only to admin users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin

class IsOwnerOrStaff(permissions.BasePermission):
    """
    Custom permission to only allow owners of a package to view or edit it,
    or allow staff (couriers and admins) with appropriate permissions.
    """
    def has_object_permission(self, request, view, obj):
        # Check if the user is the owner of the package
        if hasattr(obj, 'customer'):
            is_owner = obj.customer == request.user
        else:
            is_owner = False
            
        # Allow admin to do anything
        if request.user.is_admin:
            return True
            
        # Allow courier to view and update status of assigned packages
        if request.user.is_courier and hasattr(obj, 'courier'):
            is_assigned = obj.courier == request.user
            if is_assigned:
                if request.method in permissions.SAFE_METHODS:
                    return True  # Allow couriers to GET their assigned packages
                elif request.method in ['PUT', 'PATCH']:
                    return True  # Allow couriers to update their assigned packages
                
        # Allow customers to view their own packages
        if request.user.is_customer and is_owner:
            return request.method in permissions.SAFE_METHODS
            
        return False