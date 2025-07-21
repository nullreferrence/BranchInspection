from django.contrib import admin
from .models import Items, Branch, User  # ✅ Import your custom User model

@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['email', 'role', 'branch', 'is_staff', 'is_superuser']
    search_fields = ['email', 'role']
    list_filter = ['role', 'branch', 'division']
    autocomplete_fields = ['branch']  # optional if needed

@admin.register(Items)
class ItemsAdmin(admin.ModelAdmin):
    list_display = ['itemName', 'category']
    search_fields = ['itemName', 'category']
    list_filter = ['category']

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'division')
    list_filter = ('type', 'division')
    search_fields = ('name',)
    autocomplete_fields = ['fixed_auditor', 'fixed_manager', 'fixed_authorizer']
