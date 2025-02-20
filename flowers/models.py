from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField

class FlowerCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100,unique=True)
    class Meta:
        verbose_name_plural = 'Categories'
    def __str__(self):
        return self.name

class Flower(models.Model):
    flower_name = models.CharField(max_length=150)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # image = CloudinaryField('image')
    # image = models.ImageField(upload_to='flowers/images/')
    image = models.FileField(upload_to='flowers_image')
    category = models.ForeignKey(FlowerCategory, related_name='flowers',on_delete=models.CASCADE,null=True)
    stock = models.IntegerField(default=0)
    
    def __str__(self):
        return self.flower_name


