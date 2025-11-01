# urls.py (project-level)
"""
Main URL configuration for ActionUnitManager Django project.

Includes:
- Admin interface URLs
- API authentication routes
- REST framework authentication endpoints
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenVerifyView

urlpatterns = [
    # Django admin interface
    path('admin/', admin.site.urls),
    
    # API routes
    path('api/', include('actionunit.urls')),  # Replace 'yourapp' with your actual app name
    
    # JWT token verification
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]