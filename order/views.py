from rest_framework.decorators import action
from rest_framework import viewsets, status
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .models import Order, Cart, CartItem, OrderItem
from .serializers import OrderSerializer, CartSerializer, CartItemSerializer, AddCartItemSerializer, UpdateCartItemSerializer
from flowers.models import Flower
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from rest_framework.mixins import ListModelMixin,CreateModelMixin,RetrieveModelMixin, DestroyModelMixin
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from rest_framework.authentication import TokenAuthentication
from django.db import transaction
from .serializers import OrderSerializer, CreateOrderSerializer, ListOrderSerializer, UpdateOrderStatusSerializer
from .models import Order, Cart
from rest_framework.exceptions import ValidationError
import traceback

# @method_decorator(csrf_exempt, name='dispatch')
class CartViewSet(ListModelMixin, CreateModelMixin, RetrieveModelMixin, DestroyModelMixin, GenericViewSet):
    authentication_classes = [TokenAuthentication]
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    http_method_names = ['get', 'post', 'delete']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        account = getattr(self.request.user, 'account', None)
        print(f"Account: {account}")
        if not account:
            return Cart.objects.none()
        print(f"User type: {account.user_type}")
        return Cart.objects.filter(user=account, is_active=True) if account.user_type != "Admin" else Cart.objects.all()

    def perform_create(self, serializer):
        account = getattr(self.request.user, 'account', None)
        if not account or account.user_type == 'Admin':
            raise ValidationError("Only customers can create carts.")
        
        if Cart.objects.filter(user=account, is_active=True).exists():
            raise ValidationError("A cart already exists for this user.")
        
        cart = serializer.save(user=account)
        cart.calculate_grand_total()
        cart.save()

    def perform_update(self, serializer):
        cart = serializer.save()
        cart.calculate_grand_total()
        cart.save()

    def perform_destroy(self, instance):
        instance.items.all().delete()
        instance.delete()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        for cart in queryset:
            cart.calculate_grand_total()
            cart.save()
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

# class CartViewSet(ListModelMixin, CreateModelMixin, RetrieveModelMixin, DestroyModelMixin, GenericViewSet):
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated]
#     serializer_class = CartSerializer
#     queryset = Cart.objects.all()
#     http_method_names = ['get', 'post', 'delete']

#     def get_queryset(self):
#         user = self.request.user

#         # Ensure user has an account (UserAccount)
#         try:
#             account = user.account
#         except AttributeError:
#             print("No UserAccount associated with this user.")
#             return Cart.objects.none()

#         print(f"User: {user}, Account: {account}, User Type: {account.user_type}")
        
#         if account.user_type == "Admin":
#             return Cart.objects.all()
#         return Cart.objects.filter(user=account, is_active=True)

#     def perform_create(self, serializer):
#         try:
#             account = self.request.user.account
#         except AttributeError:
#             raise ValidationError("Only registered customers can create carts.")

#         if account.user_type == 'Admin':
#             raise ValidationError("Admins are not allowed to create carts.")

#         if Cart.objects.filter(user=account, is_active=True).exists():
#             raise ValidationError("A cart already exists for this user.")

#         cart = serializer.save(user=account)
#         cart.calculate_grand_total()
#         cart.save()


#     def perform_update(self, serializer):
#         cart = serializer.save()
#         cart.calculate_grand_total()
#         cart.save()

#     def perform_destroy(self, instance):
#         instance.items.all().delete()
#         instance.delete()

#     def list(self, request, *args, **kwargs):
#         try:
#             queryset = self.get_queryset()

#             for cart in queryset:
#                 cart.calculate_grand_total()
#                 cart.save()

#             serializer = self.get_serializer(queryset, many=True)
#             return Response(serializer.data)
#         except Exception as e:
#             print("[CartViewSet] Error in list():", str(e))
#             traceback.print_exc()
#             return Response(
#                 {"detail": "An error occurred while retrieving cart(s)."},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )
            
class CartItemViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        return CartItem.objects.filter(cart_id=self.kwargs['cart_pk'])

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AddCartItemSerializer
        elif self.request.method == 'PATCH':
            return UpdateCartItemSerializer
        return CartItemSerializer

    def get_serializer_context(self):
        return {"cart_id": self.kwargs["cart_pk"]}
import logging
logger = logging.getLogger(__name__)

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        print(f"User: {user.username}, Account Type: {user.account.user_type if hasattr(user, 'account') else 'No Account'}")

        if hasattr(user, 'account') and user.account.user_type == "Admin":
            return Order.objects.select_related('user').prefetch_related('items')

        account = self.get_account()
        return Order.objects.filter(user=account).select_related('user').prefetch_related('items')

    def get_account(self):
        account = getattr(self.request.user, 'account', None)
        if not account:
            raise ValidationError("Associated account not found for the user.")
        return account

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateOrderSerializer
        elif self.action == 'list':
            return ListOrderSerializer
        elif self.action == 'partial_update':
            return UpdateOrderStatusSerializer
        return OrderSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        account = self.get_account()
        cart_id = serializer.validated_data.get("cart_id")
        cart = Cart.objects.filter(id=cart_id, is_active=True).first()
        if not cart:
            raise ValidationError("The cart is inactive or does not exist.")
        order = serializer.save(user=account, cart=cart)
        cart.is_active = False
        cart.save()

        if self.request.user.email:
            self.send_email("Order Confirmation", 'orderemail.html', {'user': account.user.username, 'order': order}, [account.user.email])

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        if not hasattr(request.user, 'account') or request.user.account.user_type != "Admin":
            raise PermissionError("You do not have permission to change the order status.")

        previous_status = instance.status
        self.perform_update(serializer)

        if instance.status != previous_status:
            self.handle_status_change(instance, previous_status)
        return Response(serializer.data)

    def handle_status_change(self, instance, previous_status):
        if previous_status != 'Completed' and instance.status == 'Completed':
            self.send_email(
                "Order Completed",
                'order_completed_email.html',
                {'user': instance.user.user.username, 'order': instance},
                [instance.user.user.email]
            )

    @action(detail=False, methods=['get'], url_path='count')
    def order_count(self, request):
        if hasattr(request.user, 'account') and request.user.account.user_type == "Admin":
            count = Order.objects.count()
            return Response({'order_count': count}, status=status.HTTP_200_OK)
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    def send_email(self, subject, template, context, recipient_list):
        try:
            email_body = render_to_string(template, context)
            email = EmailMultiAlternatives(subject, '', to=recipient_list)
            email.attach_alternative(email_body, "text/html")
            email.send()
        except Exception as e:
            logger.error(f"Error sending email: {e}")

