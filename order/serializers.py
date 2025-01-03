from rest_framework import serializers
from .models import Order, Cart, CartItem, OrderItem
from flowers.models import Flower
from flowers.serializers import FlowerSerializer
from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum, F, FloatField
from collections import defaultdict

class CartItemSerializer(serializers.ModelSerializer):
    flower_name = serializers.ReadOnlyField(source='flower.flower_name')
    price = serializers.ReadOnlyField(source='flower.price')
    stock = serializers.ReadOnlyField(source='flower.stock')
    image_url = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'flower', 'flower_name', 'quantity', 'price', 'stock', 'image_url', 'total_price']

    def get_total_price(self, obj):
        return obj.get_total()
    
    def get_image_url(self, obj):
        return obj.flower.image.url if obj.flower.image else None  # Ensure the image URL is returned

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    grand_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    class Meta:
        model = Cart
        fields = ['id', 'user', 'is_active', 'created_at', 'updated_at', 'items', 'grand_total']
        read_only_fields = ['user']
        
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        cart = Cart.objects.create(**validated_data)

        for item_data in items_data:
            CartItem.objects.create(cart=cart, **item_data)

        # Recalculate the grand total after items are added
        cart.calculate_grand_total()
        cart.save()
        return cart

class AddCartItemSerializer(serializers.ModelSerializer):
    flower_id = serializers.IntegerField()
    quantity = serializers.IntegerField(default=1)

    class Meta:
        model = CartItem
        fields = ["id", "flower_id", "quantity"]

    def validate(self, data):
        flower_id = data["flower_id"]
        quantity = data.get("quantity", 1)
        try:
            flower = Flower.objects.get(id=flower_id)
        except Flower.DoesNotExist:
            raise serializers.ValidationError("Invalid flower ID.")

        if flower.stock < quantity:
            raise serializers.ValidationError("Not enough stock available for this item.")
        
        return data

    def save(self, **kwargs):
        cart_id = self.context["cart_id"]
        flower_id = self.validated_data["flower_id"]
        quantity = self.validated_data["quantity"]

        try:
            flower = Flower.objects.get(id=flower_id)
            cart = Cart.objects.get(id=cart_id)
        except ObjectDoesNotExist:
            raise serializers.ValidationError("Invalid cart or flower ID.")

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            flower=flower,
            defaults={'quantity': quantity, 'price_at_added': flower.price}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        flower.stock -= quantity
        flower.save()

        cart.calculate_grand_total()

        self.instance = cart_item
        return self.instance


class UpdateCartItemSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField(min_value=1)

    class Meta:
        model = CartItem
        fields = ["quantity"]

    def save(self, **kwargs):
        cart_item = self.instance
        new_quantity = self.validated_data['quantity']
        flower = cart_item.flower
        current_quantity = cart_item.quantity

        if new_quantity > current_quantity:
            quantity_diff = new_quantity - current_quantity
            if flower.stock < quantity_diff:
                raise serializers.ValidationError("Not enough stock available to increase the quantity.")
            flower.stock -= quantity_diff
        else:
            quantity_diff = current_quantity - new_quantity
            flower.stock += quantity_diff

        flower.save()
        cart_item.quantity = new_quantity
        cart_item.save()
        
        # Recalculate the cart's grand total after updating the item quantity
        cart_item.cart.calculate_grand_total()
        
        return cart_item

class OrderItemSerializer(serializers.ModelSerializer):
    sub_total = serializers.SerializerMethodField()
    flower_name = serializers.ReadOnlyField(source='flower.flower_name')
    flower_price = serializers.ReadOnlyField(source='flower.price')
    flower_id = serializers.ReadOnlyField(source='flower.id')  # Add flower_id field

    class Meta:
        model = OrderItem
        fields = ['id', 'flower_id', 'flower_name', 'quantity', 'flower_price', 'sub_total']

    def get_sub_total(self, obj):
        return obj.get_total()

