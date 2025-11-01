
import random
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count

# Create your views here.
# views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login
from .models import *
from .serializers import *





# actionunit/views.py - UPDATE EXISTING VIEWS
@api_view(['POST'])
@permission_classes([AllowAny])
def church_signup(request):
    """
    Frontend expects: POST /api/church/register/
    Frontend sends: { church: {...}, superintendent: {...}, subscription: {...} }
    Frontend expects response: { access, refresh, user, church }
    """
    serializer = ChurchSignupSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            result = serializer.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(result['user'])
            
            # Return format that frontend expects
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': result['user'].id,
                    'name': result['user'].name,
                    'email': result['user'].email,
                    'role': result['user'].role,
                },
                'church': {
                    'id': result['church'].id,
                    'name': result['church'].name,
                    'email': result['church'].email,
                    'phone': result['church'].phone,
                    'address': result['church'].address,
                    'district': result['church'].district,
                    'country': result['church'].country,
                    'denomination': result['church'].denomination,
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'error': 'Invalid data',
        'details': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

   
@api_view(['POST'])
@permission_classes([AllowAny])
def user_login(request):
    """
    Frontend expects: POST /api/auth/login/ 
    Frontend sends: { email, password }
    Frontend expects response: { access, refresh, user, church }
    """
    serializer = LoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        church = user.church
        subscription = getattr(church, 'subscription', None)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Return format that frontend expects
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role,
                'is_officer':user.is_officer,
            },
            'church': {
                'id': church.id,
                'name': church.name,
                'email': church.email,
                'phone': church.phone,
                'address': church.address,
                'district': church.district,
                'country': church.country,
                'denomination': church.denomination,
            }
        })
    
    return Response({
        'error': 'Invalid credentials'
    }, status=status.HTTP_400_BAD_REQUEST)



