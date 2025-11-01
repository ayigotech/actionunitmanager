# models.py
from django.db import models
from django.db.models import Sum
from django.contrib.auth.models import AbstractUser
from django.forms import ValidationError



class Church(models.Model):
    """
    Represents a church organization using the ActionUnitManager system.
    
    Attributes:
        name (str): The official name of the church
        email (str): Primary contact email (unique)
        phone (str): Contact phone number
        address (str): Physical location address
        district (str): Administrative district within the country
        country (str): Country where church is located (default: Ghana)
        denomination (str): Religious denomination (default: Seventh-day Adventist)
        created_at (datetime): Auto-set when church is registered
        updated_at (datetime): Auto-updated on every save
    """
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, default='Ghana')
    denomination = models.CharField(max_length=100, default='Seventh-day Adventist')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Church"
        verbose_name_plural = "Churches"
        db_table = "churches"



# actionunit/models.py - UPDATE CustomUser model
class CustomUser(AbstractUser):
    """
    Custom user model for ActionUnitManager system users.
    Extends Django's AbstractUser with church-specific fields.
    Attributes:
        church (ForeignKey): The church this user belongs to
        role (str): User role - superintendent, teacher, or member
        phone (str): User's contact phone number
        name (str): User's full name (replaces first_name/last_name).
    """
    ROLE_CHOICES = (
        ('superintendent', 'Superintendent'),
        ('teacher', 'Teacher'),
        ('member', 'Member'),
        ('system_admin', 'System Administrator'),
    )
    
    church = models.ForeignKey(Church, on_delete=models.CASCADE, related_name='users', null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='system_admin')
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_officer = models.BooleanField(default=False)
    
    first_name = None
    last_name = None
    name = models.CharField(max_length=255)

    def __str__(self):
        if self.church:
            return f"{self.name} ({self.role}) - {self.church.name}"
        return f"{self.name} ({self.role}) - System Admin"


    # CustomUser save method
    def save(self, *args, **kwargs):
        # Auto-set role for superusers
        if self.is_superuser and not self.role:
            self.role = 'system_admin'
        
        # Validate required fields based on role
        if self.role in ['superintendent', 'teacher', 'member'] and not self.church:
            raise ValidationError(f"{self.get_role_display()} must belong to a church.")
            
        if self.role in ['teacher', 'member'] and not self.phone:
            raise ValidationError(f"{self.get_role_display()} must have a phone number.")
        
        # Check if this is a new teacher/member or password needs reset
        is_new_teacher_member = (self.role in ['teacher', 'member'] and 
                            (self._state.adding or not self.password))
        
        # Call parent save first
        super().save(*args, **kwargs)
    
        # Reset password for teachers/members if needed
        if is_new_teacher_member:
            self.set_password(self.get_default_password())
            self.save(update_fields=['password'])
    
    
    def get_default_password(self):
        """Generate default password based on phone number"""
        # Use last 6 digits of phone as default password
        if self.phone:
            # Remove any non-digit characters and get last 6 digits
            digits = ''.join(filter(str.isdigit, self.phone))
            return digits[-6:]  # Last 6 digits
        return "123456"  # Fallback default
    
    def delete(self, *args, **kwargs):
        if self.role == 'superintendent':
            other_superintendents = CustomUser.objects.filter(
                church=self.church,
                role='superintendent',
                is_active=True
            ).exclude(id=self.id)
            
            if not other_superintendents.exists():
                raise ValidationError("Cannot delete the last superintendent.")
        
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        db_table = "users"



class Subscription(models.Model):
    
    """
    Manages subscription plans and status for churches.
    
    Each church has exactly one subscription defining their access level.
    
    Attributes:
        church (OneToOneField): The church this subscription belongs to
        plan (str): Subscription plan - free_trial, monthly, or annual
        status (str): Current subscription status (trialing, active, etc.)
        trial_end_date (date): When the free trial period ends
        current_period_end (date): When the current billing period ends
        grace_period_end (date): Optional grace period after subscription ends
        created_at (datetime): When subscription was created
        updated_at (datetime): Last time subscription was updated
    """
    PLAN_CHOICES = (
        ('free_trial', 'Free Trial'),
        ('monthly', 'Monthly'),
        ('quarterly',' Quarterly'),
        ('annual', 'Annual'),
    )
    
    STATUS_CHOICES = (
        ('trialing', 'Trialing'),
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('canceled', 'Canceled'),
        ('unpaid', 'Unpaid'),
    )
    
    church = models.OneToOneField(Church, on_delete=models.CASCADE, related_name='subscription')
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='free_trial')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trialing')
    trial_end_date = models.DateField()
    current_period_end = models.DateField()
    grace_period_end = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.church.name} - {self.get_plan_display()}"

    class Meta:
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"
        db_table = "subscriptions"



