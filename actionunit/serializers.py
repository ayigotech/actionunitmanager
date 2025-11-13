# serializers.py
from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import authenticate
from .models import (ActionUnitClass, Attendance, BookOrder, Church, ClassMember, ClassTeacher,
CustomUser, Offering, OrderItem, QuarterlyBook, Subscription )
from datetime import date, timedelta


class ChurchSerializer(serializers.ModelSerializer):
    """Serializer for Church model data representation."""
    
    class Meta:
        model = Church
        fields = ['id', 'name', 'email', 'phone', 'address', 'district', 'country', 'denomination']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model data representation."""
    
    class Meta:
        model = CustomUser
        fields = ['id', 'name', 'email', 'phone', 'role', 'church']



# serializers.py
class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id', 'name', 'phone', 'email', 'role', 
            'is_officer', 'is_active', 'date_joined', 'last_login'
        ]
        read_only_fields = ['date_joined', 'last_login']
        

class CustomUserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['phone', 'name', 'email', 'role', 'is_officer', 'church']
    
    def create(self, validated_data):
        validated_data['church'] = self.context['request'].user.church
        
        # Auto-generate username from phone
        validated_data['username'] = validated_data['phone']
        
        user = CustomUser.objects.create(**validated_data)
        return user


class ChurchSignupSerializer(serializers.Serializer):
    """
    Handles church registration with superintendent user creation.
    
    This serializer processes the nested structure of church and superintendent data
    during the initial registration process.
    
    Expected input format:
    {
        "church": {
            "name": "Church Name",
            "email": "church@example.com",
            ...
        },
        "superintendent": {
            "name": "Super Name", 
            "email": "super@example.com",
            ...
        }
    }
    """
    church = serializers.DictField()
    superintendent = serializers.DictField()
    
    def create(self, validated_data):
        """
        Creates Church, Superintendent User, and Free Trial Subscription.
        
        Args:
            validated_data (dict): Validated input data containing church and superintendent info
            
        Returns:
            dict: Dictionary containing created church, user, and subscription objects
            
        Raises:
            ValidationError: If church email already exists or data is invalid
        """
        church_data = validated_data['church']
        superintendent_data = validated_data['superintendent']
        
        # Check if church email already exists
        if Church.objects.filter(email=church_data['email']).exists():
            raise serializers.ValidationError({'church_email': 'A church with this email already exists.'})
        
        # Create Church
        church = Church.objects.create(**church_data)
        
        # Create Superintendent User
        user = CustomUser.objects.create_user(
            username=superintendent_data['email'],
            email=church_data['email'],
            password=superintendent_data['password'],
            name=superintendent_data['name'],
            phone=superintendent_data['phone'],
            role='superintendent',
            church=church
        )
        
        # Create Free Trial Subscription (30 days)
        trial_end = date.today() + timedelta(days=30)
        subscription = Subscription.objects.create(
            church=church,
            plan='free_trial',
            status='trialing',
            trial_end_date=trial_end,
            current_period_end=trial_end
        )
        
        return {
            'church': church,
            'user': user,
            'subscription': subscription
        }



#general login
class LoginSerializer(serializers.Serializer):
    """
    Handles user authentication for login requests.
    
    Validates email and password combination and returns authenticated user.
    """
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, data):
        """
        Validates user credentials and authenticates the user.
        
        Args:
            data (dict): Contains email and password for authentication
            
        Returns:
            dict: Original data with added 'user' key containing authenticated user
            
        Raises:
            ValidationError: If credentials are invalid or account is disabled
        """
        email = data.get('email')
        password = data.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if user:
                if user.is_active:
                    data['user'] = user
                else:
                    raise serializers.ValidationError('Account disabled.')
            else:
                raise serializers.ValidationError('Invalid credentials.')
        else:
            raise serializers.ValidationError('Must include email and password.')
        
        return data



# actionunit/SuperintendentLoginSerializer
class SuperintendentLoginSerializer(serializers.Serializer):
    """
    Login serializer for superintendents (email + password)
    """
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if email and password:
            try:
                # First, check if user exists and is a superintendent
                user = CustomUser.objects.get(email=email)
                
                if user.role != 'superintendent':
                    raise serializers.ValidationError('This email is not registered as a superintendent.')
                
                if not user.is_active:
                    raise serializers.ValidationError('Account is disabled. Please contact support.')
                
                # Then authenticate
                auth_user = authenticate(username=email, password=password)
                if auth_user:
                    data['user'] = auth_user
                else:
                    raise serializers.ValidationError('Invalid password.')
                    
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError('No superintendent found with this email address.')
                
        else:
            raise serializers.ValidationError('Must include email and password.')
        
        return data



#for teachers/classmembers
class TeacherMemberLoginSerializer(serializers.Serializer):
    """
    Login serializer for teachers and members (phone + password)
    """
    phone = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        phone = data.get('phone')
        password = data.get('password')

        if phone and password:
            # Teachers and members login with phone number
            try:
                # Find user by phone number
                user = CustomUser.objects.get(phone=phone, role__in=['teacher', 'member'])
                user = authenticate(username=user.username, password=password)
                if user:
                    if user.is_active:
                        data['user'] = user
                    else:
                        raise serializers.ValidationError('Account disabled.')
                else:
                    raise serializers.ValidationError('Invalid credentials.')
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError('No user found with this phone number.')
        else:
            raise serializers.ValidationError('Must include phone number and password.')
        
        return data



# actionunit/ActionUnitClassSerializer
class ActionUnitClassSerializer(serializers.ModelSerializer):
    """Serializer for Action Unit Class model"""
    teacher_name = serializers.SerializerMethodField()
    teacher_phone = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = ActionUnitClass
        fields = [
            'id', 'name', 'location', 'meeting_time', 'description', 
            'is_active', 'created_at', 'teacher_name', 'teacher_phone', 'member_count'
        ]

    def get_teacher_name(self, obj):
        """Get the assigned teacher's name"""
        # Use the plural related name 'teacher_assignments' for ForeignKey
        active_assignment = obj.teacher_assignments.filter(is_active=True).first()
        if active_assignment and active_assignment.teacher:
            return active_assignment.teacher.name
        return "Not Assigned"

    def get_teacher_phone(self, obj):
        """Get the assigned teacher's phone"""
        active_assignment = obj.teacher_assignments.filter(is_active=True).first()
        if active_assignment and active_assignment.teacher:
            return active_assignment.teacher.phone
        return None

    def get_member_count(self, obj):
        """Get the count of active members in the class"""
        return obj.members.filter(is_active=True).count()



class ActionUnitClassCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Action Unit Classes"""
    class Meta:
        model = ActionUnitClass
        fields = ['name', 'location', 'meeting_time', 'description']

    def create(self, validated_data):
        # Get the church from the current user
        user = self.context['request'].user
        validated_data['church'] = user.church
        return super().create(validated_data)


class AssignTeacherSerializer(serializers.Serializer):
    """Serializer for assigning teacher to a class"""
    teacher_id = serializers.IntegerField()
    class_id = serializers.IntegerField()

    def validate(self, data):
        teacher_id = data['teacher_id']
        class_id = data['class_id']

        # Check if teacher exists and belongs to the same church
        try:
            teacher = CustomUser.objects.get(id=teacher_id, church=self.context['request'].user.church, role='teacher')
            data['teacher'] = teacher
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Teacher not found or doesn't belong to your church")

        # Check if class exists and belongs to the same church
        try:
            action_unit_class = ActionUnitClass.objects.get(id=class_id, church=self.context['request'].user.church)
            data['action_unit_class'] = action_unit_class
        except ActionUnitClass.DoesNotExist:
            raise serializers.ValidationError("Class not found or doesn't belong to your church")

        return data
    

# actionunit/class teachers
class TeacherSerializer(serializers.ModelSerializer):
    """Serializer for Teacher users"""
    assigned_class = serializers.SerializerMethodField()
    class_id = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'name', 'phone', 'email', 'role', 
            'is_active', 'date_joined', 'assigned_class', 'class_id'
        ]
        read_only_fields = ['id', 'role', 'date_joined']

    def get_assigned_class(self, obj):
        """Get the name of the class this teacher is assigned to"""
        # Use 'teaching_assignments' (from teacher side of the relationship)
        active_assignment = obj.teaching_assignments.filter(is_active=True).first()
        if active_assignment:
            return active_assignment.action_unit_class.name
        return "Not Assigned"

    def get_class_id(self, obj):
        """Get the ID of the class this teacher is assigned to"""
        active_assignment = obj.teaching_assignments.filter(is_active=True).first()
        if active_assignment:
            return active_assignment.action_unit_class.id
        return None



# actionunit/serializers.py  TeacherCreateSerializer
class TeacherCreateSerializer2222(serializers.ModelSerializer):
    """Serializer for creating Teacher users"""
    class Meta:
        model = CustomUser
        fields = ['name', 'phone', 'email']
        # Remove password from fields since we'll auto-generate it

    def create(self, validated_data):
        church = self.context['request'].user.church
        
        # Generate unique username from phone
        phone = validated_data['phone']
        username = phone
        
        counter = 1
        while CustomUser.objects.filter(username=username).exists():
            username = f"{phone}_{counter}"
            counter += 1
        
        # Create teacher user - password will be auto-set in save() method
        teacher = CustomUser.objects.create_user(
            username=username,
            email=validated_data.get('email'),
            password=None,  # Let the model handle default password
            name=validated_data['name'],
            phone=phone,
            role='teacher',
            church=church
        )
        return teacher


# actionunit/serializers.py  TeacherCreateSerializer
class TeacherCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Teacher users"""
    class Meta:
        model = CustomUser
        fields = ['name', 'phone', 'email']
    
    def validate_phone(self, value):
        """Validate that phone doesn't already exist"""
        if CustomUser.objects.filter(phone=value).exists():
            raise serializers.ValidationError("A user with this phone number already exists.")
        return value
    
    def create(self, validated_data):
        church = self.context['request'].user.church
        
        # Use phone as username (should be unique)
        phone = validated_data['phone']
        
        # Create teacher user
        teacher = CustomUser.objects.create_user(
            username=phone,  # Use phone as username
            email=validated_data.get('email'),
            password=None,  # Password will be auto-set in save() method
            name=validated_data['name'],
            phone=phone,
            role='teacher',
            church=church
        )
        return teacher




