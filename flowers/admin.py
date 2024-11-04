from django.contrib import admin
from .models import Flower, FlowerCategory

admin.site.register(Flower)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',),}
    
admin.site.register(FlowerCategory,CategoryAdmin)




# Lilies
# Sunflowers
# Tulips
# Orchids
# Daisies
# Hydrangeas
# Mixed Flowers