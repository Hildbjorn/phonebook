from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
import pandas as pd
from .models import Employee, ImportLog

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
        # Получаем уникальные подразделения из всех четырех полей
        departments = set()
        for emp in Employee.objects.all():
            for dept in [emp.department1, emp.department2, emp.department3, emp.department4]:
                if dept:
                    departments.add(dept)
        return [(dept, dept) for dept in sorted(departments)]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(
                Q(department1=self.value()) |
                Q(department2=self.value()) |
                Q(department3=self.value()) |
                Q(department4=self.value())
            )
        return queryset

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = [
        'full_name',
        'position',
        'department_display',
        'phone',
        'internal_phone',
        'room',
        'hierarchy_display',
        'created_at'
    ]

    list_filter = [
        HierarchyFilter,
        DepartmentFilter,
        'created_at',
    ]

    search_fields = [
        'full_name',
        'position',
        'department1',
        'department2',
        'department3',
        'department4',
        'phone',
        'internal_phone',
        'room',
        'email'
    ]

    readonly_fields = ['created_at', 'updated_at', 'employee_link']

    fieldsets = (
        ('Основная информация', {
            'fields': ('full_name', 'initials', 'position', 'hierarchy')
        }),
        ('Контакты', {
            'fields': ('phone', 'internal_phone', 'email', 'room')
        }),
        ('Подразделения', {
            'fields': ('department1', 'department2', 'department3', 'department4'),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at', 'employee_link'),
            'classes': ('collapse',)
        }),
    )

    actions = ['export_to_excel', 'export_to_csv']

    def department_display(self, obj):
        departments = [obj.department1, obj.department2, obj.department3, obj.department4]
        departments = [dept for dept in departments if dept]
        return " → ".join(departments) if departments else "-"
    department_display.short_description = 'Подразделение'

    def hierarchy_display(self, obj):
        return obj.get_hierarchy_display()
    hierarchy_display.short_description = 'Уровень'

    def employee_link(self, obj):
        url = reverse('admin:employees_employee_change', args=[obj.id])
        return format_html('<a href="{}">Редактировать сотрудника</a>', url)
    employee_link.short_description = 'Ссылка'

    def export_to_excel(self, request, queryset):
        try:
            data = []
            for employee in queryset:
                data.append({
                    'Инициалы': employee.initials,
                    'ФИО': employee.full_name,
                    'Должность': employee.position,
                    'Подразделение 1': employee.department1,
                    'Подразделение 2': employee.department2,
                    'Подразделение 3': employee.department3,
                    'Подразделение 4': employee.department4,
                    'Телефон': employee.phone,
                    'Внутренний телефон': employee.internal_phone,
                    'Email': employee.email,
                    'Кабинет': employee.room,
                    'Уровень': employee.hierarchy,
                    'Дата создания': employee.created_at,
                })

            df = pd.DataFrame(data)
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename=employees_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'

            df.to_excel(response, index=False, engine='openpyxl')
            return response

        except Exception as e:
            self.message_user(request, f'Ошибка при экспорте: {str(e)}', messages.ERROR)

    def export_to_csv(self, request, queryset):
        try:
            data = []
            for employee in queryset:
                data.append({
                    'Инициалы': employee.initials,
                    'ФИО': employee.full_name,
                    'Должность': employee.position,
                    'Подразделение 1': employee.department1,
                    'Подразделение 2': employee.department2,
                    'Подразделение 3': employee.department3,
                    'Подразделение 4': employee.department4,
                    'Телефон': employee.phone,
                    'Внутренний телефон': employee.internal_phone,
                    'Email': employee.email,
                    'Кабинет': employee.room,
                    'Уровень': employee.hierarchy,
                    'Дата создания': employee.created_at,
                })

            df = pd.DataFrame(data)
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename=employees_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv'

            df.to_csv(response, index=False, encoding='utf-8-sig')
            return response

        except Exception as e:
            self.message_user(request, f'Ошибка при экспорте: {str(e)}', messages.ERROR)

    export_to_excel.short_description = "Экспорт выбранных в Excel"
    export_to_csv.short_description = "Экспорт выбранных в CSV"

@admin.register(ImportLog)
class ImportLogAdmin(admin.ModelAdmin):
    list_display = [
        'file_name',
        'uploaded_at',
        'status_display',
        'total_records',
        'added',
        'updated',
        'user_display',
        'errors_short'
    ]

    list_filter = [
        'status',
        'uploaded_at',
        'user'
    ]

    search_fields = ['file_name', 'errors']

    readonly_fields = [
        'file_name',
        'uploaded_at',
        'status',
        'total_records',
        'added',
        'updated',
        'errors_display',
        'user',
        'import_details'
    ]

    fieldsets = (
        ('Основная информация', {
            'fields': ('file_name', 'uploaded_at', 'status', 'user')
        }),
        ('Статистика импорта', {
            'fields': ('total_records', 'added', 'updated')
        }),
        ('Ошибки', {
            'fields': ('errors_display',),
            'classes': ('collapse',)
        }),
        ('Детали', {
            'fields': ('import_details',),
            'classes': ('collapse',)
        }),
    )

    def status_display(self, obj):
        color = {
            'success': 'green',
            'partial': 'orange',
            'failed': 'red'
        }.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Статус'

    def user_display(self, obj):
        return obj.user.username if obj.user else 'Система'
    user_display.short_description = 'Пользователь'

    def errors_short(self, obj):
        if obj.errors:
            return obj.errors[:50] + '...' if len(obj.errors) > 50 else obj.errors
        return '-'
    errors_short.short_description = 'Ошибки (кратко)'

    def errors_display(self, obj):
        if obj.errors:
            return format_html('<pre style="background: #f5f5f5; padding: 10px; border-radius: 5px;">{}</pre>', obj.errors)
        return 'Ошибок нет'
    errors_display.short_description = 'Ошибки'

    def import_details(self, obj):
        success_rate = (obj.added + obj.updated) / obj.total_records * 100 if obj.total_records > 0 else 0
        return format_html("""
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
                <h4>Детали импорта</h4>
                <p><strong>Общее количество записей:</strong> {}</p>
                <p><strong>Добавлено новых:</strong> {}</p>
                <p><strong>Обновлено существующих:</strong> {}</p>
                <p><strong>Процент успеха:</strong> {:.1f}%</p>
                <p><strong>Ошибок:</strong> {}</p>
            </div>
        """, obj.total_records, obj.added, obj.updated, success_rate, len(obj.errors.split('\n')) if obj.errors else 0)
    import_details.short_description = 'Детали импорта'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

# Кастомная главная страница админки
class CustomAdminSite(admin.AdminSite):
    site_header = 'Панель управления телефонным справочником'
    site_title = 'Телефонный справочник'
    index_title = 'Управление данными'

    def get_app_list(self, request):
        app_list = super().get_app_list(request)
        # Перемещаем приложение employees на первое место
        for app in app_list:
            if app['app_label'] == 'employees':
                app_list.remove(app)
                app_list.insert(0, app)
                break
        return app_list

# Заменяем стандартную админку на кастомную
admin_site = CustomAdminSite(name='custom_admin')

# Регистрируем модели в кастомной админке
admin_site.register(Employee, EmployeeAdmin)
admin_site.register(ImportLog, ImportLogAdmin)