class TeacherAssignmentSerializer(serializers.Serializer):
    """Serializer for assigning teacher to class"""
    teacher_id = serializers.IntegerField()
    class_id = serializers.IntegerField()

    def validate(self, data):
        teacher_id = data['teacher_id']
        class_id = data['class_id']
        church = self.context['request'].user.church

        # Check if teacher exists and belongs to the same church
        try:
            teacher = CustomUser.objects.get(
                id=teacher_id, 
                church=church, 
                role='teacher'
            )
            data['teacher'] = teacher
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Teacher not found or doesn't belong to your church")

        # Check if class exists and belongs to the same church
        try:
            action_unit_class = ActionUnitClass.objects.get(
                id=class_id, 
                church=church
            )
            data['action_unit_class'] = action_unit_class
        except ActionUnitClass.DoesNotExist:
            raise serializers.ValidationError("Class not found or doesn't belong to your church")

        return data

    def create(self, validated_data):
        teacher = validated_data['teacher']
        action_unit_class = validated_data['action_unit_class']

        # Deactivate any existing assignment for this teacher
        ClassTeacher.objects.filter(teacher=teacher, is_active=True).update(is_active=False)
        
        # Deactivate any existing assignment for this class
        ClassTeacher.objects.filter(action_unit_class=action_unit_class, is_active=True).update(is_active=False)

        # Create new assignment
        assignment = ClassTeacher.objects.create(
            teacher=teacher,
            action_unit_class=action_unit_class
        )
        
        return assignment
    
    

#TeacherMemberSimpleLoginSerializer
class TeacherMemberSimpleLoginSerializer(serializers.Serializer):
    phone = serializers.CharField()

    def validate(self, data):
        phone = data.get('phone')

        if phone:
            try:
                # DEBUG: Print the phone number being searched
                print(f"DEBUG: Searching for phone: '{phone}'")
                
                # Find user by phone number
                user = CustomUser.objects.get(phone=phone)
                print(f"DEBUG: Found user: {user.id}, {user.name}, Role: {user.role}, Is Officer: {user.is_officer}")
                
                # Check if user is teacher, member, OR officer
                is_authorized_user = (
                    user.role in ['teacher', 'member'] or 
                    user.is_officer
                )
                print(f"DEBUG: Is authorized user: {is_authorized_user}")
                
                if not is_authorized_user:
                    raise serializers.ValidationError('No teacher, member, or officer found with this phone number.')
                
                # Auto-generate password based on phone
                default_password = user.get_default_password()
                print(f"DEBUG: Default password: {default_password}")
                
                # Set the password if not already set
                user.set_password(default_password)
                user.save()
                print(f"DEBUG: Password set successfully")
                
                # Authenticate with auto-generated password
                auth_user = authenticate(username=user.username, password=default_password)
                print(f"DEBUG: Auth result: {auth_user}")
                
                if auth_user:
                    if auth_user.is_active:
                        data['user'] = auth_user
                        data['auto_password'] = default_password
                        print(f"DEBUG: Login successful")
                    else:
                        raise serializers.ValidationError('Account disabled.')
                else:
                    raise serializers.ValidationError('Authentication failed.')
                    
            except CustomUser.DoesNotExist as e:
                print(f"DEBUG: User not found with phone: '{phone}'")
                # List all users with similar phones for debugging
                similar_users = CustomUser.objects.filter(phone__contains=phone[-6:])
                print(f"DEBUG: Similar users: {list(similar_users.values('id', 'phone', 'name'))}")
                raise serializers.ValidationError('No teacher, member, or officer found with this phone number.')
        else:
            raise serializers.ValidationError('Phone number is required.')
        
        return data

