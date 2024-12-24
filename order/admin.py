from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0  # Number of empty forms to display in the inline formset
    fields = ('flower', 'quantity')  # Customize fields as per your model

class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'updated_at', 'grand_total')  # Include grand_total if you have it
    search_fields = ('user__username', 'user__email')  # Adding email to search
    list_filter = ('user', 'created_at')  # Filters for user and created_at
    inlines = [CartItemInline]
    readonly_fields = ('grand_total',)  # If grand_total is a calculated field
    
    def save_model(self, request, obj, form, change):
        # Ensure that the Cart is saved first before adding CartItem
        obj.save()  # Save the Cart first to generate a primary key
        super().save_model(request, obj, form, change)

# class OrderItemInline(admin.TabularInline):
#     model = OrderItem
#     extra = 0
#     fields = ('flower', 'quantity')  # Customize fields as per your model

# class OrderAdmin(admin.ModelAdmin):
#     list_display = ('id', 'user', 'placed_time', 'status', 'total_amount')  # Modify to suit your model
#     list_filter = ('status', 'placed_time')  # Filter by status and placed_time
#     search_fields = ('user__username', 'user__email', 'total_amount')  # Add email for easier search
#     inlines = [OrderItemInline]
#     readonly_fields = ('total_amount',)  # If total_amount is calculated

#     def save_model(self, request, obj, form, change):
#         # Ensure that the Order is saved first before adding OrderItem
#         obj.save()  # Save the Order first to generate a primary key
#         super().save_model(request, obj, form, change)

# # Register your models here
# admin.site.register(Cart, CartAdmin)
# admin.site.register(CartItem)
# admin.site.register(Order, OrderAdmin)
# admin.site.register(OrderItem)



from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem

# # Inline model for Cart Items
# class CartItemInline(admin.TabularInline):
#     model = CartItem
#     extra = 0
#     fields = ('flower', 'quantity')
#     readonly_fields = ('flower_name',)

#     def flower_name(self, obj):
#         return obj.flower.flower_name if obj.flower else 'No flower selected'

#     flower_name.short_description = 'Flower Name'


# # Admin for Cart
# class CartAdmin(admin.ModelAdmin):
#     list_display = ('id', 'user', 'created_at', 'updated_at', 'grand_total')
#     search_fields = ('user__username', 'user__email')
#     list_filter = ('user', 'created_at')
#     inlines = [CartItemInline]
#     readonly_fields = ('grand_total',)

#     def save_model(self, request, obj, form, change):
#         obj.save()
#         obj.grand_total = sum(item.quantity * item.flower.price for item in obj.cartitem_set.all())
#         super().save_model(request, obj, form, change)


from django.contrib import admin
from django.db import transaction
from .models import Order, OrderItem


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
        """
        Save the Order instance first to generate the primary key.
        """
        if not obj.pk:
            obj.save()  # Save the parent Order instance to assign a primary key
            print(f"Order saved with PK: {obj.pk}")  # Debugging statement

        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        """
        Save related OrderItem instances only after the parent Order is saved.
        """
        # Ensure all changes are wrapped in a transaction
        with transaction.atomic():
            print(f"Saving related objects for Order PK: {form.instance.pk}")  # Debugging statement
            super().save_related(request, form, formsets, change)


# Register your models
admin.site.register(Order, OrderAdmin)

# Register your models with the admin site
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem)
admin.site.register(OrderItem)

