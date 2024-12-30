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

# @method_decorator(csrf_exempt, name='dispatch')
class CartViewSet(ListModelMixin, CreateModelMixin, RetrieveModelMixin, DestroyModelMixin, GenericViewSet):
    authentication_classes = [TokenAuthentication]
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    http_method_names = ['get', 'post', 'delete']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        account = getattr(self.request.user, 'account', None)
        print(f"Account: {account}")  # Debug print
        if not account:
            return Cart.objects.none()
        print(f"User type: {account.user_type}")  # Debug print
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


# class OrderViewSet(viewsets.ModelViewSet):
#     queryset = Order.objects.all()
#     serializer_class = OrderSerializer
#     http_method_names = ['get', 'post', 'patch', 'delete']
#     permission_classes = [IsAuthenticated]  # Ensures that only authenticated users can access orders

#     def get_queryset(self):
#         user = self.request.user

#         # Check if the user is a superuser
#         if user.is_superuser:
#             return Order.objects.all()

#         # Get the related Account instance for the logged-in user
#         account = getattr(user, 'account', None)  # Assuming `Account` is a OneToOne relation with `User`
#         if not account:
#             return Order.objects.none()  # Return an empty queryset if no account is found

#         # Filter orders based on the Account instance
#         return Order.objects.filter(user=account)

#     def get_serializer_class(self):
#         if self.action == 'create':
#             return CreateOrderSerializer
#         elif self.action == 'list':
#             return ListOrderSerializer
#         elif self.action == 'partial_update':
#             return UpdateOrderStatusSerializer
#         return OrderSerializer

#     @transaction.atomic
#     def perform_create(self, serializer):
#         user = self.request.user
#         account = getattr(user, 'account', None)  # Assuming a OneToOne relation exists as `account`
#         if not account:
#             raise ValidationError("Associated account not found for the user.")

#         cart_id = serializer.validated_data.get("cart_id")
#         try:
#             cart = Cart.objects.get(id=cart_id, is_active=True)
#         except Cart.DoesNotExist:
#             raise ValidationError("The cart is inactive or does not exist.")
        
#         order = serializer.save(user=account, cart=cart)

#         # Deactivate the cart after order placement
#         cart.is_active = False
#         cart.save()
#         if user.email:
#             self.send_order_email(order)

#     def send_order_email(self, order, status='Order Confirmation'):
#         email_subject = status
#         email_body = render_to_string('orderemail.html', {
#             'user': order.user.user.username,
#             'order': order,
#         })
#         email = EmailMultiAlternatives(email_subject, '', to=[order.user.user.email])
#         print(email)
#         email.attach_alternative(email_body, "text/html")
#         email.send()

#     @action(detail=False, methods=['get'], url_path='count')
#     def order_count(self, request):
#         count = Order.objects.count()
#         return Response({'order_count': count}, status=status.HTTP_200_OK)

#     def partial_update(self, request, *args, **kwargs):
#         instance = self.get_object()
#         serializer = self.get_serializer(instance, data=request.data, partial=True)
#         serializer.is_valid(raise_exception=True)
#         previous_status = instance.order_status
#         self.perform_update(serializer)

#         if previous_status != 'Completed' and instance.order_status == 'Completed':
#             self.send_order_completed_email(instance)
#         return Response(serializer.data)

#     def send_order_completed_email(self, order):
#         """
#         Send an email when the order status is updated to 'Completed'.
#         """
#         email_subject = "Order Completed"
#         email_body = render_to_string('order_completed_email.html', {
#             'user': order.user.username,
#             'order': order,
#         })
#         email = EmailMultiAlternatives(email_subject, '', to=[order.user.email])
#         email.attach_alternative(email_body, "text/html")
#         email.send()

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
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
        previous_status = instance.order_status
        self.perform_update(serializer)
        self.handle_status_change(instance, previous_status)
        return Response(serializer.data)

    def handle_status_change(self, instance, previous_status):
        if previous_status != 'Completed' and instance.order_status == 'Completed':
            self.send_email("Order Completed", 'order_completed_email.html', {'user': instance.user.username, 'order': instance}, [instance.user.email])

    @action(detail=False, methods=['get'], url_path='count')
    def order_count(self, request):
        count = Order.objects.count()
        return Response({'order_count': count}, status=status.HTTP_200_OK)

    def send_email(self, subject, template, context, recipient_list):
        try:
            email_body = render_to_string(template, context)
            email = EmailMultiAlternatives(subject, '', to=recipient_list)
            email.attach_alternative(email_body, "text/html")
            email.send()
        except Exception as e:
            logger.error(f"Error sending email: {e}")