#class membership management serializers
class ClassMemberSerializer(serializers.ModelSerializer):
    """Serializer for Class Member model"""
    member_name = serializers.CharField(source='user.name', read_only=True)
    member_phone = serializers.CharField(source='user.phone', read_only=True)
    member_email = serializers.CharField(source='user.email', read_only=True)
    class_name = serializers.CharField(source='action_unit_class.name', read_only=True)

    class Meta:
        model = ClassMember
        fields = [
            'id', 'action_unit_class', 'user', 'member_name', 'member_phone', 'location',
            'member_email', 'class_name', 'joined_date', 'is_active'
        ]



class ClassMemberCreateSerializer2222(serializers.ModelSerializer):
    """Serializer for creating Class Members from frontend data"""
    name = serializers.CharField(write_only=True)
    phone = serializers.CharField(write_only=True)
    email = serializers.CharField(write_only=True, required=False, allow_blank=True)
    class_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = ClassMember
        fields = ['name', 'phone', 'email', 'class_id', 'location']

    def validate(self, data):
        # Get the church from the current user - with error handling
        try:
            request = self.context.get('request')
            if not request or not hasattr(request, 'user'):
                raise serializers.ValidationError('Authentication required.')
            
            church = request.user.church
            if not church:
                raise serializers.ValidationError('User must belong to a church.')
                
            data['church'] = church
            
        except AttributeError:
            raise serializers.ValidationError('Authentication required.')

        # Check if class exists and belongs to the same church
        try:
            action_unit_class = ActionUnitClass.objects.get(
                id=data['class_id'],
                church=church
            )
            data['action_unit_class'] = action_unit_class
        except ActionUnitClass.DoesNotExist:
            raise serializers.ValidationError({
                'class_id': 'Class not found or does not belong to your church.'
            })

        # Check if user already exists with this phone in the same church
        existing_user = CustomUser.objects.filter(
            phone=data['phone'],
            church=church
        ).first()

        if existing_user:
            # User exists, check if they're already a member of this class
            if ClassMember.objects.filter(
                action_unit_class=data['action_unit_class'],
                user=existing_user,
                is_active=True
            ).exists():
                raise serializers.ValidationError({
                    'phone': 'This member is already in this class.'
                })
            data['user'] = existing_user
        else:
            # Create new user
            data['user'] = self.create_member_user(data, church)

        return data

    def create_member_user(self, data, church):
        """Create a new member user"""
        # Generate unique username from phone
        username = data['phone']
        counter = 1
        while CustomUser.objects.filter(username=username).exists():
            username = f"{data['phone']}_{counter}"
            counter += 1

        # Create the member user
        user = CustomUser.objects.create_user(
            username=username,
            email=data.get('email', ''),
            password=None,  # Auto-generated password for members
            name=data['name'],
            phone=data['phone'],
            role='member',
            church=church
        )
        return user

    def create(self, validated_data):
        # Remove the frontend fields we don't need for ClassMember creation
        validated_data.pop('name', None)
        validated_data.pop('phone', None)
        validated_data.pop('email', None)
        validated_data.pop('class_id', None)
        validated_data.pop('church', None)

        # Create the class membership
        class_member, created = ClassMember.objects.get_or_create(
            action_unit_class=validated_data['action_unit_class'],
            user=validated_data['user'],
            defaults=validated_data
        )
        return class_member




class ClassMemberCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Class Members from frontend data"""
    name = serializers.CharField(write_only=True)
    phone = serializers.CharField(write_only=True)
    email = serializers.CharField(write_only=True, required=False, allow_blank=True)
    class_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = ClassMember
        fields = ['name', 'phone', 'email', 'class_id', 'location']

    def validate_phone(self, value):
        """Validate phone number format and ensure system-wide uniqueness"""
        if not value:
            raise serializers.ValidationError("Phone number is required.")
        
        # Strip any whitespace and clean the phone number
        cleaned_phone = value.strip()
        
        # Check if phone already exists in ANY church (system-wide uniqueness)
        if CustomUser.objects.filter(phone=cleaned_phone).exists():
            raise serializers.ValidationError("This phone number is already registered in the system.")
        
        return cleaned_phone

    def validate(self, data):
        # Get the church from the current user
        try:
            request = self.context.get('request')
            if not request or not hasattr(request, 'user'):
                raise serializers.ValidationError('Authentication required.')
            
            church = request.user.church
            if not church:
                raise serializers.ValidationError('User must belong to a church.')
                
            data['church'] = church
            
        except AttributeError:
            raise serializers.ValidationError('Authentication required.')

        # Check if class exists and belongs to the same church
        try:
            action_unit_class = ActionUnitClass.objects.get(
                id=data['class_id'],
                church=church
            )
            data['action_unit_class'] = action_unit_class
        except ActionUnitClass.DoesNotExist:
            raise serializers.ValidationError({
                'class_id': 'Class not found or does not belong to your church.'
            })

        # Since phone is system-wide unique, we can safely find the user
        # But we still need to check if they're in this specific church
        existing_user = CustomUser.objects.filter(phone=data['phone']).first()

        if existing_user:
            # User exists system-wide, check if they belong to this church
            if existing_user.church != church:
                raise serializers.ValidationError({
                    'phone': 'This phone number is registered with a different church.'
                })
            
            # User exists in this church, check if they're already in this class
            if ClassMember.objects.filter(
                action_unit_class=data['action_unit_class'],
                user=existing_user,
                is_active=True
            ).exists():
                raise serializers.ValidationError({
                    'phone': 'This member is already in this class.'
                })
            
            data['user'] = existing_user
        else:
            # Create new user (phone uniqueness is guaranteed by validate_phone)
            data['user'] = self.create_member_user(data, church)

        return data

    def create_member_user(self, data, church):
        """Create a new member user with system-wide unique phone"""
        # Phone is already validated as unique, so we can use it as username
        username = data['phone']

        # Create the member user
        user = CustomUser.objects.create_user(
            username=username,
            email=data.get('email', ''),
            password=None,  # Auto-generated password will use phone's last 6 digits
            name=data['name'],
            phone=data['phone'],  # This is system-wide unique
            role='member',
            church=church
        )
        return user

    def create(self, validated_data):
        # Remove the frontend fields we don't need for ClassMember creation
        validated_data.pop('name', None)
        validated_data.pop('phone', None)
        validated_data.pop('email', None)
        validated_data.pop('class_id', None)
        validated_data.pop('church', None)

        # Create or update the class membership
        class_member, created = ClassMember.objects.get_or_create(
            action_unit_class=validated_data['action_unit_class'],
            user=validated_data['user'],
            defaults=validated_data
        )
        
        if not created:
            # Reactivate if previously inactive and update location
            class_member.is_active = True
            class_member.location = validated_data.get('location', class_member.location)
            class_member.save()
            
        return class_member

class BulkImportMemberSerializer(serializers.Serializer):
    """Serializer for bulk importing members from Excel/CSV"""
    name = serializers.CharField()
    phone = serializers.CharField()
    email = serializers.CharField(required=False, allow_blank=True, default='')
    class_name = serializers.CharField()
    location = serializers.CharField(required=False, allow_blank=True, default='')

    def validate(self, data):
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            raise serializers.ValidationError('Authentication required.')
        
        church = request.user.church
        if not church:
            raise serializers.ValidationError('User must belong to a church.')
        
        data['church'] = church
        return data



#attendance serializers
class AttendanceSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='class_member.user.name', read_only=True)
    member_phone = serializers.CharField(source='class_member.user.phone', read_only=True)
    
    class Meta:
        model = Attendance
        fields = ['id', 'class_member', 'date', 'is_present', 'absence_reason', 'marked_by', 'marked_at', 'member_name', 'member_phone']


class AttendanceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = ['class_member', 'date', 'is_present', 'absence_reason']

    def create(self, validated_data):
        # Automatically set the logged-in teacher as marked_by
        validated_data['marked_by'] = self.context['request'].user
        return super().create(validated_data)


class OfferingSerializer(serializers.ModelSerializer):
    recorded_by_name = serializers.CharField(source='recorded_by.name', read_only=True)
    class_name = serializers.CharField(source='action_unit_class.name', read_only=True)
    
    class Meta:
        model = Offering
        fields = [
            'id', 'action_unit_class', 'amount', 'currency', 'date',
            'recorded_by', 'recorded_by_name', 'notes', 'created_at',
            'class_name'
        ]



class OfferingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offering
        fields = ['action_unit_class', 'amount', 'currency', 'date', 'notes']
    
    def create(self, validated_data):
        # Automatically set the logged-in user as recorded_by
        validated_data['recorded_by'] = self.context['request'].user
        return super().create(validated_data)


# sabbath school quarterly
class QuarterlyBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuarterlyBook
        fields = [
            'id', 'title', 'price', 'currency', 'is_active', 
            'created_at', 'updated_at'
        ]



class QuarterlyBookCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuarterlyBook
        fields = ['title', 'price', 'currency', 'is_active']
    
    def create(self, validated_data):
        # Automatically set the church from the logged-in user
        validated_data['church'] = self.context['request'].user.church
        return super().create(validated_data)






# quarterly orders
class OrderItemSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source='quarterly_book.title', read_only=True)
    book_currency = serializers.CharField(source='quarterly_book.currency', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'quarterly_book', 'book_title', 'book_currency', 'quantity', 'unit_price', 'total_price']

class OrderItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['quarterly_book', 'quantity']



class BookOrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True, read_only=True)
    class_name = serializers.CharField(source='action_unit_class.name', read_only=True)
    submitted_by_name = serializers.CharField(source='submitted_by.name', read_only=True)
    
    class Meta:
        model = BookOrder
        fields = [
            'id', 'action_unit_class', 'class_name', 'quarter', 'year', 
            'total_amount', 'status', 'submitted_by', 'submitted_by_name',
            'submitted_date', 'created_at', 'updated_at', 'order_items'
        ]



class BookOrderCreateSerializer(serializers.ModelSerializer):
    order_items = OrderItemCreateSerializer(many=True, required=False)
    
    class Meta:
        model = BookOrder
        fields = ['action_unit_class', 'quarter', 'year', 'order_items']
    
    def create(self, validated_data):
        order_items_data = validated_data.pop('order_items', [])
        validated_data['submitted_by'] = self.context['request'].user
        
        # Check if order already exists and update it
        try:
            existing_order = BookOrder.objects.get(
                action_unit_class=validated_data['action_unit_class'],
                quarter=validated_data['quarter'],
                year=validated_data['year']
            )
            # Update existing order
            for order_item_data in order_items_data:
                order_item, created = OrderItem.objects.get_or_create(
                    book_order=existing_order,
                    quarterly_book=order_item_data['quarterly_book'],
                    defaults={
                        'quantity': order_item_data['quantity'],
                        'unit_price': order_item_data['quarterly_book'].price
                    }
                )
                if not created:
                    order_item.quantity = order_item_data['quantity']
                    order_item.unit_price = order_item_data['quarterly_book'].price
                    order_item.save()
            
            # Update total amount
            existing_order.update_total_amount()
            return existing_order
            
        except BookOrder.DoesNotExist:
            # Create new order
            order = BookOrder.objects.create(**validated_data)
            
            for order_item_data in order_items_data:
                OrderItem.objects.create(
                    book_order=order,
                    quarterly_book=order_item_data['quarterly_book'],
                    quantity=order_item_data['quantity'],
                    unit_price=order_item_data['quarterly_book'].price
                )
            
            order.update_total_amount()
            return order





class BookOrderSubmitSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookOrder
        fields = ['status', 'submitted_date']




#  Subscription serializers
class SubscriptionSerializer(serializers.ModelSerializer):
    church_name = serializers.CharField(source='church.name', read_only=True)
    is_active = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = [
            'id', 'church', 'church_name', 'plan', 'status', 
            'trial_end_date', 'current_period_end', 'grace_period_end',
            'is_active', 'days_remaining', 'created_at', 'updated_at'
        ]

    def get_is_active(self, obj):
        """Check if subscription is currently active"""
        today = timezone.now().date()
        return obj.status in ['trialing', 'active'] and obj.current_period_end >= today

    def get_days_remaining(self, obj):
        """Calculate days remaining in trial/current period"""
        today = timezone.now().date()
        if obj.status == 'trialing':
            end_date = obj.trial_end_date
        else:
            end_date = obj.current_period_end
        
        if end_date >= today:
            return (end_date - today).days
        return 0  # Always return 0 instead of None

class SubscriptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['plan', 'trial_end_date', 'current_period_end']