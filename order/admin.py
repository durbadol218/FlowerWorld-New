from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem
from django.db import transaction

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ('flower', 'quantity')

class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'updated_at', 'grand_total')
    search_fields = ('user__username', 'user__email')
    list_filter = ('user', 'created_at')
    inlines = [CartItemInline]
    readonly_fields = ('grand_total',)
    
    def save_model(self, request, obj, form, change):
        obj.save()
        super().save_model(request, obj, form, change)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('flower', 'quantity', 'price_at_order_time')


class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'placed_time', 'status', 'total_amount')
    list_filter = ('status', 'placed_time')
    search_fields = ('user__username', 'user__email', 'total_amount')
    inlines = [OrderItemInline]
    readonly_fields = ('total_amount',)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.save()
            print(f"Order saved with PK: {obj.pk}")
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        with transaction.atomic():
            print(f"Saving related objects for Order PK: {form.instance.pk}")
            super().save_related(request, form, formsets, change)


admin.site.register(Order, OrderAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem)
admin.site.register(OrderItem)

