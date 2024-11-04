from django.db import models
from user.models import Account
from flowers.models import Flower

class Cart(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.user.username}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Call the original save method

        # Update total amount in the related order (if exists)
        if hasattr(self, 'order') and self.order is not None:
            self.order.calculate_total_amount()  # Recalculate total amount for the order
            
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items',on_delete=models.CASCADE)
    flower = models.ForeignKey(Flower,on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    def get_total(self):
        return self.quantity * self.flower.price
    
    def __str__(self):
        return f"{self.flower.flower_name} in {self.cart.user.user.username}'s cart."
    
    
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
