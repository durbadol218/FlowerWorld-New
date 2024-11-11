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

class CartViewSet(ListModelMixin, CreateModelMixin, RetrieveModelMixin, DestroyModelMixin, GenericViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'delete']

    # def get_queryset(self):
    #     # Ensure the cart is filtered for the authenticated user
    #     return Cart.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Create the cart and trigger the grand total calculation
        cart = serializer.save()
        cart.calculate_grand_total()

    def perform_update(self, serializer):
        # Recalculate grand total after updating the cart
        cart = serializer.save()
        cart.calculate_grand_total()

    def perform_destroy(self, instance):
        # Recalculate grand total after deleting the cart
        super().perform_destroy(instance)
        instance.calculate_grand_total()

    def list(self, request, *args, **kwargs):
        # Ensure that grand total is calculated for each cart item when listing
        carts = self.get_queryset()
        for cart in carts:
            cart.calculate_grand_total()  # Ensure the grand total is recalculated
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        # Recalculate grand total when retrieving a single cart
        cart = self.get_object()
        cart.calculate_grand_total()  # Ensure grand total is up-to-date
        return super().retrieve(request, *args, **kwargs)
    # def get_queryset(self):
    #     # Optionally, filter carts by the authenticated user if needed:
    #     return Cart.objects.filter(user=self.request.user)
    
    # def list(self, request, *args, **kwargs):
    #     # Get the queryset filtered by the authenticated user
    #     queryset = self.get_queryset()
        
    #     # Serialize the data
    #     serializer = self.get_serializer(queryset, many=True)
        
    #     # Return a Response with serialized data
    #     return Response(serializer.data, status=status.HTTP_200_OK)

class CartItemViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        # Retrieves only items in the specified cart (via cart_pk)
        return CartItem.objects.filter(cart_id=self.kwargs['cart_pk'])

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AddCartItemSerializer
        elif self.request.method == 'PATCH':
            return UpdateCartItemSerializer
        return CartItemSerializer

    def get_serializer_context(self):
        # Passes the cart ID to serializers that require it
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
    
