from django.db import models
from user.models import Account
from flowers.models import Flower
from decimal import Decimal
from datetime import datetime
import uuid

class Cart(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    #discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    def __str__(self):
        return f"Cart ({self.id}) for {self.user.user.username} - {self.items.count()} items, Total: ${self.grand_total}, (Active: {self.is_active})"
    
    def calculate_grand_total(self, delta=None):
        self.grand_total = Decimal(self.grand_total)
        if delta is not None:
            self.grand_total += Decimal(delta)
        else:
            total = sum(Decimal(item.get_total()) for item in self.items.all())
            self.grand_total = total
        self.save(update_fields=["grand_total"])
        
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE,null=True)
    flower = models.ForeignKey(Flower, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    cart_image = models.ImageField(upload_to='cart_images/', null=True, blank=True)
    price_at_added = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    def get_total(self):
        return self.quantity * (self.price_at_added or self.flower.price)
    
    def save(self, *args, **kwargs):
        if not self.price_at_added:
            self.price_at_added = self.flower.price

        if self.quantity > self.flower.stock:
            raise ValueError(f"Not enough stock for {self.flower.flower_name}. Only {self.flower.stock} available.")

        self.subtotal = self.quantity * self.price_at_added

        is_new = self.pk is None
        if is_new:
            delta = self.get_total()
        else:
            old_quantity = CartItem.objects.get(pk=self.pk).quantity
            delta = (self.quantity - old_quantity) * self.price_at_added
        super().save(*args, **kwargs)

        self.cart.calculate_grand_total(delta=delta)

    def delete(self, *args, **kwargs):
        delta = -self.get_total()
        super().delete(*args, **kwargs)

        self.cart.calculate_grand_total(delta=delta)

    def __str__(self):
        return f"{self.quantity}x {self.flower.flower_name} (${self.subtotal}) in Cart ({self.cart.id})"

class Order(models.Model):
    ORDER_STATUS = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
        ('Failed', 'Failed'),
    ]
    
    PAYMENT_STATUS = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Failed', 'Failed'),
        ('Refunded', 'Refunded'),
    ]

    user = models.ForeignKey(Account, on_delete=models.CASCADE, blank=True, null=True)
    placed_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=ORDER_STATUS, default="Pending")
    payment_status = models.CharField(max_length=50, choices=PAYMENT_STATUS, default="Pending")
    shipping_address = models.TextField(default="Not Provided")
    transaction_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    total_amount = models.DecimalField(
        max_digits=10, verbose_name='Total amount of order', decimal_places=2, default=0
    )
    cart = models.ForeignKey('Cart', on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-placed_time']

    def calculate_total_amount(self):
        if not self.items.exists():
            return
        self.total_amount = sum(item.get_total() for item in self.items.all())
        self.save(update_fields=["total_amount"])

    def transfer_cart_to_order_items(self):
        if not self.cart:
            return

        for cart_item in self.cart.items.all():
            OrderItem.objects.create(
                order=self,
                flower=cart_item.flower,
                quantity=cart_item.quantity,
                price_at_order_time=cart_item.flower.price
            )

    def save(self, *args, **kwargs):
        """
        Override the save method to generate a custom transaction ID, ensure total amount is calculated,
        and deactivate the related cart after the order is placed.
        """
        is_new = self.pk is None
        
        if is_new and not self.transaction_id:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            unique_part = uuid.uuid4().hex[:6].upper()
            self.transaction_id = f"TXN-{timestamp}-{unique_part}"

        super().save(*args, **kwargs)
        if is_new and self.cart:
            self.transfer_cart_to_order_items()
            self.cart.is_active = False
            self.cart.save()

        if self.items.exists():
            self.total_amount = sum(item.get_total() for item in self.items.all())
            super().save(update_fields=["total_amount"])

    def __str__(self):
        return f"Order {self.id} for {self.user.user.username} - Status: {self.status}, Total: ${self.total_amount}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    flower = models.ForeignKey(Flower, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price_at_order_time = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def get_total(self):
        return self.quantity * self.price_at_order_time

    def save(self, *args, **kwargs):
        if not self.price_at_order_time:
            self.price_at_order_time = self.flower.price

        self.subtotal = self.get_total()
        super().save(*args, **kwargs)
        self.order.calculate_total_amount()

    def __str__(self):
        return f"{self.quantity}x {self.flower.flower_name} (${self.subtotal}) in Order ({self.order.id})"
