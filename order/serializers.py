from rest_framework import serializers
from .models import Order, Cart, CartItem, OrderItem
from flowers.models import Flower
from flowers.serializers import FlowerSerializer
from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist

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
        fields = ['id', 'user', 'created_at', 'updated_at', 'items', 'grand_total']
    
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
    class Meta:
        model = OrderItem
        fields = ['id','flower','quantity','sub_total']
    
    def get_sub_total(self, obj):
        return obj.get_total()
    
# Order Serializer
class OrderSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    flower_names = serializers.SerializerMethodField()
    flower_prices = serializers.SerializerMethodField()
    # items = CartItemSerializer(source='cart.items', many=True, read_only=True)  # Serialize the items from the related cart
    items = OrderItemSerializer(many=True, read_only=True) # Serialize the items from the related
    class Meta:
        model = Order
        fields = ['id', 'user', 'username', 'placed_time', 'status', 'total_amount', 'items', 'flower_names', 'flower_prices']

    def get_username(self, obj):
        return obj.user.user.username if obj.user else None

    def get_flower_names(self, obj):
        if obj.cart and obj.cart.items.exists():
            return ", ".join([item.flower.flower_name for item in obj.cart.items.all()])
        return None

    def get_flower_prices(self, obj):
        if obj.cart and obj.cart.items.exists():
            return ", ".join([f"${item.flower.price}" for item in obj.cart.items.all()])
        return None

