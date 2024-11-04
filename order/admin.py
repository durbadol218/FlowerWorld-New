# # from django.contrib import admin
# # from .models import Order
# # from flowers.models import Flower

# # class OrderAdmin(admin.ModelAdmin):
# #     list_display = ('id', 'user', 'placed_time', 'status', 'flower', 'quantity', 'total_amount')
# #     list_filter = ('status', 'placed_time')
# #     search_fields = ('user__username', 'flower__flower_name')

# # admin.site.register(Order, OrderAdmin)
# from django.contrib import admin
# from .models import Order, Cart, CartItem
# from flowers.models import Flower

# # Order Admin Configuration
# class OrderAdmin(admin.ModelAdmin):
#     list_display = ('id', 'user', 'placed_time', 'status', 'get_quantity', 'total_amount')
#     list_filter = ('status', 'placed_time')
#     search_fields = ('user__username', 'flower__flower_name')

#     # Custom method to display quantity
#     def get_quantity(self, obj):
#         # If the Order has an associated quantity field, use that. Otherwise, implement the logic to calculate it.
#         return obj.quantity if hasattr(obj, 'quantity') else 'N/A'
#     get_quantity.short_description = 'Quantity'

# admin.site.register(Order, OrderAdmin)

# # Inline CartItem for displaying within Cart
# class CartItemInline(admin.TabularInline):
#     model = CartItem
#     extra = 1  # Number of extra empty fields for new items in the cart

# # Cart Admin Configuration
# class CartAdmin(admin.ModelAdmin):
#     list_display = ('id', 'user', 'created_at', 'updated_at')
#     list_filter = ('created_at', 'updated_at')
#     search_fields = ('user__username',)
#     inlines = [CartItemInline]  # Include CartItems inside the Cart admin

# admin.site.register(Cart, CartAdmin)

# # CartItem Admin Configuration
# class CartItemAdmin(admin.ModelAdmin):
#     list_display = ('id', 'cart', 'get_flower_name', 'quantity')
#     list_filter = ('cart__created_at', 'cart__updated_at')
#     search_fields = ('flower__flower_name',)

#     def get_flower_name(self, obj):
#         return obj.flower.flower_name if obj.flower else None
#     get_flower_name.short_description = 'Flower Name'

# admin.site.register(CartItem, CartItemAdmin)

#Before modified
# from django.contrib import admin
# from .models import Order, OrderItem, Cart, CartItem
# from flowers.models import Flower

# # Cart Admin Configuration
# class CartItemInline(admin.TabularInline):
#     model = CartItem
#     extra = 1  # Number of empty forms to display

# class CartAdmin(admin.ModelAdmin):
#     list_display = ('user', 'created_at', 'updated_at')
#     inlines = [CartItemInline]

# admin.site.register(Cart, CartAdmin)

# # Order Admin Configuration
# class OrderItemInline(admin.TabularInline):
#     model = OrderItem
#     extra = 1  # Number of empty forms to display

# class OrderAdmin(admin.ModelAdmin):
#     list_display = ('id', 'user', 'placed_time', 'status', 'total_amount')
#     list_filter = ('status', 'placed_time')
#     search_fields = ('user__username',)

#     # Inline order items
#     inlines = [OrderItemInline]

#     def save_model(self, request, obj, change):
#         super().save_model(request, obj, change)
#         obj.calculate_total_amount()  # Ensure the total amount is calculated and saved

# admin.site.register(Order, OrderAdmin)

# # Order Item Admin Configuration
# class OrderItemAdmin(admin.ModelAdmin):
#     list_display = ('order', 'flower', 'quantity', 'get_total_price')
#     list_filter = ('order', 'flower')
    
#     def get_total_price(self, obj):
#         return obj.get_total()
#     get_total_price.short_description = 'Total Price'

# admin.site.register(OrderItem, OrderItemAdmin)

# # Cart Item Admin Configuration
# class CartItemAdmin(admin.ModelAdmin):
#     list_display = ('cart', 'flower', 'quantity', 'get_total_price')
#     list_filter = ('cart', 'flower')
    
#     def get_total_price(self, obj):
#         return obj.get_total()
#     get_total_price.short_description = 'Total Price'

# admin.site.register(CartItem, CartItemAdmin)





# from django.contrib import admin
# from .models import Order, OrderItem, Cart, CartItem
# from flowers.models import Flower

# # Cart Admin Configuration
# class CartItemInline(admin.TabularInline):
#     model = CartItem
#     extra = 1  # Number of empty forms to display

# class CartAdmin(admin.ModelAdmin):
#     list_display = ('user', 'created_at', 'updated_at')
#     inlines = [CartItemInline]

# admin.site.register(Cart, CartAdmin)

