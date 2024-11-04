from rest_framework import serializers
from .models import Flower, FlowerCategory

class FlowerCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FlowerCategory
        fields = ['id','name']


class SimpleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flower
        fields = ["id","flower_name", "price"]
        
        

class FlowerSerializer(serializers.ModelSerializer):
    category = FlowerCategorySerializer(read_only=True) 
    category_id = serializers.PrimaryKeyRelatedField(queryset=FlowerCategory.objects.all(), required=False, allow_null=True)
    class Meta:
        model = Flower
        fields = ['id', 'flower_name', 'description', 'price', 'image', 'category', 'category_id', 'stock']
        
    def validate_category(self, value):
        if value and not FlowerCategory.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Category does not exist.")
        return value
# class ReviewSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ReviewModel
#         fields = ["id","date_created","name","description"]
        
#     def create(self,validated_data):
#         product_id = self.context['id']
#         return ReviewModel.objects.create(product_id=id,**validated_data)
