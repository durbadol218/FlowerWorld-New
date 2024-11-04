from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FlowerViewSet, CategoryViewSet, CountFlowersAndCategoriesView

router = DefaultRouter()
router.register(r'flowers', FlowerViewSet, basename='flower')
router.register(r'categories', CategoryViewSet, basename='category')

urlpatterns = [
    path('', include(router.urls)),
    path('flower/count/', CountFlowersAndCategoriesView.as_view(), name='flowers-count'),  # Ensure this line is included
]
