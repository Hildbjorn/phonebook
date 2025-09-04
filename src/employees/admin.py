from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from .models import Department, Employee, ImportLog

@admin.register(Department)
class DepartmentAdmin(MPTTModelAdmin):
    list_display = ['name', 'parent', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name']
    mptt_level_indent = 20

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'position', 'department', 'phone', 'hierarchy']
    list_filter = ['department', 'hierarchy', 'created_at']
    search_fields = ['full_name', 'position', 'phone']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = [
        ('Основная информация', {
            'fields': ['initials', 'full_name', 'position', 'department', 'hierarchy']
        }),
        ('Контактная информация', {
            'fields': ['phone', 'internal_phone', 'email', 'room']
        }),
        ('Системная информация', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

@admin.register(ImportLog)
class ImportLogAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'uploaded_at', 'status', 'total_records', 'added', 'updated']
    list_filter = ['status', 'uploaded_at']
    readonly_fields = ['uploaded_at']
    fieldsets = [
        ('Основная информация', {
            'fields': ['file_name', 'uploaded_at', 'status', 'user']
        }),
        ('Статистика', {
            'fields': ['total_records', 'added', 'updated']
        }),
        ('Ошибки', {
            'fields': ['errors'],
            'classes': ['collapse']
        }),
    ]