# actionunit/views.py - UPDATE AND ADD NEW VIEWS
@api_view(['POST'])
@permission_classes([AllowAny])
def superintendent_login(request):
    """
    Login for superintendents (church email + password)
    """
    serializer = SuperintendentLoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        church = user.church
        subscription = getattr(church, 'subscription', None)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role,
                'is_officer':user.is_officer,
            },
            'church': {
                'id': church.id,
                'name': church.name,
                'email': church.email,
                'phone': church.phone,
                'address': church.address,
                'district': church.district,
                'country': church.country,
                'denomination': church.denomination,
            },
            'subscription': {
                'plan': subscription.plan if subscription else 'free_trial',
                'status': subscription.status if subscription else 'trialing',
                'trial_end_date': subscription.trial_end_date if subscription else None
            }
        })
    
    return Response({
        'error': 'Login failed',
        'details': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def teacher_member_login(request):
    """
    Login for teachers and members (phone + password)
    """
    serializer = TeacherMemberLoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        church = user.church
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        response_data = {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'phone': user.phone,
                'role': user.role,
                'is_officer':user.is_officer,
            },
            'church': {
                'id': church.id,
                'name': church.name,
            }
        }
        
        # Add class information for teachers
        if user.role == 'teacher':
            active_assignment = user.teaching_assignments.filter(is_active=True).first()
            if active_assignment:
                response_data['assigned_class'] = {
                    'id': active_assignment.action_unit_class.id,
                    'name': active_assignment.action_unit_class.name,
                    'location': active_assignment.action_unit_class.location
                }
        
        return Response(response_data)
    
    return Response({
        'error': 'Login failed',
        'details': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)



# actionunit/views.py - ADD THIS VIEW
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    """
    Frontend expects: GET /api/auth/me/ or /api/church/profile/
    Returns current user with church data
    """
    user = request.user
    church = user.church
    
    return Response({
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'phone': user.phone,
        },
        'church': {
            'id': church.id,
            'name': church.name,
            'email': church.email,
            'phone': church.phone,
            'address': church.address,
            'district': church.district,
            'country': church.country,
            'denomination': church.denomination,
        }
    })



# actionunit/class management
# actionunit/views.py - UPDATE classes_list_create VIEW
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def classes_list_create(request):
    """
    GET: List all classes for the current user's church
    POST: Create a new class for the current user's church
    """
    if request.method == 'GET':
        classes = ActionUnitClass.objects.filter(
            church=request.user.church, 
            is_active=True
        ).prefetch_related('teacher_assignments__teacher')  # Use plural 'teacher_assignments'
        
        serializer = ActionUnitClassSerializer(classes, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = ActionUnitClassCreateSerializer(
            data=request.data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            class_instance = serializer.save()
            
            # Return the created class with full details
            full_serializer = ActionUnitClassSerializer(class_instance)
            return Response(full_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# get members of a specific class.
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def class_members_list(request, class_id):
    """
    GET: Get all members of a specific class
    """
    try:
        # Verify the class exists and belongs to user's church
        action_unit_class = ActionUnitClass.objects.get(
            id=class_id, 
            church=request.user.church
        )
    except ActionUnitClass.DoesNotExist:
        return Response(
            {'error': 'Class not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        # Get all active class members for this class
        class_members = ClassMember.objects.filter(
            action_unit_class=action_unit_class,
            is_active=True
        ).select_related('user')
        
        # Format response to match frontend Member interface
        members_data = []
        for class_member in class_members:
            user = class_member.user
            members_data.append({
                'id': str(user.id),
                'name': user.name,
                'phone': user.phone,
                'location': user.location or '',
                'isPresent': False,  # Default for frontend
                'joined_date': class_member.joined_date
            })
        
        return Response(members_data)



@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def class_detail(request, class_id):
    """
    GET: Get class details
    PUT: Update class
    DELETE: Soft delete class (set is_active=False)
    """
    try:
        action_unit_class = ActionUnitClass.objects.get(
            id=class_id, 
            church=request.user.church
        )
    except ActionUnitClass.DoesNotExist:
        return Response(
            {'error': 'Class not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = ActionUnitClassSerializer(action_unit_class)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = ActionUnitClassCreateSerializer(
            action_unit_class, 
            data=request.data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            full_serializer = ActionUnitClassSerializer(action_unit_class)
            return Response(full_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        action_unit_class.is_active = False
        action_unit_class.save()
        return Response(status=status.HTTP_204_NO_CONTENT)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_teacher(request):
    """
    Assign a teacher to a class
    """
    serializer = AssignTeacherSerializer(
        data=request.data, 
        context={'request': request}
    )
    
    if serializer.is_valid():
        teacher = serializer.validated_data['teacher']
        action_unit_class = serializer.validated_data['action_unit_class']

        # Remove existing teacher assignment if any
        ClassTeacher.objects.filter(action_unit_class=action_unit_class).update(is_active=False)
        
        # Create new teacher assignment
        ClassTeacher.objects.create(
            action_unit_class=action_unit_class,
            teacher=teacher
        )
        
        # Return updated class data
        class_serializer = ActionUnitClassSerializer(action_unit_class)
        return Response(class_serializer.data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




# actionunit/
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def teachers_list_create(request):
    """
    GET: List all teachers for the current user's church
    POST: Create a new teacher for the current user's church
    """
    if request.method == 'GET':
        teachers = CustomUser.objects.filter(
            church=request.user.church,
            role='teacher',
            is_active=True
        ).prefetch_related('teaching_assignments__action_unit_class')  # Use 'teaching_assignments'
        
        serializer = TeacherSerializer(teachers, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = TeacherCreateSerializer(
            data=request.data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            teacher = serializer.save()
            
            # Return the created teacher with full details
            full_serializer = TeacherSerializer(teacher)
            return Response(full_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# teacher dashboard info
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teacher_dashboard_info(request):
    """
    GET: Get dashboard statistics for teacher's assigned classes
    """
    try:
        # Get teacher's assigned classes
        teacher_assignments = ClassTeacher.objects.filter(
            teacher=request.user,
            is_active=True
        ).select_related('action_unit_class')
        
        if not teacher_assignments.exists():
            return Response({'error': 'No classes assigned to this teacher'}, status=404)
        
        # For now, use the first assigned class (can be extended to handle multiple)
        class_assignment = teacher_assignments.first()
        action_unit_class = class_assignment.action_unit_class
        
        # Calculate statistics
        today = timezone.now().date()
        
        # Member count
        member_count = ClassMember.objects.filter(
            action_unit_class=action_unit_class,
            is_active=True
        ).count()
        
        # Today's attendance
        today_attendance = Attendance.objects.filter(
            class_member__action_unit_class=action_unit_class,
            date=today,
            is_present=True
        ).count()
        
        # Total offerings (current month)
        current_month_start = today.replace(day=1)
        total_offerings = Offering.objects.filter(
            action_unit_class=action_unit_class,
            date__gte=current_month_start,
            date__lte=today
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        class_info = {
            'id': action_unit_class.id,
            'name': action_unit_class.name,
            'member_count': member_count,
            'today_attendance': today_attendance,
            'total_offerings': float(total_offerings),
            'location': action_unit_class.location or 'Main Church Hall'
        }
        
        return Response(class_info)
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def teacher_detail(request, teacher_id):
    """
    GET: Get teacher details
    PUT: Update teacher
    DELETE: Soft delete teacher (set is_active=False)
    """
    try:
        teacher = CustomUser.objects.get(
            id=teacher_id, 
            church=request.user.church,
            role='teacher'
        )
    except CustomUser.DoesNotExist:
        return Response(
            {'error': 'Teacher not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = TeacherSerializer(teacher)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = TeacherCreateSerializer(
            teacher, 
            data=request.data, 
            context={'request': request},
            partial=True  # Allow partial updates
        )
        
        if serializer.is_valid():
            # Handle password update separately
            password = request.data.get('password')
            if password:
                teacher.set_password(password)
            
            serializer.save()
            full_serializer = TeacherSerializer(teacher)
            return Response(full_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        teacher.is_active = False
        teacher.save()
        return Response(status=status.HTTP_204_NO_CONTENT)



# 
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teacher_classes_list(request):
    """
    GET: Get all classes assigned to the current teacher
    """
    if request.method == 'GET':
        # Get all class assignments for current teacher
        teacher_assignments = ClassTeacher.objects.filter(
            teacher=request.user,
            is_active=True
        ).select_related('action_unit_class')
        
        # Extract the classes from assignments
        classes = [assignment.action_unit_class for assignment in teacher_assignments]
        
        serializer = ActionUnitClassSerializer(classes, many=True)
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_teacher_to_class(request):
    """
    Assign a teacher to a class
    """
    serializer = TeacherAssignmentSerializer(
        data=request.data, 
        context={'request': request}
    )
    
    print(request)
    
    if serializer.is_valid():
        assignment = serializer.save()
        
        # Return success response with assignment details
        return Response({
            'success': True,
            'message': 'Teacher assigned to class successfully',
            'assignment': {
                'teacher_id': assignment.teacher.id,
                'teacher_name': assignment.teacher.name,
                'class_id': assignment.action_unit_class.id,
                'class_name': assignment.action_unit_class.name
            }
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reassign_teacher(request):
    """
    Reassign a teacher to a different class
    """
    serializer = TeacherAssignmentSerializer(
        data=request.data, 
        context={'request': request}
    )
    
    if serializer.is_valid():
        assignment = serializer.save()
        
        return Response({
            'success': True,
            'message': 'Teacher reassigned successfully',
            'assignment': {
                'teacher_id': assignment.teacher.id,
                'teacher_name': assignment.teacher.name,
                'class_id': assignment.action_unit_class.id,
                'class_name': assignment.action_unit_class.name
            }
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# actionunit
@api_view(['POST'])
@permission_classes([AllowAny])
def teacher_member_simple_login(request):
    """
    Simple login for teachers and members (phone only)
    Auto-generates password based on phone number
    """
    serializer = TeacherMemberSimpleLoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        church = user.church
        
         # DEBUG: Print user details
        print(f"DEBUG: User ID: {user.id}, Role: {user.role}, Is Officer: {user.is_officer}")
        
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        response_data = {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'phone': user.phone,
                'role': user.role,
                'is_officer': bool(user.is_officer),  # Add this line
            },
            'church': {
                'id': church.id,
                'name': church.name,
            }
        }
        
        # Add class information for teachers
        if user.role == 'teacher':
            active_assignment = user.teaching_assignments.filter(is_active=True).first()
            if active_assignment:
                response_data['assigned_class'] = {
                    'id': active_assignment.action_unit_class.id,
                    'name': active_assignment.action_unit_class.name,
                    'location': active_assignment.action_unit_class.location
                }
        
        return Response(response_data)
    
    return Response({
        'error': 'Login failed',
        'details': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)




@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def class_members_list_create(request, class_id=None):
    """
    GET: List all members for a class or all classes
    POST: Add a member to a class
    """
    if request.method == 'GET':
        if class_id:
            # Get members for specific class
            members = ClassMember.objects.filter(
                action_unit_class_id=class_id,
                action_unit_class__church=request.user.church,
                is_active=True
            ).select_related('user', 'action_unit_class')
        else:
            # Get all members for the church
            members = ClassMember.objects.filter(
                action_unit_class__church=request.user.church,
                is_active=True
            ).select_related('user', 'action_unit_class')
        
        serializer = ClassMemberSerializer(members, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        # PASS THE REQUEST CONTEXT TO THE SERIALIZER
        serializer = ClassMemberCreateSerializer(
            data=request.data, 
            context={'request': request}  # This is the fix
        )
        
        if serializer.is_valid():
            member = serializer.save()
            full_serializer = ClassMemberSerializer(member)
            return Response(full_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    




@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def class_member_detail(request, member_id):
    """
    DELETE: Remove member from class (soft delete)
    """
    try:
        member = ClassMember.objects.get(
            id=member_id,
            action_unit_class__church=request.user.church
        )
    except ClassMember.DoesNotExist:
        return Response(
            {'error': 'Member not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

    member.is_active = False
    member.save()
    return Response(status=status.HTTP_204_NO_CONTENT)




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_import_members(request):
    """
    Bulk import members from Excel/CSV data
    Expected payload: [{name, phone, email, class_name, location}, ...]
    """
    if request.method == 'POST':
        members_data = request.data.get('members', [])
        
        if not members_data:
            return Response(
                {'error': 'No member data provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        results = {
            'successful': [],
            'failed': [],
            'summary': {
                'total': len(members_data),
                'successful': 0,
                'failed': 0
            }
        }

        for index, member_data in enumerate(members_data):
            try:
                # Validate the incoming data
                serializer = BulkImportMemberSerializer(
                    data=member_data, 
                    context={'request': request}
                )
                
                if not serializer.is_valid():
                    results['failed'].append({
                        'index': index,
                        'data': member_data,
                        'error': serializer.errors
                    })
                    continue

                validated_data = serializer.validated_data
                church = validated_data['church']

                # Find or create the class
                class_name = validated_data['class_name']
                action_unit_class, class_created = ActionUnitClass.objects.get_or_create(
                    church=church,
                    name=class_name,
                    defaults={
                        'location': validated_data.get('location', ''),
                        'is_active': True
                    }
                )

                # Prepare data for ClassMember creation
                class_member_data = {
                    'name': validated_data['name'],
                    'phone': validated_data['phone'],
                    'email': validated_data.get('email', ''),
                    'class_id': action_unit_class.id,
                    'location': validated_data.get('location', '')
                }

                # Use existing ClassMemberCreateSerializer to handle user creation
                class_member_serializer = ClassMemberCreateSerializer(
                    data=class_member_data,
                    context={'request': request}
                )

                if class_member_serializer.is_valid():
                    class_member = class_member_serializer.save()
                    
                    results['successful'].append({
                        'index': index,
                        'member_id': class_member.id,
                        'user_id': class_member.user.id,
                        'class_id': action_unit_class.id,
                        'class_created': class_created,
                        'message': f"Successfully added {validated_data['name']} to {class_name}"
                    })
                    
                else:
                    results['failed'].append({
                        'index': index,
                        'data': member_data,
                        'error': class_member_serializer.errors
                    })

            except Exception as e:
                results['failed'].append({
                    'index': index,
                    'data': member_data,
                    'error': str(e)
                })

        # Update summary counts
        results['summary']['successful'] = len(results['successful'])
        results['summary']['failed'] = len(results['failed'])

        # Return appropriate status code
        if results['summary']['failed'] == results['summary']['total']:
            return Response(results, status=status.HTTP_400_BAD_REQUEST)
        elif results['summary']['failed'] > 0:
            return Response(results, status=status.HTTP_207_MULTI_STATUS)
        else:
            return Response(results, status=status.HTTP_201_CREATED)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_attendance(request):
    """
    POST: Mark attendance for class members - UPDATE existing or CREATE new
    """
    if request.method == 'POST':
        attendance_data = request.data
        
        # Handle both single and bulk attendance
        if not isinstance(attendance_data, list):
            attendance_data = [attendance_data]
        
        updated_attendances = []
        created_attendances = []
        errors = []
        
        for attendance_item in attendance_data:
            try:
                class_member_id = attendance_item['class_member']
                date = attendance_item['date']
                is_present = attendance_item['is_present']
                absence_reason = attendance_item.get('absence_reason')
                
                # Check if attendance already exists
                existing_attendance = Attendance.objects.filter(
                    class_member=class_member_id,
                    date=date
                ).first()
                
                if existing_attendance:
                    # UPDATE existing attendance
                    existing_attendance.is_present = is_present
                    existing_attendance.absence_reason = absence_reason
                    existing_attendance.marked_by = request.user
                    existing_attendance.save()
                    updated_attendances.append(existing_attendance)
                else:
                    # CREATE new attendance
                    attendance = Attendance.objects.create(
                        class_member_id=class_member_id,
                        date=date,
                        is_present=is_present,
                        absence_reason=absence_reason,
                        marked_by=request.user
                    )
                    created_attendances.append(attendance)
                    
            except KeyError as e:
                errors.append(f"Missing required field: {e}")
            except Exception as e:
                errors.append(str(e))
        
        # Prepare response
        result_attendances = updated_attendances + created_attendances
        result_serializer = AttendanceSerializer(result_attendances, many=True)
        
        response_data = {
            'message': f'Successfully processed {len(result_attendances)} attendance records '
                      f'({len(created_attendances)} created, {len(updated_attendances)} updated)',
            'attendances': result_serializer.data
        }
        
        if errors:
            response_data['errors'] = errors
            
        status_code = status.HTTP_200_OK if result_attendances else status.HTTP_400_BAD_REQUEST
        return Response(response_data, status=status_code)


# offering views
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def offerings_list_create(request, class_id=None):
    """
    GET: List offerings for a class or all classes
    POST: Create a new offering
    """
    if request.method == 'GET':
        if class_id:
            # Get offerings for specific class
            offerings = Offering.objects.filter(
                action_unit_class_id=class_id,
                action_unit_class__church=request.user.church
            )
        else:
            # Get all offerings for teacher's classes
            teacher_classes = ActionUnitClass.objects.filter(
                teacher_assignments__teacher=request.user,
                teacher_assignments__is_active=True
            )
            offerings = Offering.objects.filter(action_unit_class__in=teacher_classes)
        
        offerings = offerings.select_related('action_unit_class', 'recorded_by')
        serializer = OfferingSerializer(offerings, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = OfferingCreateSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            offering = serializer.save()
            full_serializer = OfferingSerializer(offering)
            return Response(full_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# absent members
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def absent_members_report(request, class_id=None):
    """
    GET: Get report of absent members with their absence patterns
    Query params: days_back (default: 30), min_absences (default: 1)
    """
    # Get query parameters
    days_back = int(request.GET.get('days_back', 30))
    min_absences = int(request.GET.get('min_absences', 1))
    
    # Calculate date range
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days_back)
    
    try:
        if class_id:
            # Get specific class
            action_unit_class = ActionUnitClass.objects.get(
                id=class_id,
                church=request.user.church
            )
            classes = [action_unit_class]
        else:
            # Get all classes assigned to teacher
            classes = ActionUnitClass.objects.filter(
                teacher_assignments__teacher=request.user,
                teacher_assignments__is_active=True
            )
        
        absent_members_data = []
        
        for class_obj in classes:
            # Get all class members
            class_members = ClassMember.objects.filter(
                action_unit_class=class_obj,
                is_active=True
            ).select_related('user')
            
            for class_member in class_members:
                # Get attendance records for this member in date range
                attendances = Attendance.objects.filter(
                    class_member=class_member,
                    date__range=[start_date, end_date]
                ).order_by('-date')
                
                # Calculate absence statistics
                total_days = (end_date - start_date).days + 1
                absences = attendances.filter(is_present=False)
                absence_count = absences.count()
                
                # Only include members with minimum absences
                if absence_count >= min_absences:
                    last_attendance = attendances.filter(is_present=True).first()
                    last_absence = absences.first()
                    
                    absent_members_data.append({
                    'id': class_member.user.id,
                    'class_member_id': class_member.id,
                    'name': class_member.user.name,
                    'phone': class_member.user.phone,
                    'location': class_member.location or '',  # Get location from ClassMember, not CustomUser
                    'absence_reason': last_absence.absence_reason if last_absence else 'Unknown',
                    'last_attendance': last_attendance.date if last_attendance else None,
                    'absence_count': absence_count,
                    'class_name': class_obj.name,
                    'notes': ''
                })
        
        return Response(absent_members_data)
        
    except ActionUnitClass.DoesNotExist:
        return Response(
            {'error': 'Class not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )



# sabbath school quarterlies
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def quarterly_books_list_create(request):
    """
    GET: List all quarterly books for the church
    POST: Create a new quarterly book
    """
    if request.method == 'GET':
        books = QuarterlyBook.objects.filter(
            church=request.user.church
        ).order_by('-created_at')
        
        serializer = QuarterlyBookSerializer(books, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = QuarterlyBookCreateSerializer(
            data=request.data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            book = serializer.save()
            full_serializer = QuarterlyBookSerializer(book)
            return Response(full_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def quarterly_book_detail(request, book_id):
    """
    GET: Get book details
    PUT: Update book
    DELETE: Delete book
    """
    try:
        book = QuarterlyBook.objects.get(
            id=book_id, 
            church=request.user.church
        )
    except QuarterlyBook.DoesNotExist:
        return Response(
            {'error': 'Book not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = QuarterlyBookSerializer(book)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = QuarterlyBookCreateSerializer(
            book, 
            data=request.data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            full_serializer = QuarterlyBookSerializer(book)
            return Response(full_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        book.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)





# quarterly orders views
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def book_orders_list_create(request):
    """
    GET: List book orders for teacher's classes
    POST: Create or update book order (auto-updates if exists)
    """
    if request.method == 'GET':
        # Get orders for teacher's classes
        teacher_classes = ActionUnitClass.objects.filter(
            teacher_assignments__teacher=request.user,
            teacher_assignments__is_active=True
        )
        orders = BookOrder.objects.filter(
            action_unit_class__in=teacher_classes
        ).select_related('action_unit_class', 'submitted_by').prefetch_related('order_items')
        
        serializer = BookOrderSerializer(orders, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = BookOrderCreateSerializer(
            data=request.data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            try:
                order = serializer.save()
                full_serializer = BookOrderSerializer(order)
                return Response(full_serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(
                    {'error': str(e)}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def book_order_detail(request, order_id):
    """
    GET: Get order details
    PUT: Update order (allowed for both draft and submitted status)
    """
    try:
        order = BookOrder.objects.get(
            id=order_id,
            action_unit_class__teacher_assignments__teacher=request.user
        )
    except BookOrder.DoesNotExist:
        return Response(
            {'error': 'Order not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = BookOrderSerializer(order)
        return Response(serializer.data)

    elif request.method == 'PUT':
        # Remove status restriction - allow updates for both draft and submitted
        order_items_data = request.data.get('order_items', [])
        
        # Update or create order items
        for item_data in order_items_data:
            try:
                order_item = OrderItem.objects.get(
                    book_order=order,
                    quarterly_book_id=item_data['quarterly_book']
                )
                order_item.quantity = item_data['quantity']
                order_item.save()
            except OrderItem.DoesNotExist:
                # Create new order item
                quarterly_book = QuarterlyBook.objects.get(id=item_data['quarterly_book'])
                OrderItem.objects.create(
                    book_order=order,
                    quarterly_book=quarterly_book,
                    quantity=item_data['quantity'],
                    unit_price=quarterly_book.price
                )
        
        # Remove order items that are not in the update data (if needed)
        # This depends on your UI behavior
        
        order.update_total_amount()
        order.save()  # Ensure updated_at is refreshed
        
        serializer = BookOrderSerializer(order)
        return Response(serializer.data)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_book_order(request, order_id):
    """
    POST: Submit a draft order
    """
    try:
        order = BookOrder.objects.get(
            id=order_id,
            action_unit_class__teacher_assignments__teacher=request.user,
            status='draft'
        )
    except BookOrder.DoesNotExist:
        return Response(
            {'error': 'Draft order not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'POST':
        order.status = 'submitted'
        order.submitted_date = timezone.now()
        order.save()
        
        serializer = BookOrderSerializer(order)
        return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def active_quarterly_books(request):
    """
    GET: Get all active quarterly books for ordering
    """
    books = QuarterlyBook.objects.filter(is_active=True)
    serializer = QuarterlyBookSerializer(books, many=True)
    return Response(serializer.data)






# superintendent orders view
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def superintendent_book_orders(request):
    """
    GET: Get all book orders for the superintendent's church
    Query params: quarter, year
    """
   
    
    # Get query parameters
    quarter = request.GET.get('quarter')
    year = request.GET.get('year')
    
    # Get all orders for the church
    orders = BookOrder.objects.filter(
        action_unit_class__church=request.user.church
    ).select_related(
        'action_unit_class', 
        'submitted_by'
    ).prefetch_related('order_items__quarterly_book')
    
    # Filter by quarter and year if provided
    if quarter:
        orders = orders.filter(quarter=quarter)
    if year:
        orders = orders.filter(year=year)
    
    # Group by quarter and year for the response
    orders_data = []
    
    
    
    for order in orders:
         # Format as YYYY-MM-DD
        order_date = order.submitted_date or order.created_at
        formatted_date = order_date.strftime('%Y-%m-%d')
        order_items_data = []
        total_quantity = 0
        
        
        
        for item in order.order_items.all():
            order_items_data.append({
                'book_title': item.quarterly_book.title,
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'total_price': float(item.total_price)
            })
            total_quantity += item.quantity  # Calculate total quantity
        
        orders_data.append({
        'class_id': order.action_unit_class.id,
        'class_name': order.action_unit_class.name,
        'teacher_name': order.submitted_by.name,
        'quarter': f"{order.quarter} {order.year}",
        'order_date': formatted_date,
        'total_order_value': float(order.total_amount),
        'total_order_qty': total_quantity, 
        'status': order.status,
        'books': order_items_data
    })
    
    return Response(orders_data)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def superintendent_orders_quarters(request):
    """
    GET: Get unique quarters and years for filter dropdown
    """
    quarters_data = BookOrder.objects.filter(
        action_unit_class__church=request.user.church
    ).values('quarter', 'year').distinct().order_by('-year', '-quarter')
    
    # Format for frontend dropdown
    quarters_list = []
    for item in quarters_data:
        quarters_list.append(f"{item['quarter']} {item['year']}")
    
    return Response(quarters_list)



# superintendent_dashboard_metrics
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def superintendent_dashboard_metrics(request):
    """
    GET: Get summary statistics for superintendent dashboard
    """
    church = request.user.church
    today = timezone.now().date()
    
    # Total classes
    total_classes = ActionUnitClass.objects.filter(
        church=church, 
        is_active=True
    ).count()
    
    # Total members (across all classes)
    total_members = ClassMember.objects.filter(
        action_unit_class__church=church,
        is_active=True
    ).count()
    
    # Total teachers
    total_teachers = ClassTeacher.objects.filter(
        action_unit_class__church=church,
        is_active=True
    ).values('teacher').distinct().count()
    
    # Today's attendance
    today_attendance = Attendance.objects.filter(
        class_member__action_unit_class__church=church,
        date=today,
        is_present=True
    ).count()
    
    metrics = {
        'total_classes': total_classes,
        'total_members': total_members,
        'total_teachers': total_teachers,
        'today_attendance': today_attendance
    }
    
    return Response(metrics)




#  attendance_reports
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def attendance_reports(request):
    """
    GET: Get attendance reports with date filtering
    Query params: start_date, end_date, class_id (optional)
    """
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date') 
    class_id = request.GET.get('class_id')
    
    # Build query for classes
    classes_query = ActionUnitClass.objects.filter(church=request.user.church)
    if class_id:
        classes_query = classes_query.filter(id=class_id)
    
    reports_data = []
    
    for class_obj in classes_query:
        # Get attendance for this class in date range
        attendance_query = Attendance.objects.filter(
            class_member__action_unit_class=class_obj
        )
        
        if start_date:
            attendance_query = attendance_query.filter(date__gte=start_date)
        if end_date:
            attendance_query = attendance_query.filter(date__lte=end_date)
        
        # Calculate statistics
        total_members = ClassMember.objects.filter(
            action_unit_class=class_obj, 
            is_active=True
        ).count()
        
        present_count = attendance_query.filter(is_present=True).count()
        absent_count = attendance_query.filter(is_present=False).count()
        
        # Get absent reasons
        absent_reasons = attendance_query.filter(
            is_present=False
        ).exclude(absence_reason__isnull=True).values('absence_reason').annotate(
            count=Count('id')
        )
        
        absent_reasons_dict = {
            item['absence_reason']: item['count'] 
            for item in absent_reasons
        }
        
        attendance_rate = (present_count / total_members * 100) if total_members > 0 else 0
        
        # Get teacher name
        teacher = class_obj.teacher_assignments.filter(is_active=True).first()
        teacher_name = teacher.teacher.name if teacher else "No Teacher"
        
        reports_data.append({
            'class_name': class_obj.name,
            'teacher_name': teacher_name,
            'date': start_date or timezone.now().date().isoformat(),  # Use filter date or today
            'total_members': total_members,
            'present_count': present_count,
            'absent_count': absent_count,
            'attendance_rate': round(attendance_rate, 2),
            'absent_reasons': absent_reasons_dict
        })
    
    return Response(reports_data)

#offerings_reports
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def offerings_reports(request):
    """
    GET: Get offerings reports with date filtering
    Query params: start_date, end_date, class_id (optional)
    """
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    class_id = request.GET.get('class_id')
    
    offerings_query = Offering.objects.filter(
        action_unit_class__church=request.user.church
    )
    
    if start_date:
        offerings_query = offerings_query.filter(date__gte=start_date)
    if end_date:
        offerings_query = offerings_query.filter(date__lte=end_date)
    if class_id:
        offerings_query = offerings_query.filter(action_unit_class_id=class_id)
    
    # Group by class
    class_totals = offerings_query.values(
        'action_unit_class__name'
    ).annotate(
        total_amount=Sum('amount')
    ).order_by('action_unit_class__name')
    
    reports_data = []
    
    for class_total in class_totals:
        # Calculate trend (simplified - compare with previous period)
        # You might want to implement more sophisticated trend calculation
        reports_data.append({
            'class_name': class_total['action_unit_class__name'],
            'date': start_date or timezone.now().date().isoformat(),
            'total_amount': float(class_total['total_amount']),
            'trend': 'stable',  # Implement actual trend calculation
            'trend_percentage': 0  # Implement actual percentage calculation
        })
    
    return Response(reports_data)


#books_reports
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def books_reports(request):
    """
    GET: Get book orders reports with date/quarter filtering
    Query params: quarter, year, class_id (optional)
    """
    quarter = request.GET.get('quarter')
    year = request.GET.get('year')
    class_id = request.GET.get('class_id')
    
    orders_query = BookOrder.objects.filter(
        action_unit_class__church=request.user.church,
        status='submitted'  # Only include submitted orders
    )
    
    if quarter:
        orders_query = orders_query.filter(quarter=quarter)
    if year:
        orders_query = orders_query.filter(year=year)
    if class_id:
        orders_query = orders_query.filter(action_unit_class_id=class_id)
    
    reports_data = []
    
    for order in orders_query:
        total_quantity = order.order_items.aggregate(
            total_qty=Sum('quantity')
        )['total_qty'] or 0
        
        reports_data.append({
            'class_name': order.action_unit_class.name,
            'teacher_name': order.submitted_by.name,
            'quarter': f"{order.quarter} {order.year}",
            'total_books': total_quantity,
            'total_value': float(order.total_amount),
            'order_date': order.submitted_date.date().isoformat() if order.submitted_date else order.created_at.date().isoformat(),
            'status': order.status
        })
    
    return Response(reports_data)




# officers insight
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def at_risk_members_analysis(request):
    """
    GET: Analyze and identify members at risk based on attendance patterns
    Query params: days_back (default: 90), min_absences (default: 3)
    """
    days_back = int(request.GET.get('days_back', 90))
    min_absences = int(request.GET.get('min_absences', 3))
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days_back)
    
    # Get all active members in the church
    members = ClassMember.objects.filter(
        action_unit_class__church=request.user.church,
        is_active=True
    ).select_related('user', 'action_unit_class')
    
    at_risk_data = []
    
    for member in members:
        # Get attendance records for the period
        attendances = Attendance.objects.filter(
            class_member=member,
            date__range=[start_date, end_date]
        ).order_by('date')
        
        total_days = (end_date - start_date).days + 1
        present_count = attendances.filter(is_present=True).count()
        absent_count = attendances.filter(is_present=False).count()
        attendance_rate = (present_count / total_days * 100) if total_days > 0 else 0
        
        # Calculate risk factors
        risk_factors = []
        risk_score = 0
        
        # Factor 1: Low overall attendance
        if attendance_rate < 60:
            risk_factors.append(f"Low attendance ({attendance_rate:.1f}%)")
            risk_score += 3
        
        # Factor 2: Recent consecutive absences
        recent_absences = attendances.filter(is_present=False, date__gte=end_date-timedelta(days=21))
        if recent_absences.count() >= 2:
            risk_factors.append(f"{recent_absences.count()} recent absences")
            risk_score += 2
        
        # Factor 3: Frequent specific absence reasons
        absence_reasons = attendances.filter(is_present=False).values('absence_reason').annotate(
            count=Count('id')
        )
        for reason in absence_reasons:
            if reason['count'] >= 2 and reason['absence_reason']:
                risk_factors.append(f"Frequent {reason['absence_reason']}")
                risk_score += 1
        
        # Only include members with risk factors
        if risk_score > 0:
            last_attendance = attendances.filter(is_present=True).order_by('-date').first()
            
            at_risk_data.append({
                'member_id': member.user.id,
                'member_name': member.user.name,
                'member_phone': member.user.phone,
                'member_location': member.location,
                'class_name': member.action_unit_class.name,
                'attendance_rate': round(attendance_rate, 1),
                'total_absences': absent_count,
                'risk_score': risk_score,
                'risk_factors': risk_factors,
                'last_attendance': last_attendance.date if last_attendance else None,
                'days_since_last_attendance': (end_date - last_attendance.date).days if last_attendance else None
            })
    
    # Sort by risk score (highest first)
    at_risk_data.sort(key=lambda x: x['risk_score'], reverse=True)
    
    return Response(at_risk_data)





# officers_management
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def officers_management(request):
    """
    GET: List all officers in the church
    POST: Create a new officer (promote existing member or create new)
    """
    if request.method == 'GET':
        # Get all officers in the church
        officers = CustomUser.objects.filter(
            church=request.user.church,
            is_officer=True
        ).order_by('-date_joined')
        
        serializer = CustomUserSerializer(officers, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        phone = request.data.get('phone')
        
        # Check if user already exists
        try:
            # Try to find existing user
            user = CustomUser.objects.get(phone=phone)
            
            # If user exists, promote to officer and set default password
            if user.church != request.user.church:
                return Response(
                    {'error': 'User belongs to a different church'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user.is_officer = True
            user.role = 'member'
            
            # Set the default password for login
            default_password = user.get_default_password()
            user.set_password(default_password)
            user.save()
            
            # Serialize the updated user for response
            user_serializer = CustomUserSerializer(user)
            return Response(user_serializer.data, status=status.HTTP_201_CREATED)
            
        except CustomUser.DoesNotExist:
            # Create new officer
            user_data = {
                'phone': phone,
                'role': 'member',
                'is_officer': True,
                'name': request.data.get('name', ''),
                'email': request.data.get('email', ''),
                
            }
            
            print("USER DATA BEING SENT:", user_data)  # Debug line
            
            serializer = CustomUserCreateSerializer(
                data=user_data, 
                context={'request': request}
            )
        
            print("SERIALIZER VALID:", serializer.is_valid())  # Debug line
            if not serializer.is_valid():
                print("SERIALIZER ERRORS:", serializer.errors)  # Debug line
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            user = serializer.save()
            
            # Set the default password after creation
            default_password = user.get_default_password()
            user.set_password(default_password)
            user.save()
            
            # Serialize the created user for response
            user_serializer = CustomUserSerializer(user)
            return Response(user_serializer.data, status=status.HTTP_201_CREATED)
    

@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def officer_detail(request, officer_id):
    """
    PUT: Toggle officer active status or update details
    DELETE: Remove officer role (demote)
    """
    try:
        officer = CustomUser.objects.get(
            id=officer_id,
            church=request.user.church,
            is_officer=True
        )
    except CustomUser.DoesNotExist:
        return Response(
            {'error': 'Officer not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'PUT':
        # Toggle is_active status or update details
        if 'is_active' in request.data:
            officer.is_active = request.data['is_active']
        if 'name' in request.data:
            officer.name = request.data['name']
        
        officer.save()
        serializer = CustomUserSerializer(officer)
        return Response(serializer.data)

    elif request.method == 'DELETE':
        # Demote officer (remove officer role but keep as member)
        officer.is_officer = False
        officer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    
    
    
# subscription_status
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def subscription_status(request):
    """
    GET: Get current subscription status for the church
    """
    try:
        subscription = Subscription.objects.get(church=request.user.church)
        serializer = SubscriptionSerializer(subscription)
        return Response(serializer.data)
    except Subscription.DoesNotExist:
        return Response(
            {'error': 'No subscription found for this church'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_subscription(request):
    """
    POST: Create initial subscription (for new churches)
    """
    try:
        # Check if subscription already exists
        Subscription.objects.get(church=request.user.church)
        return Response(
            {'error': 'Subscription already exists for this church'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Subscription.DoesNotExist:
        # Calculate trial end date (30 days from now)
        trial_end = timezone.now().date() + timedelta(days=60)
        current_period_end = trial_end
        
        subscription_data = {
            'church': request.user.church.id,
            'plan': 'free_trial',
            'status': 'trialing',
            'trial_end_date': trial_end,
            'current_period_end': current_period_end
        }
        
        serializer = SubscriptionCreateSerializer(data=subscription_data)
        if serializer.is_valid():
            subscription = serializer.save()
            full_serializer = SubscriptionSerializer(subscription)
            return Response(full_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_payment(request):
    """
    POST: Initiate payment for subscription upgrade/renewal
    """
    plan = request.data.get('plan')  # 'monthly' or 'annual' or 'quarter'
    phone_number = request.data.get('phone_number')
    
    if plan not in ['monthly', 'annual', 'quarterly']:
        return Response(
            {'error': 'Invalid plan type'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Calculate new period end date
    today = timezone.now().date()
    if plan == 'monthly':
        period_end = today + timedelta(days=30)
    elif plan == 'quarterly':
        period_end = today + timedelta(days=90)
    else:  # annual
        period_end = today + timedelta(days=365)
    
    # Generate transaction ID
    transaction_id = f"MTN_{int(timezone.now().timestamp())}"
    
    # In a real implementation, you would integrate with MTN Mobile Money API here
    # For now, we'll simulate the payment initiation
    
    response_data = {
        'success': True,
        'transaction_id': transaction_id,
        'plan': plan,
         'amount': {
            'monthly': 50.00,
            'quarterly': 150.00, 
            'yearly': 500.00
        }.get(plan, 150.00),  # Default to quaterly if plan not found
        'currency': 'GHS',
        'message': 'Payment initiated successfully. Please check your phone to complete payment.'
    }
    
    return Response(response_data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_payment(request):
    """
    POST: Verify payment and update subscription
    """
    transaction_id = request.data.get('transaction_id')
    plan = request.data.get('plan')
    
    # In real implementation, verify with payment provider
    # For now, we'll assume payment is successful
    
    try:
        subscription = Subscription.objects.get(church=request.user.church)
        
        # Update subscription
        today = timezone.now().date()
        if plan == 'monthly':
            period_end = today + timedelta(days=30)
        elif plan == 'quarterly':
            period_end = today + timedelta(days=90)
        else:  # annual
            period_end = today + timedelta(days=365)
        
        subscription.plan = plan
        subscription.status = 'active'
        subscription.current_period_end = period_end
        subscription.save()
        
        serializer = SubscriptionSerializer(subscription)
        return Response({
            'success': True,
            'message': 'Payment verified and subscription updated',
            'subscription': serializer.data
        })
        
    except Subscription.DoesNotExist:
        return Response(
            {'error': 'Subscription not found'},
            status=status.HTTP_404_NOT_FOUND
        )