# actionunit/class management
class ActionUnitClass(models.Model):
    """
    Represents an Action Unit (Sabbath School Class) in a church.
    """
    church = models.ForeignKey(Church, on_delete=models.CASCADE, related_name='classes')
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200, blank=True, null=True)
    meeting_time = models.TimeField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.church.name}"

    class Meta:
        verbose_name = "Action Unit Class"
        verbose_name_plural = "Action Unit Classes"
        db_table = "action_unit_classes"
        unique_together = ['church', 'name']



class ClassTeacher(models.Model):
    """
    Represents a teacher assigned to an Action Unit class.
    """
    action_unit_class = models.ForeignKey(ActionUnitClass, on_delete=models.CASCADE, related_name='teacher_assignments')
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='teaching_assignments')
    assigned_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.teacher.name} - {self.action_unit_class.name}"

    class Meta:
        verbose_name = "Class Teacher"
        verbose_name_plural = "Class Teachers"
        db_table = "class_teachers"
        unique_together = ['action_unit_class', 'teacher']  # Prevent duplicate assignments



class ClassMember(models.Model):
    """
    Represents members belonging to an Action Unit class.
    """
    action_unit_class = models.ForeignKey(ActionUnitClass, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='class_memberships')
    location = models.CharField(max_length=200, blank=True, null=True)
    joined_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.name} - {self.action_unit_class.name}"

    class Meta:
        verbose_name = "Class Member"
        verbose_name_plural = "Class Members"
        db_table = "class_members"
        unique_together = ['action_unit_class', 'user']




#attendance reporting
class Attendance(models.Model):
    ABSENCE_REASONS = [
        ('sick', 'Sick'),
        ('traveling', 'Traveling'),
        ('work', 'Work'),
        ('family_emergency', 'Family Emergency'),
        ('unknown', 'Unknown'),
        ('other', 'Other'),
    ]
    
    class_member = models.ForeignKey(ClassMember, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    is_present = models.BooleanField(default=True)
    absence_reason = models.CharField(max_length=100, choices=ABSENCE_REASONS, blank=True, null=True)
    marked_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='marked_attendances')
    marked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Attendance"
        verbose_name_plural = "Attendances"
        db_table = "attendances"
        unique_together = ['class_member', 'date']

    def __str__(self):
        return f"{self.class_member.user.name} - {self.date} - {'Present' if self.is_present else 'Absent'}"





# models.py - Add Offering model
class Offering(models.Model):
    CURRENCY_CHOICES = [
        ('GHS', 'Ghana Cedi'),
        ('USD', 'US Dollar'),
    ]
    
    action_unit_class = models.ForeignKey(ActionUnitClass, on_delete=models.CASCADE, related_name='offerings')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='GHS')
    date = models.DateField()
    recorded_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='recorded_offerings')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Offering"
        verbose_name_plural = "Offerings"
        db_table = "offerings"
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.amount} {self.currency} - {self.action_unit_class.name} - {self.date}"



# sabbath school quarterly books
class QuarterlyBook(models.Model):
    CURRENCY_CHOICES = [
        ('GHS', 'Ghana Cedi'),
        ('USD', 'US Dollar'),
    ]
    
    church = models.ForeignKey(Church, on_delete=models.CASCADE, related_name='quarterly_books')
    title = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='GHS')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Quarterly Book"
        verbose_name_plural = "Quarterly Books"
        db_table = "quarterly_books"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.price} {self.currency}"


# quarterly orders
class BookOrder(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
    ]
    
    QUARTER_CHOICES = [
        ('Q1-Q2', 'Quarter 1 & 2 (Jan-Jun)'),
        ('Q3-Q4', 'Quarter 3 & 4 (Jul-Dec)'),
    ]
    
    action_unit_class = models.ForeignKey(ActionUnitClass, on_delete=models.CASCADE, related_name='book_orders')
    quarter = models.CharField(max_length=10, choices=QUARTER_CHOICES)
    year = models.IntegerField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    submitted_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='submitted_orders')
    submitted_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Book Order"
        verbose_name_plural = "Book Orders"
        db_table = "book_orders"
        unique_together = ['action_unit_class', 'quarter', 'year']
        ordering = ['-year', '-quarter', '-created_at']

    def __str__(self):
        return f"{self.action_unit_class.name} - {self.quarter} {self.year}"
    
    
    def update_total_amount(self):
        total = self.order_items.aggregate(total=Sum('total_price'))['total'] or 0
        self.total_amount = total
        self.save()



class OrderItem(models.Model):
    book_order = models.ForeignKey(BookOrder, on_delete=models.CASCADE, related_name='order_items')
    quarterly_book = models.ForeignKey(QuarterlyBook, on_delete=models.CASCADE, related_name='order_items')
    quantity = models.PositiveIntegerField(default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
        db_table = "order_items"
        unique_together = ['book_order', 'quarterly_book']

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quarterly_book.title} - {self.quantity} copies"


