from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, CartViewSet, CartItemViewSet
from rest_framework_nested import routers

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'carts', CartViewSet, basename='cart')

cart_router = routers.NestedDefaultRouter(router,r'carts',lookup="cart")
cart_router.register(r'items', CartItemViewSet, basename='cartItems')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(cart_router.urls)),
]



