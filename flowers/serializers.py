from rest_framework import serializers
from .models import Flower, FlowerCategory
from django.utils.text import slugify

# class FlowerCategorySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = FlowerCategory
#         fields = ['id','name']


class FlowerCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FlowerCategory
        fields = ['id', 'name', 'slug']
        extra_kwargs = {
            'slug': {'required': False}  # Make slug optional in API requests
        }

    def create(self, validated_data):
        if not validated_data.get('slug'):
            validated_data['slug'] = slugify(validated_data['name'])
        return super().create(validated_data)


class SimpleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flower
        fields = ["id","flower_name", "price"]
        
        

class FlowerSerializer(serializers.ModelSerializer):
    category = FlowerCategorySerializer(read_only=True) 
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=FlowerCategory.objects.all(),
        source='category'
    )
    # image_url = serializers.URLField(required=False, allow_blank=True)
    class Meta:
        model = Flower
        fields = ['id', 'flower_name', 'description', 'price', 'image_url', 'category', 'category_id', 'stock']
        
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
