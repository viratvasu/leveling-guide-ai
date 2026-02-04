from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Company, User, LevellingGuide, LevellingGuideLog


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'address')
    ordering = ('-created_at',)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'company', 'current_role', 'is_active', 'is_staff')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'company')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'current_role')
    ordering = ('-date_joined',)
    
    # Add custom fields to the fieldsets
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('company', 'current_role', 'permissions')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('company', 'current_role', 'permissions')}),
    )


@admin.register(LevellingGuide)
class LevellingGuideAdmin(admin.ModelAdmin):
    list_display = ('id', 'company', 'uploaded_by', 'version', 'is_current_version', 'is_active', 'created_at')
    list_filter = ('is_active', 'is_current_version', 'company', 'created_at')
    search_fields = ('company__name', 'uploaded_by__username')
    ordering = ('-created_at',)
    raw_id_fields = ('company', 'uploaded_by')


@admin.register(LevellingGuideLog)
class LevellingGuideLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'levelling_guide', 'rating', 'updated_by', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('levelling_guide__company__name', 'updated_by__username', 'comment')
    ordering = ('-created_at',)
    raw_id_fields = ('levelling_guide', 'updated_by')