class CreateOrderSerializer(serializers.ModelSerializer):
    cart_id = serializers.IntegerField(write_only=True)
    items = OrderItemSerializer(source='order_items_relation', many=True, read_only=True)
    shipping_address = serializers.CharField(
        max_length=255,
        required=False,
        default="Not Provided"
    )
    payment_status = serializers.CharField(read_only=True)
    class Meta:
        model = Order
        fields = ['id', 'user', 'cart_id', 'placed_time', 'status', 'payment_status', 'shipping_address','items']

    def validate_cart_id(self, value):
        try:
            cart = Cart.objects.get(id=value, is_active=True)
        except Cart.DoesNotExist:
            raise serializers.ValidationError("Cart does not exist or is inactive.")
        if not cart.items.exists():
            raise serializers.ValidationError("Cannot place an order with an empty cart.")
        return value
    
    def create(self, validated_data):
        user = validated_data.pop('user')
        cart_id = validated_data.pop('cart_id')
        shipping_address = validated_data.pop('shipping_address', "Not Provided")
        print(f"Received Cart ID: {cart_id}")
        try:
            cart = Cart.objects.get(id=cart_id)
        except Cart.DoesNotExist:
            raise serializers.ValidationError(f"Cart with ID {cart_id} does not exist.")

        print(f"Cart ID: {cart.id}, Cart Active: {cart.is_active}")
        if not cart.is_active:
            raise serializers.ValidationError("This cart is inactive and cannot be used to place an order.")
        if not cart.items.exists():
            raise serializers.ValidationError("Cannot place an order with an empty cart.")

        item_quantities = defaultdict(lambda: {'quantity': 0, 'price_at_added': None})
        for item in cart.items.all():
            flower_id = item.flower.id
            item_quantities[flower_id]['quantity'] += item.quantity
            item_quantities[flower_id]['price_at_added'] = item.flower.price

        flower_ids = item_quantities.keys()
        flowers = Flower.objects.filter(id__in=flower_ids)
        flower_map = {flower.id: flower for flower in flowers}

        missing_flower_ids = set(flower_ids) - set(flower_map.keys())
        if missing_flower_ids:
            raise serializers.ValidationError(f"Missing flowers for IDs: {missing_flower_ids}")
        
        order = Order.objects.create(user=user, shipping_address=shipping_address)
        order_items = [
            OrderItem(
                order=order,
                flower=flower_map[flower_id],
                quantity=details['quantity'],
                price_at_order_time=details['price_at_added']
            )
            for flower_id, details in item_quantities.items()
        ]
        OrderItem.objects.bulk_create(order_items)
        order.total_amount = sum(
            item.quantity * item.price_at_order_time for item in order_items
        )
        order.save()
        cart.is_active = False
        cart.save()
        return order

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    username = serializers.ReadOnlyField(source='user.user.username')
    shipping_address = serializers.CharField(read_only=True)
    transaction_id = serializers.CharField(read_only=True)
    payment_status = serializers.CharField(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'username', 'placed_time', 'status',
            'payment_status', 'transaction_id', 'total_amount',
            'items', 'shipping_address'
        ]

class ListOrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)  # Use correct related_name
    username = serializers.ReadOnlyField(source='user.user.username')
    shipping_address = serializers.CharField(read_only=True)
    transaction_id = serializers.CharField(read_only=True)
    payment_status = serializers.CharField(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user','username', 'status', 'payment_status',
            'transaction_id', 'total_amount', 'placed_time',
            'items', 'shipping_address'
        ]


class UpdateOrderStatusSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=Order.ORDER_STATUS)
    transaction_id = serializers.CharField(required=False)
    payment_status = serializers.ChoiceField(
        choices=Order.PAYMENT_STATUS, required=False
    )
    class Meta:
        model = Order
        fields = ['status', 'payment_status', 'transaction_id']

    def update(self, instance, validated_data):
        instance.status = validated_data['status']
        instance.payment_status = validated_data.get('payment_status', instance.payment_status)
        instance.transaction_id = validated_data.get('transaction_id', instance.transaction_id)
        instance.save()
        return instance

