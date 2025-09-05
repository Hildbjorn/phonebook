from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
import pandas as pd
from .models import Employee, ImportLog, Department

class DepartmentChildrenFilter(admin.SimpleListFilter):
    title = 'Имеет дочерние подразделения'
    parameter_name = 'has_children'

    def lookups(self, request, model_admin):
        return [
            ('yes', 'Да'),
            ('no', 'Нет')
        ]

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(children__isnull=False).distinct()
        elif self.value() == 'no':
            return queryset.filter(children__isnull=True)
        return queryset

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'short_name', 'parent', 'level', 'employee_count', 'children_count']
    list_filter = ['level', 'parent', DepartmentChildrenFilter]
    search_fields = ['name', 'short_name']
    ordering = ['level', 'name']
    readonly_fields = ['created_at', 'updated_at', 'full_path_display']

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'short_name', 'parent', 'level')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at', 'full_path_display'),
            'classes': ('collapse',)
        }),
    )

    def employee_count(self, obj):
        count = obj.employee_set.count()
        url = reverse('admin:employees_employee_changelist') + f'?department__id__exact={obj.id}'
        return format_html('<a href="{}">{}</a>', url, count)
    employee_count.short_description = 'Кол-во сотрудников'

    def children_count(self, obj):
        count = obj.children.count()
        if count > 0:
            url = reverse('admin:employees_department_changelist') + f'?parent__id__exact={obj.id}'
            return format_html('<a href="{}">{}</a>', url, count)
        return count
    children_count.short_description = 'Дочерние подразделения'

    def full_path_display(self, obj):
        return obj.get_full_path()
    full_path_display.short_description = 'Полный путь'

    def get_queryset(self, request):
        return super().get_queryset().annotate(
            employee_count=Count('employee'),
            children_count=Count('children')
        )

class HierarchyFilter(admin.SimpleListFilter):
    title = 'Уровень иерархии'
    parameter_name = 'hierarchy'

    def lookups(self, request, model_admin):
        return Employee.HIERARCHY_LEVELS

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(hierarchy=self.value())
        return queryset

class DepartmentFilter(admin.SimpleListFilter):
    title = 'Подразделение'
    parameter_name = 'department'

    def lookups(self, request, model_admin):
        departments = Department.objects.all().order_by('level', 'name')
        return [(dept.id, f"{'→ ' * dept.level}{dept.name}") for dept in departments]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(department__id=self.value())
        return queryset

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'position', 'department_display', 'phone', 'hierarchy_display', 'created_at']
    list_filter = [HierarchyFilter, DepartmentFilter, 'created_at']
    search_fields = ['full_name', 'position', 'phone', 'internal_phone', 'email', 'department__name', 'department__short_name']
    readonly_fields = ['created_at', 'updated_at', 'department_path']
    ordering = ['department__level', 'hierarchy', 'full_name']

    fieldsets = (
        ('Основная информация', {
            'fields': ('full_name', 'initials', 'position', 'hierarchy')
        }),
        ('Контакты', {
            'fields': ('phone', 'internal_phone', 'email', 'room')
        }),
        ('Подразделение', {
            'fields': ('department', 'department_path')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def department_display(self, obj):
        if obj.department:
            if obj.department.short_name:
                return f"{obj.department.name} ({obj.department.short_name})"
            return obj.department.name
        return "-"
    department_display.short_description = 'Подразделение'
    department_display.admin_order_field = 'department__name'

    def hierarchy_display(self, obj):
        return obj.get_hierarchy_display()
    hierarchy_display.short_description = 'Уровень'
    hierarchy_display.admin_order_field = 'hierarchy'

    def department_path(self, obj):
        if obj.department:
            return obj.department.get_full_path()
        return "Не указано"
    department_path.short_description = 'Полный путь подразделения'

    def get_queryset(self, request):
        return super().get_queryset().select_related('department')

class ImportStatusFilter(admin.SimpleListFilter):
    title = 'Статус импорта'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return ImportLog.STATUS_CHOICES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset

@admin.register(ImportLog)
class ImportLogAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'uploaded_at', 'status_display', 'total_records', 'added', 'updated', 'user_display', 'has_errors']
    list_filter = [ImportStatusFilter, 'uploaded_at', 'user']
    search_fields = ['file_name', 'errors']
    readonly_fields = ['file_name', 'uploaded_at', 'status', 'total_records', 'added', 'updated', 'errors', 'user', 'error_details']
    ordering = ['-uploaded_at']

    fieldsets = (
        ('Основная информация', {
            'fields': ('file_name', 'uploaded_at', 'status', 'user')
        }),
        ('Статистика импорта', {
            'fields': ('total_records', 'added', 'updated')
        }),
        ('Ошибки', {
            'fields': ('errors', 'error_details'),
            'classes': ('collapse',)
        }),
    )

    def status_display(self, obj):
        colors = {
            'success': 'green',
            'partial': 'orange',
            'failed': 'red'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_display.short_description = 'Статус'

    def user_display(self, obj):
        return obj.user.username if obj.user else 'Система'
    user_display.short_description = 'Пользователь'

    def has_errors(self, obj):
        return bool(obj.errors)
    has_errors.boolean = True
    has_errors.short_description = 'Есть ошибки'

    def error_details(self, obj):
        if obj.errors:
            error_count = len(obj.errors.split('\n'))
            success_rate = ((obj.added + obj.updated) / obj.total_records * 100) if obj.total_records > 0 else 0

            return format_html("""
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
                    <h6>Детали импорта:</h6>
                    <p><strong>Общее количество записей:</strong> {}</p>
                    <p><strong>Успешно обработано:</strong> {} ({:.1f}%)</p>
                    <p><strong>Добавлено новых:</strong> {}</p>
                    <p><strong>Обновлено существующих:</strong> {}</p>
                    <p><strong>Количество ошибок:</strong> {}</p>
                </div>
            """, obj.total_records, obj.added + obj.updated, success_rate, obj.added, obj.updated, error_count)
        return "Ошибок нет"
    error_details.short_description = 'Детали импорта'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
