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
from rest_framework.permissions import IsAuthenticated

# class CartViewSet(ListModelMixin,CreateModelMixin, RetrieveModelMixin, DestroyModelMixin, GenericViewSet):
#     queryset = Cart.objects.all()
#     serializer_class = CartSerializer
#     permission_classes = [IsAuthenticated]
#     http_method_names = ['get', 'post', 'delete']
    
#     def get_queryset(self):
#         # Ensuring we're filtering carts by the Account associated with the authenticated User
#         # if self.request.user.is_staff:  # Check if the user is an admin
#         #     return Cart.objects.all()
#         account = getattr(self.request.user, 'account', None)
#         if account and account.user_type == "Admin":  # Custom admin check
#             return Cart.objects.all()  # Admins can see all carts
#         if account:
#             return Cart.objects.filter(user=account)
#         else:
#             print("Error: No Account associated with this user")
#             return Cart.objects.none()  # No Account found, return empty queryset

#     # def get_queryset(self):
#     #     # Ensure the cart is filtered for the authenticated user
#     #     return Cart.objects.filter(user=self.request.user)

#     def perform_create(self, serializer):
#         account = getattr(self.request.user, 'account', None)
#         if account and account.user_type != 'Admin':
#             serializer.save(user=account)
#             serializer.instance.calculate_grand_total()
#         else:
#             print("Error: No Account associated with this user")
#             raise ValueError("No account associated with the authenticated user./ Admin users cannot create carts.")
#         # cart = serializer.save()
#         # cart.calculate_grand_total()

#     def perform_update(self, serializer):
#         cart = serializer.save()
#         cart.calculate_grand_total()

#     def perform_destroy(self, instance):
#         if instance.pk:  # Ensure that the Cart instance has a primary key
#             super().perform_destroy(instance)
#             instance.calculate_grand_total()
#         else:
#             raise ValueError("Cannot delete a cart without a primary key.")

#     def list(self, request, *args, **kwargs):
#         carts = self.get_queryset()
#         for cart in carts:
#             cart.calculate_grand_total()
#         return super().list(request, *args, **kwargs)

#     def retrieve(self, request, *args, **kwargs):
#         cart = self.get_object()
#         cart.calculate_grand_total()
#         return super().retrieve(request, *args, **kwargs)

class CartViewSet(ListModelMixin, CreateModelMixin, RetrieveModelMixin, DestroyModelMixin, GenericViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'delete']

    def get_queryset(self):
        #Filter carts by user or allow admins to view all carts.
        account = getattr(self.request.user, 'account', None)
        if not account:
            return Cart.objects.none()  # No account found, return an empty queryset

        if account.user_type == "Admin":
            return Cart.objects.all()
        return Cart.objects.filter(user=account)

    def perform_create(self, serializer):
        #Handle cart creation.
        account = getattr(self.request.user, 'account', None)
        if not account or account.user_type == 'Admin':
            raise PermissionDenied("Only customers can create carts.")
        
        cart = serializer.save(user=account)
        cart.calculate_grand_total()
        
    def perform_update(self, serializer):
        #Update cart and recalculate total.
        cart = serializer.save()
        cart.calculate_grand_total()

    def perform_destroy(self, instance):
        #Ensure cart deletion is handled properly.
        instance.items.all().delete()
        instance.delete()

    def list(self, request, *args, **kwargs):
        #List all carts with grand total recalculated.
        carts = self.get_queryset()
        for cart in carts:
            cart.calculate_grand_total()
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        #Retrieve a cart and recalculate grand total.
        cart = self.get_object()
        cart.calculate_grand_total()
        return super().retrieve(request, *args, **kwargs)



# class CartViewSet(ListModelMixin, CreateModelMixin, RetrieveModelMixin, DestroyModelMixin, GenericViewSet):
#     queryset = Cart.objects.all()
#     serializer_class = CartSerializer
#     permission_classes = [IsAuthenticated]
#     http_method_names = ['get', 'post', 'delete']

#     def get_queryset(self):
#         # Ensure that the cart is filtered for the authenticated user
#         return Cart.objects.filter(user=self.request.user)

