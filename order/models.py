from django.db import models
from user.models import Account
from flowers.models import Flower
from decimal import Decimal

class Cart(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    #discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # def __str__(self):
    #     return f"Cart for {self.user.user.username}"
    def __str__(self):
        return f"Cart ({self.id}) for {self.user.user.username} - {self.items.count()} items, Total: ${self.grand_total}, (Active: {self.is_active})"

    # def calculate_grand_total(self):
    #     total = sum(item.get_total() for item in self.items.all())
    #     self.grand_total = total
    #     self.save(update_fields=["grand_total"])
    def calculate_grand_total(self, delta=None):
        self.grand_total = Decimal(self.grand_total)
        if delta is not None:
            self.grand_total += Decimal(delta)
        else:
            total = sum(Decimal(item.get_total()) for item in self.items.all())
            self.grand_total = total
        self.save(update_fields=["grand_total"])
    
    def clear_cart(self):
        self.items.all().delete()
        self.calculate_grand_total()
        
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
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
    user = models.ForeignKey(Account,on_delete=models.CASCADE,blank=True,null=True)
    placed_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=ORDER_STATUS, default="Pending")
    total_amount = models.FloatField(verbose_name='Total amount of order', default=0)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, blank=True, null=True)
    
    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-placed_time']
    
    def calculate_total_amount(self):
        if self.cart and self.cart.items.exists():
            self.total_amount = sum(item.get_total() for item in self.cart.items.all())
        elif self.order_items_relation.exists():
            self.total_amount = sum(item.get_total() for item in self.order_items_relation.all())
        else:
            self.total_amount = 0
        self.save()


class OrderItem(models.Model):
    order = models.ForeignKey(Order,related_name = 'order_items_relation', on_delete=models.CASCADE)
    # order = models.ForeignKey(Order,related_name = 'items', on_delete=models.CASCADE)
    flower = models.ForeignKey(Flower, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    def get_total(self):
        return self.quantity * self.flower.price
    
    def __str__(self):
        return f"{self.flower.flower_name} in Order {self.order.id}"
