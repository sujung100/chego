from django.contrib import admin

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from . import models
# Register your models here.

class ProfileInline(admin.StackedInline):
    model = models.Manager
    can_delete = False
    verbose_name_plural = 'Manager Profiles'

class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)



admin.site.unregister(User)
admin.site.register(User, UserAdmin)