# actionunit/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import *

@admin.register(Church)
class ChurchAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'district', 'country', 'created_at')
    list_filter = ('district', 'country', 'denomination', 'created_at')
    search_fields = ('name', 'email', 'district')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Church Information', {
            'fields': ('name', 'email', 'phone', 'denomination')
        }),
        ('Location', {
            'fields': ('address', 'district', 'country')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('name', 'email', 'role', 'church', 'is_active', 'date_joined', 'is_officer')
    list_filter = ('role', 'church', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('name', 'email', 'church__name')
    ordering = ('name',)
    
    # Fields for editing users
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Personal Info', {
            'fields': ('name', 'email', 'phone', 'church', 'role')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions', 'is_officer')
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    # Fields for creating users
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'name', 'email', 'phone', 'church', 'role', 'password1', 'password2'),
        }),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('church', 'plan', 'status', 'trial_end_date', 'current_period_end')
    list_filter = ('plan', 'status', 'trial_end_date', 'current_period_end')
    search_fields = ('church__name',)
    ordering = ('church__name',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Subscription Details', {
            'fields': ('church', 'plan', 'status')
        }),
        ('Dates', {
            'fields': ('trial_end_date', 'current_period_end', 'grace_period_end')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    

# actionunit/class management
@admin.register(ActionUnitClass)
class ActionUnitClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'church', 'location', 'meeting_time', 'is_active', 'created_at')
    list_filter = ('church', 'is_active', 'created_at')
    search_fields = ('name', 'church__name', 'location')
    ordering = ('church__name', 'name')
    
    fieldsets = (
        ('Class Information', {
            'fields': ('church', 'name', 'location', 'meeting_time', 'description')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

 
@admin.register(ClassTeacher)
class ClassTeacherAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'action_unit_class', 'assigned_date', 'is_active')
    list_filter = ('is_active', 'assigned_date')
    search_fields = ('teacher__name', 'action_unit_class__name')
    ordering = ('action_unit_class__church__name', 'action_unit_class__name')


@admin.register(ClassMember)
class ClassMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'action_unit_class', 'joined_date', 'is_active')
    list_filter = ('is_active', 'joined_date', 'action_unit_class__church')
    search_fields = ('user__name', 'action_unit_class__name')
    ordering = ('action_unit_class__name', 'user__name')



@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['class_member', 'date', 'is_present', 'absence_reason', 'marked_by']
    list_filter = ['date', 'is_present', 'absence_reason', 'marked_by']
    search_fields = ['class_member__user__name', 'marked_by__name']
    date_hierarchy = 'date'



@admin.register(Offering)
class OfferingAdmin(admin.ModelAdmin):
    list_display = ['action_unit_class', 'amount', 'currency', 'date', 'recorded_by']
    list_filter = ['currency', 'date', 'action_unit_class__church']
    search_fields = ['action_unit_class__name', 'recorded_by__name', 'notes']
    date_hierarchy = 'date'
    


# admin.py
@admin.register(QuarterlyBook)
class QuarterlyBookAdmin(admin.ModelAdmin):
    list_display = ['title', 'church', 'price', 'currency', 'is_active', 'created_at']
    list_filter = ['church', 'is_active', 'currency', 'created_at']
    search_fields = ['title']
    list_editable = ['is_active']
    



# admin.py
@admin.register(BookOrder)
class BookOrderAdmin(admin.ModelAdmin):
    list_display = ['action_unit_class', 'quarter', 'year', 'total_amount', 'status', 'submitted_date']
    list_filter = ['status', 'quarter', 'year', 'action_unit_class__church']
    search_fields = ['action_unit_class__name', 'submitted_by__name']
    date_hierarchy = 'submitted_date'

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['book_order', 'quarterly_book', 'quantity', 'unit_price', 'total_price']
    list_filter = ['book_order__quarter', 'book_order__year']
    search_fields = ['quarterly_book__title', 'book_order__action_unit_class__name']
    
    
    
