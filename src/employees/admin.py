from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Employee, ImportLog, Department

class DepartmentChildrenFilter(admin.SimpleListFilter):
    """Фильтр для подразделений с дочерними элементами"""
    title = 'Имеет дочерние подразделения'
    parameter_name = 'has_children'

    def lookups(self, request, model_admin):
        return [('yes', 'Да'), ('no', 'Нет')]

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(children__isnull=False).distinct()
        elif self.value() == 'no':
            return queryset.filter(children__isnull=True)
        return queryset

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """Админка для подразделений"""
    list_display = ['name', 'short_name', 'parent', 'level', 'employee_count', 'children_count']
    list_filter = ['level', 'parent', DepartmentChildrenFilter]
    search_fields = ['name', 'short_name']
    ordering = ['level', 'name']
    readonly_fields = ['created_at', 'updated_at', 'full_path_display']

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

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """Админка для сотрудников"""
    list_display = ['full_name', 'position', 'department_display', 'phone', 'hierarchy_display']
    list_filter = ['hierarchy', 'department']
    search_fields = ['full_name', 'position', 'phone', 'email']
    readonly_fields = ['created_at', 'updated_at']

    def department_display(self, obj):
        if obj.department:
            return f"{obj.department.name} ({obj.department.short_name})" if obj.department.short_name else obj.department.name
        return "-"
    department_display.short_description = 'Подразделение'

    def hierarchy_display(self, obj):
        return obj.get_hierarchy_display()
    hierarchy_display.short_description = 'Уровень'

@admin.register(ImportLog)
class ImportLogAdmin(admin.ModelAdmin):
    """Админка для логов импорта"""
    list_display = ['file_name', 'uploaded_at', 'status_display', 'total_records', 'added', 'updated']
    list_filter = ['status', 'uploaded_at']
    readonly_fields = ['file_name', 'uploaded_at', 'status', 'total_records', 'added', 'updated', 'errors']

    def status_display(self, obj):
        colors = {'success': 'green', 'partial': 'orange', 'failed': 'red'}
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_display.short_description = 'Статус'