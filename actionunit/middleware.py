# middleware.py
from django.http import JsonResponse
from django.utils import timezone

from .models import Subscription

class SubscriptionMiddleware:
    """
    Django Middleware for Subscription-Based Access Control
    
    This middleware enforces subscription-based access control for all non-GET API requests.
    It ensures that only churches with active subscriptions can perform write operations
    (POST, PUT, PATCH, DELETE) while allowing read operations (GET) for all users.
    
    Access Levels:
    - ACTIVE/TRIALING: Full access (all HTTP methods)
    - PAST_DUE/GRACE_PERIOD: Read-only (GET only, writes blocked with 402 status)
    - CANCELED/UNPAID/EXPIRED: Read-only (GET only, writes blocked with 402 status)
    
    Flow:
    1. Skip authentication and static endpoints
    2. Allow all GET requests (read-only access)
    3. For write operations, check subscription status
    4. Block writes if subscription is not active with 402 Payment Required
    
    HTTP 402 Payment Required is used to indicate subscription payment is needed.
    
    Example Responses:
    - 200: Request allowed (active subscription or GET request)
    - 402: Subscription required (with error message)
    - 404: Subscription not found (allowed for new churches)
    
    This works in conjunction with frontend FeatureGuard service to provide
    both user experience hints and backend security enforcement.
    """
    
    def __init__(self, get_response):
        """
        Initialize the middleware.
        
        Args:
            get_response: The next middleware/handler in the chain
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Process the request through middleware chain.
        
        Args:
            request: The incoming HTTP request
            
        Returns:
            response: The HTTP response
        """
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Process view before it's called to check subscription permissions.
        
        This method is called before the view function and can return:
        - None: Continue normal processing
        - HttpResponse: Short-circuit and return response immediately
        
        Args:
            request: The HTTP request object
            view_func: The view function that will be called
            view_args: Positional arguments for the view
            view_kwargs: Keyword arguments for the view
            
        Returns:
            None|JsonResponse: None to continue, or JsonResponse to block
        """
        # Skip for authentication endpoints (login, token refresh, etc.)
        if request.path.startswith('/api/auth/'):
            return None
            
        # Skip for static files and admin endpoints
        if request.path.startswith('/static/') or request.path.startswith('/admin/'):
            return None
        
        # Allow all GET requests (read-only access for all subscription states)
        if request.method == 'GET':
            return None
            
        # Check if user is authenticated and has a church association
        if not (hasattr(request, 'user') and 
                request.user.is_authenticated and 
                hasattr(request.user, 'church')):
            return None
            
        try:
            subscription = request.user.church.subscription
            today = timezone.now().date()
            
            # BLOCK: Subscription is in terminated states
            if subscription.status in ['canceled', 'unpaid']:
                return JsonResponse(
                    {
                        'error': 'Subscription terminated',
                        'message': 'Your subscription has been terminated. Please contact support.',
                        'code': 'SUBSCRIPTION_TERMINATED'
                    },
                    status=402
                )
                
            # BLOCK: Subscription is past due (payment failed)
            if subscription.status == 'past_due':
                return JsonResponse(
                    {
                        'error': 'Payment past due',
                        'message': 'Your payment is past due. Please update your payment method.',
                        'code': 'PAYMENT_PAST_DUE'
                    },
                    status=402
                )
                
            # BLOCK: Current billing period has ended
            if subscription.current_period_end < today:
                return JsonResponse(
                    {
                        'error': 'Subscription period ended',
                        'message': 'Your subscription period has ended. Please renew to continue.',
                        'code': 'SUBSCRIPTION_EXPIRED'
                    },
                    status=402
                )
                
            # ALLOW: Subscription is active or trialing
            if subscription.status in ['active', 'trialing']:
                return None
                
        except Subscription.DoesNotExist:
            # No subscription found - allow access for new churches
            # This enables churches to use the system initially
            # A subscription will be created on their first write operation
            return None
                
        # Default deny for any unhandled cases
        return JsonResponse(
            {
                'error': 'Subscription access denied',
                'message': 'Unable to verify subscription status.',
                'code': 'SUBSCRIPTION_ACCESS_DENIED'
            },
            status=402
        )