# # Order Admin Configuration
# class OrderItemInline(admin.TabularInline):
#     model = OrderItem
#     extra = 1  # Number of empty forms to display

# class OrderAdmin(admin.ModelAdmin):
#     inlines = [OrderItemInline]  # Include OrderItem inline in Order admin
#     list_display = ('id', 'user', 'placed_time', 'status', 'total_amount')  # Customize list display

#     def save_model(self, request, obj, form, change):
#         super().save_model(request, obj, form, change)  # Call the superclass's save_model
#         obj.calculate_total_amount()  # Ensure the total amount is calculated and saved

# admin.site.register(Order, OrderAdmin)

# # Cart Item Admin Configuration
# class CartItemAdmin(admin.ModelAdmin):
#     list_display = ('cart', 'flower', 'quantity', 'get_total_price')
#     list_filter = ('cart', 'flower')
    
#     def get_total_price(self, obj):
#         return obj.get_total()
#     get_total_price.short_description = 'Total Price'

# admin.site.register(CartItem, CartItemAdmin)




#OLD VERSION
# from django.contrib import admin
# from .models import Order, OrderItem, Cart, CartItem

# # Inline Cart Items for Cart Admin
# class CartItemInline(admin.TabularInline):
#     model = CartItem
#     extra = 0  # No extra empty forms unless you want to allow adding new items directly

# class CartAdmin(admin.ModelAdmin):
#     list_display = ('user', 'created_at', 'updated_at')
#     inlines = [CartItemInline]

# admin.site.register(Cart, CartAdmin)

# # Inline Order Items for Order Admin
# class OrderItemInline(admin.TabularInline):
#     model = OrderItem
#     extra = 0  # No extra empty forms unless required

# class OrderAdmin(admin.ModelAdmin):
#     inlines = [OrderItemInline]  # Include OrderItem inline in Order admin
#     list_display = ('id', 'user', 'placed_time', 'status', 'total_amount')
    
#     # Override save_related to ensure OrderItems are saved before calculating total
#     def save_related(self, request, form, formsets, change):
#         super().save_related(request, form, formsets, change)
#         form.instance.calculate_total_amount()  # Recalculate total after related items are saved

# admin.site.register(Order, OrderAdmin)

# # Cart Item Admin
# class CartItemAdmin(admin.ModelAdmin):
#     list_display = ('cart', 'flower', 'quantity', 'get_total_price')
#     list_filter = ('cart', 'flower')
    
#     def get_total_price(self, obj):
#         return obj.get_total()  # Ensure that CartItem model has a get_total method
#     get_total_price.short_description = 'Total Price'

# admin.site.register(CartItem, CartItemAdmin)

# # You may want to register OrderItem directly as well (optional)
# class OrderItemAdmin(admin.ModelAdmin):
#     list_display = ('order', 'flower', 'quantity', 'get_total_price')

#     def get_total_price(self, obj):
#         return obj.get_total()
#     get_total_price.short_description = 'Total Price'

# admin.site.register(OrderItem, OrderItemAdmin)



from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0  # Number of empty forms to display in the inline formset

class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'updated_at')
    search_fields = ('user__username',)  # Assuming Account model has a User FK
    inlines = [CartItemInline]

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'placed_time', 'status', 'total_amount')
    list_filter = ('status',)
    search_fields = ('user__username', 'total_amount')  # Assuming Account model has a User FK
    inlines = [OrderItemInline]

# Register your models here
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)









#After modifying
# from django.contrib import admin
# from .models import Order, Cart, CartItem
# from flowers.models import Flower

# # Cart Admin Configuration
# class CartItemInline(admin.TabularInline):
#     model = CartItem
#     extra = 1  # Number of empty forms to display

# class CartAdmin(admin.ModelAdmin):
#     list_display = ('user', 'created_at', 'updated_at')
#     inlines = [CartItemInline]

# admin.site.register(Cart, CartAdmin)

# # Order Admin Configuration
# class OrderAdmin(admin.ModelAdmin):
#     list_display = ('id', 'user', 'placed_time', 'status', 'total_amount')
#     list_filter = ('status', 'placed_time')
#     search_fields = ('user__username',)

#     def save_model(self, request, obj, change):
#         super().save_model(request, obj, change)
#         obj.calculate_total_amount()  # Ensure the total amount is calculated and saved

# admin.site.register(Order, OrderAdmin)

# # Cart Item Admin Configuration
# class CartItemAdmin(admin.ModelAdmin):
#     list_display = ('cart', 'flower', 'quantity', 'get_total_price')
#     list_filter = ('cart', 'flower')
    
#     def get_total_price(self, obj):
#         return obj.get_total()  # Assuming get_total() is a method in your CartItem model
#     get_total_price.short_description = 'Total Price'

# admin.site.register(CartItem, CartItemAdmin)