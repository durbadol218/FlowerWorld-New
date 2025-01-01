from rest_framework import viewsets
from .models import Flower, FlowerCategory
from .serializers import FlowerSerializer, FlowerCategorySerializer
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView

class FlowerViewSet(viewsets.ModelViewSet):
    queryset = Flower.objects.all()
    serializer_class = FlowerSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        category_id = self.request.query_params.get('category_id')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset

    @action(detail=False, methods=['get'], url_path='category/(?P<category_id>\d+)')
    def list_by_category(self, request, category_id=None):
        queryset = Flower.objects.filter(category_id=category_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = FlowerCategory.objects.all()
    serializer_class = FlowerCategorySerializer

class CountFlowersAndCategoriesView(APIView):
    def get(self, request, *args, **kwargs):
        total_flowers = Flower.objects.count()
        total_categories = FlowerCategory.objects.count()
        
        return Response({
            'total_flowers': total_flowers,
            'total_categories': total_categories
        })