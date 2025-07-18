from django.shortcuts import render, redirect
from rest_framework import viewsets,status
from . import models
from . import serializers
from rest_framework.views import APIView
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth import authenticate, login, logout
from rest_framework.authtoken.models import Token
from .serializers import ContactMessageSerializer
from django.core.mail import send_mail
from django.conf import settings
# from django.views.decorators.csrf import csrf_exempt
# from django.utils.decorators import method_decorator


class UserViewSet(viewsets.ModelViewSet):
    queryset = models.User.objects.all()
    serializer_class = serializers.UserSerializer
    
class AccountViewset(viewsets.ModelViewSet):
    queryset = models.Account.objects.all()
    serializer_class = serializers.AccountSerializer


class UserRegistrationApiView(APIView):
    serializer_class = serializers.UserRegisterSerializer
    
    # def post(self, request):
    #     if request.user.is_authenticated:
    #         return Response({"detail": "You are already logged in. Log out to create a new account."},status=status.HTTP_400_BAD_REQUEST)
    #     serializer = self.serializer_class(data=request.data) 
        
    #     if serializer.is_valid(): 
    #         user = serializer.save()
    #         print(user)
    #         token = default_token_generator.make_token(user)
    #         print("Token", token)
    #         uid = urlsafe_base64_encode(force_bytes(user.pk))
    #         print("uid",uid)
    #         confirm_link = f"https://flower-world.vercel.app/user/activate/{uid}/{token}"
            
    #         email_subject = "Confirmation Email for Activate Account"
    #         email_body = render_to_string('confirm_email.html', {'confirm_link':confirm_link})
    #         email = EmailMultiAlternatives(email_subject, '', to=[user.email])
    #         email.attach_alternative(email_body, 'text/html')
    #         email.send()
            
    #         return Response("Check Your Email For Confirmation")
        
    #     return Response(serializer.errors)
    
    def post(self, request):
        try:
            if request.user.is_authenticated:
                return Response(
                    {"detail": "You are already logged in. Log out to create a new account."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = self.serializer_class(data=request.data)

            if serializer.is_valid():
                user = serializer.save()
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                confirm_link = f"https://flowerworld-api.vercel.app/user/activate/{uid}/{token}"
                print(confirm_link)
                email_subject = "Confirmation Email for Activate Account"
                email_body = render_to_string('confirm_email.html', {'confirm_link': confirm_link})
                email = EmailMultiAlternatives(email_subject, '', to=[user.email])
                email.attach_alternative(email_body, 'text/html')
                email.send()

                return Response({"message": "Check your email for confirmation."}, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print("REGISTRATION EXCEPTION:", e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def activateAccount(request, uid64, token):
    try:
        uid = urlsafe_base64_decode(uid64).decode()
        user = User._default_manager.get(pk=uid)
    except(User.DoesNotExist):
        user=None
        
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return redirect('https://flower-world-modified.vercel.app/login.html')
    else:
        return redirect('https://flower-world-modified.vercel.app/register.html')


# @method_decorator(csrf_exempt, name='dispatch')
class UserLoginApiView(APIView):
    def post(self, request):
        serializer = serializers.UserLoginSerializer(data=self.request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user = authenticate(username=username, password=password)
            
            if user:
                token, created = Token.objects.get_or_create(user=user)
                account, created = models.Account.objects.get_or_create(user=user)
                print(account)
                print(f"Generated Token: {token.key}")
                login(request, user)
                return Response({'token':token.key, 'user_id': account.id})
            else:
                return  Response({'error':'Invalid Credential'})
        return Response(serializer.errors,status=400)

class UserProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        serializer = serializers.UserProfileUpdate(instance=user)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = serializers.UserProfileUpdate(instance=user, data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile updated successfully"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = serializers.ChangePassword(data=request.data)
        if serializer.is_valid():
            serializer.update_password(user, serializer.validated_data)
            user.save()
            return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

class UserLogoutApiView(APIView):
    def get(self, request):
        request.user.auth_token.delete()
        logout(request)
        return redirect('login')
    
class TotalUsersCountView(APIView):
    def get(self, request, *args, **kwargs):
        total_users = User.objects.count()
        return Response({'total_users': total_users})
    
    
class ContactMessageView(APIView):
    def post(self, request):
        serializer = ContactMessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()

            full_name = serializer.validated_data['full_name']
            email = serializer.validated_data['email']
            message = serializer.validated_data['message']

            subject = f"New Contact Message from {full_name}"
            email_message = f"Name: {full_name}\nEmail: {email}\n\nMessage:\n{message}"

            send_mail(
                subject,
                email_message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.CONTACT_RECEIVER_EMAIL],
                fail_silently=False,
            )

            return Response({"message": "Message sent successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)