#     def perform_create(self, serializer):
#         # Create the cart and associate it with the logged-in user
#         serializer.save(user=self.request.user)
#         cart = serializer.instance
#         cart.calculate_grand_total()

#     def perform_update(self, serializer):
#         # Recalculate grand total after updating the cart
#         cart = serializer.save()
#         cart.calculate_grand_total()

#     def perform_destroy(self, instance):
#         # Recalculate grand total after deleting the cart
#         super().perform_destroy(instance)
#         instance.calculate_grand_total()

#     def list(self, request, *args, **kwargs):
#         # Ensure that grand total is calculated for each cart item when listing
#         carts = self.get_queryset()
#         for cart in carts:
#             cart.calculate_grand_total()  # Ensure the grand total is recalculated
#         return super().list(request, *args, **kwargs)

#     def retrieve(self, request, *args, **kwargs):
#         # Recalculate grand total when retrieving a single cart
#         cart = self.get_object()
#         cart.calculate_grand_total()  # Ensure grand total is up-to-date
#         return super().retrieve(request, *args, **kwargs)
    
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


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    http_method_names = ['get', 'post', 'patch', 'put', 'delete', 'head', 'options']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        customer_id = self.request.query_params.get('customer_id')
        if customer_id:
            queryset = queryset.filter(user_id=customer_id)
        return queryset

    def perform_create(self, serializer):
        flower = serializer.validated_data.get('flower')
        user_account = serializer.validated_data.get('user')
        quantity = serializer.validated_data.get('quantity')
        
        if flower and flower.stock >= quantity:
            flower.stock -= quantity
            flower.save()
            total_amount = flower.price * quantity

            order = serializer.save(total_amount=total_amount)

            if user_account:
                email = user_account.user.email
                if email:
                    email_subject = "Thank You for Your Order"
                    email_body = render_to_string('orderemail.html', {
                        'flower_name': flower.flower_name,
                        'quantity': quantity,
                        'total_amount': total_amount,
                        'email': email,
                        'phone': user_account.phone
                    })
                    email_message = EmailMultiAlternatives(email_subject, '', to=[email])
                    email_message.attach_alternative(email_body, "text/html")
                    email_message.send()
                else:
                    print("No email found!")
        else:
            raise serializer.ValidationError("Insufficient stock for the selected flower.")
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        status_before_update = instance.status

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if serializer.validated_data.get('status') == 'Completed' and status_before_update != 'Completed':
            user_email = getattr(instance.user, 'email', None)
            if user_email:
                email_subject = "Order Completed"
                email_body = render_to_string('order_completed_email.html', {
                    'user': instance.user,
                    'order': instance,
                })
                email_message = EmailMultiAlternatives(email_subject, '', to=[user_email])
                email_message.attach_alternative(email_body, "text/html")
                email_message.send()
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='order_count')
    def order_count(self, request):
        total_orders = Order.objects.count()
        return Response({'total_orders': total_orders})

# class CartListCreateView(viewsets.ModelViewSet):
#     queryset = Cart.objects.all()
#     serializer_class = CartSerializer

# class CartDetailView(viewsets.ModelViewSet):
#     queryset = Cart.objects.all()
#     serializer_class = CartSerializer
# class CartViewSet(CreateModelMixin, RetrieveModelMixin, DestroyModelMixin, GenericViewSet):
#     queryset = Cart.objects.all()
#     serializer_class = CartSerializer
    
# class CartItemViewSet(viewsets.ModelViewSet):
#     # queryset = CartItem.objects.all()
#     serializer_class = CartItemSerializer
#     http_method_names = ['get','post','patch','delete']
#     def get_queryset(self):
#         return CartItem.objects.filter(cart_id=self.kwargs['cart_pk'])
    
#     def get_serializer_class(self):
#         if self.request.method == 'POST':
#             return AddCartItemSerializer
#         elif self.request.method == 'PATCH':
#             return UpdateCartItemSerializer
#         return CartItemSerializer
    
#     def get_serializer_context(self):
#         return {"cart_id": self.kwargs["cart_pk"]}
    
