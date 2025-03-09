from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from .views import PackageViewSet, PackageStatusUpdateViewSet

# Main router for packages
router = DefaultRouter()
router.register(r'', PackageViewSet, basename='package')

# Nested router for status updates
status_router = routers.NestedSimpleRouter(router, r'', lookup='package')
status_router.register(r'status', PackageStatusUpdateViewSet, basename='package-status')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(status_router.urls)),
]