# urls.py (app-level)
"""
URL routes for ActionUnitManager authentication API.

Defines endpoints for:
- Church registration and user authentication
- Token management and refresh
- User profile retrieval
"""

from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

app_name = 'authentication'

urlpatterns = [
    # Church registration - frontend expects: /api/church/register/
    path('church/register/', views.church_signup, name='church-register'),

    # Authentication endpoints
    path('auth/superintendent-login/', views.superintendent_login, name='superintendent-login'),
    path('auth/teacher-member-login/', views.teacher_member_simple_login, name='teacher-member-login'),
    
    # general login - frontend expects: /api/auth/login/
    path('auth/login/', views.user_login, name='user-login'),
    
    
    
    
    # Token refresh - frontend expects: /api/auth/token/refresh/
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    # Current user - frontend might expect: /api/auth/me/ or /api/church/profile/
    path('auth/me/', views.get_current_user, name='current-user'),
    path('church/profile/', views.get_current_user, name='church-profile'),
    
     # Classes management endpoints
    path('classes/', views.classes_list_create, name='classes-list-create'),
    path('classes/<int:class_id>/', views.class_detail, name='class-detail'),
    path('classes/assign-teacher/', views.assign_teacher, name='assign-teacher'),
    
    
    # Members management endpoints
    path('members-classes/', views.class_members_list_create, name='class-members-list'),
    path('members/<int:class_id>/classes/', views.class_members_list_create, name='class-members-by-class'),
    path('members-classes/<int:member_id>/', views.class_member_detail, name='class-member-detail'),
    path('members-bulk-import/', views.bulk_import_members, name='bulk-import-members'),
    
    
    
    # Teacher management endpoints
    path('teachers/', views.teachers_list_create, name='teachers-list-create'),
    path('teachers/<int:teacher_id>/', views.teacher_detail, name='teacher-detail'),
    path('teacher-classes/', views.teacher_classes_list, name='teacher-classes-list'),
    path('teachers-assign-to-class/', views.assign_teacher_to_class, name='assign-teacher-to-class'),
    path('teachers-reassign/', views.reassign_teacher, name='reassign-teacher'),
    
    
    #attendance endpoints
    path('attendance/', views.mark_attendance, name='mark-attendance'),
    path('teacher/dashboard/', views.teacher_dashboard_info, name='teacher-dashboard-info'),
    
    
    
    # offerings endpoint
    path('offerings/', views.offerings_list_create, name='offerings-list-create'),
    path('classes/<int:class_id>/offerings/', views.offerings_list_create, name='class-offerings'),
    
    
    #absent members
    path('reports/absent-members/', views.absent_members_report, name='absent-members-report'),
    path('classes/<int:class_id>/absent-members/', views.absent_members_report, name='class-absent-members'),
    
    
    # sabbath school books manage
    path('quarterly-books/', views.quarterly_books_list_create, name='quarterly-books-list-create'),
    path('quarterly-books/<int:book_id>/', views.quarterly_book_detail, name='quarterly-book-detail'),
        
        
    # sabbath school quarterlies oder submit
    path('book-orders/', views.book_orders_list_create, name='book-orders-list-create'),
    path('book-orders/<int:order_id>/', views.book_order_detail, name='book-order-detail'),
    path('book-orders/<int:order_id>/submit/', views.submit_book_order, name='submit-book-order'),
    path('quarterly-books/active/', views.active_quarterly_books, name='active-quarterly-books'),
    # superintendent dashboard view
    path('superintendent/book-orders/', views.superintendent_book_orders, name='superintendent-book-orders'),
    path('superintendent/orders-quarters/', views.superintendent_orders_quarters, name='superintendent-orders-quarters'),
    path('superintendent/dashboard-metrics/', views.superintendent_dashboard_metrics, name='superintendent-dashboard-metrics'),
    
    
    #report
    path('reports/attendance/', views.attendance_reports, name='attendance-reports'),
    path('reports/offerings/', views.offerings_reports, name='offerings-reports'),
    path('reports/books/', views.books_reports, name='books-reports'),
    path('officers/at-risk-members/', views.at_risk_members_analysis, name='at-risk-members'),
    path('officers/', views.officers_management, name='officers-management'),
    path('officers/<int:officer_id>/', views.officer_detail, name='officer-detail'),
    
    
    
    
    # subscripyion
    path('subscription/status/', views.subscription_status, name='subscription-status'),
    path('subscription/create/', views.create_subscription, name='create-subscription'),
    path('subscription/initiate-payment/', views.initiate_payment, name='initiate-payment'),
    path('subscription/verify-payment/', views.verify_payment, name='verify-payment'),
    ]