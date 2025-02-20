from rest_framework import serializers
from . import models
from django.contrib.auth.models import User
from .constants import USER_TYPE
from rest_framework import serializers
from .models import Account



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','username', 'first_name', 'last_name', 'email', 'account']
        
class AccountSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = models.Account
        # fields = ['user', 'user_type', 'phone', 'image_url']
        fields = ['user', 'user_type', 'phone', 'image_url']
        
class UserRegisterSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(required=True)
    phone = serializers.CharField(required=True)
    user_type = serializers.ChoiceField(choices=USER_TYPE, required=True)
    # image = serializers.ImageField(required=False, allow_null=True)
    # image_url = serializers.URLField(required=False, allow_null=True)
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'confirm_password', 'user_type', 'phone']


    def save(self):
        username = self.validated_data['username']
        first_name = self.validated_data['first_name']
        last_name = self.validated_data['last_name']
        email = self.validated_data['email']
        password = self.validated_data['password']
        password2 = self.validated_data['confirm_password']
        user_type = self.validated_data['user_type']
        phone = self.validated_data['phone']
        # image_url = self.validated_data.get('image_url', '')
        # image = self.validated_data.get('image')
        
        print("phone:", phone)
        # print("image_url:", image_url)
        
        if password != password2:
            raise serializers.ValidationError({'error': "Password Doesn't Matched"})
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({'error': "Email Already Exists"})
        
        
        user = User(username=username, email=email,first_name=first_name,last_name=last_name)
        print(user)
        user.set_password(password)
        user.is_active = False
        user.save()
        
        # account = models.Account.objects.create(user=user, user_type=user_type)
        account = models.Account.objects.create(user=user, user_type=user_type, phone=phone)
        account.save()
        return user

class UserProfileUpdate(serializers.ModelSerializer):
    phone = serializers.CharField(source='account.phone', required=True)
    user_type = serializers.ChoiceField(source='account.user_type', choices=USER_TYPE, required=True)
    image_url = serializers.URLField(source='account.image_url', required=False)
    # image = serializers.ImageField(source='account.image', required=False)
    new_password = serializers.CharField(required=False, write_only=True)
    confirm_password = serializers.CharField(required=False, write_only=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'user_type', 'image_url', 'new_password', 'confirm_password']

    def update(self, instance, validated_data):
        account_data = validated_data.pop('account', {})
        instance.username = validated_data.get('username', instance.username)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        
        new_password = validated_data.get('new_password')
        confirm_password = validated_data.get('confirm_password')
        if new_password and new_password == confirm_password:
            instance.set_password(new_password)

        instance.save()
        
        account = instance.account
        account.phone = account_data.get('phone', account.phone)
        account.user_type = account_data.get('user_type', account.user_type)
        # account.image = account_data.get('image', account.image)
        account.image_url = account_data.get('image_url', account.image_url)
        account.save()

        return instance

class ChangePassword(serializers.Serializer):
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)
    
    def validate(self,attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("New password and confirm password do not match.")
        return attrs
    
    def update_password(self,user,validated_data):
        user.set_password(validated_data['new_password'])
        user.save()
        return user
    
    
    
# class AccountRegisterSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = models.Account
#         fields = ['user','image', 'phone', 'user_type']

#     def save(self):
#         user = self.validated_data['user']
#         phone = self.validated_data['phone']
#         image = self.validated_data['image']
#         user_type = self.validated_data['user_type']
#         account = models.Account(user=user, phone=phone, image=image, user_type=user_type)
#         account.save()
#         return account
    


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    

# class UserProfileUpdate(serializers.Serializer):
#     phone = serializers.CharField(source='account.phone', required=True)
#     user_type = serializers.ChoiceField(source='account.user_type', choices=USER_TYPE, required=True)
#     image = serializers.ImageField(source='account.image', required=False)
    
#     class Meta:
#         model = User
#         fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'user_type', 'image']
    
#     def update(self,instance,validated_data):
#         account_data = validated_data.pop('account',{})
#         instance.username = validated_data.get('username', instance.username)
#         instance.first_name = validated_data.get('first_name', instance.first_name)
#         instance.last_name = validated_data.get('last_name', instance.last_name)
#         instance.email = validated_data.get('email', instance.email)
#         instance.save()
        
#         account = instance.account
#         account.phone = account_data.get('phone', account.phone)
#         account.user_type = account_data.get('user_type', account.user_type)
#         account.image = account_data.get('image', account.image)
#         account.save()

#         return instance
    
    