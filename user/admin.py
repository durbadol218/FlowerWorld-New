from django.contrib import admin
from .models import Account, ContactMessage

class AccountAdmin(admin.ModelAdmin):
    list_display = ['get_first_name','get_last_name','phone','user_type']
    
    def get_first_name(self,obj):
        return obj.user.first_name
    
    def get_last_name(self,obj):
        return obj.user.last_name
admin.site.register(Account,AccountAdmin)
admin.site.register(ContactMessage)