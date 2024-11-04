from rest_framework import serializers
from .models import Order, Cart, CartItem, OrderItem
from flowers.models import Flower
from flowers.serializers import FlowerSerializer
from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist

class CartItemSerializer(serializers.ModelSerializer):
    flower = FlowerSerializer()
    sub_total = serializers.SerializerMethodField()
    
    class Meta:
        model = CartItem
        fields = ['id', 'cart', 'flower','quantity', 'sub_total']
    
    def get_sub_total(self,obj):
        return obj.get_total()

# Cart Serializer
class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    grand_total = serializers.SerializerMethodField(method_name='main_total')
    class Meta:
        model = Cart
        fields = ['id', 'user', 'created_at', 'updated_at', 'items','grand_total']
    
    def main_total(self,cart:Cart):
        items = cart.items.all()
        total = sum([item.quantity * item.flower.price for item in items])
        return total

class AddCartItemSerializer(serializers.ModelSerializer):
    flower_id = serializers.IntegerField()
    quantity = serializers.IntegerField(default=1)

    def save(self, **kwargs):
        cart_id = self.context["cart_id"]
        flower_id = self.validated_data["flower_id"]
        quantity = self.validated_data["quantity"]

        try:
            flower = Flower.objects.get(id=flower_id)
            cart = Cart.objects.get(id=cart_id)
        except ObjectDoesNotExist:
            raise serializers.ValidationError("Invalid cart or flower ID.")

        if flower.stock < quantity:
            raise serializers.ValidationError("Not enough stock available for this item.")

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            flower=flower,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
            
        flower.stock -= quantity
        flower.save()
        cart.save()
        
        self.instance = cart_item
        return self.instance

    class Meta:
        model = CartItem
        fields = ["id", "flower_id", "quantity"]

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

        # Check if the quantity is being increased or decreased
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
        
        cart_item.cart.save()
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

