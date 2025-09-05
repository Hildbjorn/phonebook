# Файл: admin.py

```
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

```


-----

# Файл: apps.py

```
from django.apps import AppConfig


class EmployeesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'employees'

```


-----

# Файл: context_processors.py

```
from .models import Employee, ImportLog

def admin_stats(request):
    if request.path.startswith('/admin/'):
        return {
            'employees_count': Employee.objects.count(),
            'import_logs_count': ImportLog.objects.count(),
        }
    return {}

```


-----

# Файл: forms.py

```
from django import forms
from .models import Employee, Department

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = '__all__'
        widgets = {
            'initials': forms.TextInput(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'internal_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'room': forms.TextInput(attrs={'class': 'form-control'}),
            'hierarchy': forms.Select(attrs={'class': 'form-control'}),
        }

class ImportForm(forms.Form):
    excel_file = forms.FileField(
        label='Excel файл',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx'})
    )

class SearchForm(forms.Form):
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по ФИО, должности, отделам...'
        })
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(level=1),
        required=False,
        empty_label="Все подразделения",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    hierarchy = forms.ChoiceField(
        choices=[('', 'Все уровни')] + list(Employee.HIERARCHY_LEVELS),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

```


-----

# Файл: models.py

```
from django.db import models
from django.contrib.auth.models import User

class Department(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название")
    short_name = models.CharField(max_length=50, blank=True, verbose_name="Короткое название")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                              verbose_name="Родительское подразделение")
    level = models.IntegerField(default=1, verbose_name="Уровень")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Структурное подразделение'
        verbose_name_plural = 'Структурные подразделения'

    def __str__(self):
        return self.name

    def get_full_path(self):
        parts = []
        current = self
        while current:
            parts.append(current.name)
            current = current.parent
        return ' → '.join(reversed(parts))

    def get_all_children(self):
        """Возвращает все дочерние подразделения"""
        children = []
        for child in self.children.all():
            children.append(child)
            children.extend(child.get_all_children())
        return children

class Employee(models.Model):
    HIERARCHY_LEVELS = [
        (1, 'Высшее руководство (ГД)'),
        (2, 'Первые заместители'),
        (3, 'Заместители'),
        (4, 'Руководители центров'),
        (5, 'Руководители управлений'),
        (6, 'Руководители отделов'),
        (7, 'Специалисты'),
        (8, 'Ассистенты'),
    ]

    initials = models.CharField(max_length=50, verbose_name="Инициалы")
    full_name = models.CharField(max_length=200, verbose_name="ФИО")
    position = models.CharField(max_length=200, verbose_name="Должность")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True,
                                  blank=True, verbose_name="Подразделение")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    internal_phone = models.CharField(max_length=20, verbose_name="Внутренний телефон")
    email = models.EmailField(blank=True, verbose_name="Email")
    room = models.CharField(max_length=50, blank=True, verbose_name="Кабинет")
    hierarchy = models.IntegerField(choices=HIERARCHY_LEVELS, default=7, verbose_name="Уровень иерархии")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['department', 'hierarchy', 'full_name']
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'
        unique_together = ['full_name', 'internal_phone']

    def __str__(self):
        return f"{self.full_name} ({self.position})"

class ImportLog(models.Model):
    STATUS_CHOICES = [
        ('success', 'Успешно'),
        ('partial', 'Частично'),
        ('failed', 'Не удалось'),
    ]

    file_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    total_records = models.IntegerField()
    added = models.IntegerField()
    updated = models.IntegerField()
    errors = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Лог импорта'
        verbose_name_plural = 'Логи импорта'

```


-----

# Файл: tests.py

```
from django.test import TestCase

# Create your tests here.

```


-----

# Файл: urls.py

```
from django.urls import path
from . import views

urlpatterns = [
    path('', views.EmployeeListView.as_view(), name='employee_list'),
    path('api/employees/', views.employee_search_api, name='employee_search_api'),
    path('api/employees/<int:pk>/', views.employee_detail_api, name='employee_detail_api'),
    path('api/employees/create/', views.employee_create_api, name='employee_create_api'),
    path('api/employees/update/<int:pk>/', views.employee_update_api, name='employee_update_api'),
    path('api/employees/delete/<int:pk>/', views.employee_delete_api, name='employee_delete_api'),
    path('import/', views.ImportView.as_view(), name='import'),
    path('import/log/', views.ImportLogListView.as_view(), name='import_log'),
]

```


-----

# Файл: views.py

```
import pandas as pd
import re
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.generic import ListView
from django.urls import reverse_lazy
from django.db import transaction, models
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from .models import Employee, ImportLog, Department
from .forms import EmployeeForm, ImportForm, SearchForm

def extract_short_name(full_name):
    """Извлекает сокращенное название из скобок"""
    match = re.search(r'\((.*?)\)', full_name)
    if match:
        short_name = match.group(1)
        clean_name = re.sub(r'\(.*?\)', '', full_name).strip()
        return clean_name, short_name
    return full_name, ''

def determine_hierarchy_from_position(position):
    """Определяет уровень иерархии на основе должности"""
    position_lower = position.lower()

    if any(word in position_lower for word in ['генеральный директор', 'гд', 'директор']):
        return 1
    elif any(word in position_lower for word in ['первый заместитель', '1-й зам']):
        return 2
    elif any(word in position_lower for word in ['заместитель', 'зам', 'вице']):
        return 3
    elif any(word in position_lower for word in ['руководитель центра', 'директор департамента', 'начальник департамента']):
        return 4
    elif any(word in position_lower for word in ['руководитель управления', 'начальник управления', 'руководитель отделения']):
        return 5
    elif any(word in position_lower for word in ['руководитель отдела', 'начальник отдела', 'руководитель службы']):
        return 6
    elif any(word in position_lower for word in ['специалист', 'эксперт', 'аналитик']):
        return 7
    else:
        return 8  # Ассистенты по умолчанию

class EmployeeListView(ListView):
    model = Employee
    template_name = 'employees/list.html'
    context_object_name = 'employees'
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset().select_related('department')
        query = self.request.GET.get('query')
        department_id = self.request.GET.get('department')
        hierarchy = self.request.GET.get('hierarchy')

        if query:
            queryset = queryset.filter(
                models.Q(full_name__icontains=query) |
                models.Q(position__icontains=query) |
                models.Q(department__name__icontains=query) |
                models.Q(department__short_name__icontains=query) |
                models.Q(phone__icontains=query) |
                models.Q(email__icontains=query)
            )

        if department_id:
            try:
                department = Department.objects.get(id=department_id)
                # Включаем всех сотрудников выбранного подразделения и его дочерних
                all_departments = [department] + list(department.get_all_children())
                queryset = queryset.filter(department__in=all_departments)
            except Department.DoesNotExist:
                pass

        if hierarchy:
            queryset = queryset.filter(hierarchy=hierarchy)

        return queryset.order_by('department__level', 'department__name', 'hierarchy', 'full_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = SearchForm(self.request.GET or None)
        context['departments'] = Department.objects.filter(level=1).order_by('name')
        context['hierarchy_levels'] = Employee.HIERARCHY_LEVELS

        # Группировка по иерархии подразделений
        employees = context['employees']
        departments_tree = {}

        for employee in employees:
            dept = employee.department
            if not dept:
                continue

            # Строим полный путь подразделения
            current = dept
            path = []
            while current:
                path.insert(0, current)
                current = current.parent

            # Добавляем сотрудника в дерево
            current_level = departments_tree
            for i, dept_node in enumerate(path):
                dept_id = dept_node.id
                if dept_id not in current_level:
                    current_level[dept_id] = {
                        'department': dept_node,
                        'employees': [],
                        'children': {}
                    }

                if i == len(path) - 1:  # Последний уровень - добавляем сотрудника
                    current_level[dept_id]['employees'].append(employee)
                else:  # Переходим на следующий уровень
                    current_level = current_level[dept_id]['children']

        context['departments_tree'] = self._flatten_tree(departments_tree)
        return context

    def _flatten_tree(self, tree, level=0):
        """Преобразует дерево в плоский список для отображения"""
        result = []
        for dept_id, data in sorted(tree.items(), key=lambda x: x[1]['department'].name):
            result.append({
                'department': data['department'],
                'employees': sorted(data['employees'], key=lambda x: (x.hierarchy, x.full_name)),
                'level': level,
                'children': self._flatten_tree(data['children'], level + 1)
            })
        return result

@require_http_methods(["GET"])
def employee_detail_api(request, pk):
    try:
        employee = get_object_or_404(Employee, pk=pk)
        data = {
            'id': employee.id,
            'initials': employee.initials,
            'full_name': employee.full_name,
            'position': employee.position,
            'department': employee.department.id if employee.department else None,
            'phone': employee.phone,
            'internal_phone': employee.internal_phone,
            'email': employee.email,
            'room': employee.room,
            'hierarchy': employee.hierarchy,
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def employee_create_api(request):
    try:
        data = json.loads(request.body)
        form = EmployeeForm(data)
        if form.is_valid():
            employee = form.save()
            return JsonResponse({'success': True, 'id': employee.id})
        return JsonResponse({'success': False, 'errors': form.errors})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
def employee_update_api(request, pk):
    try:
        employee = get_object_or_404(Employee, pk=pk)
        data = json.loads(request.body)
        form = EmployeeForm(data, instance=employee)
        if form.is_valid():
            employee = form.save()
            return JsonResponse({'success': True, 'id': employee.id})
        return JsonResponse({'success': False, 'errors': form.errors})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_http_methods(["DELETE"])
def employee_delete_api(request, pk):
    try:
        employee = get_object_or_404(Employee, pk=pk)
        employee.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_http_methods(["GET"])
def employee_search_api(request):
    query = request.GET.get('query', '').strip()

    if not query or len(query) < 2:
        return JsonResponse({'results': []})

    try:
        # Получаем всех сотрудников с подразделениями
        all_employees = Employee.objects.select_related('department')

        query_lower = query.lower()
        results = []

        for emp in all_employees:
            # Проверяем все текстовые поля на совпадение (регистронезависимо)
            search_fields = [
                emp.full_name or '',
                emp.position or '',
                emp.department.name if emp.department else '',
                emp.department.short_name if emp.department and emp.department.short_name else '',
                emp.phone or '',
                emp.room or '',
                emp.internal_phone or '',
                emp.email or ''
            ]

            # Проверяем, содержится ли запрос в любом из полей (регистронезависимо)
            if any(query_lower in (field or '').lower() for field in search_fields):
                results.append({
                    'id': emp.id,
                    'full_name': emp.full_name,
                    'position': emp.position,
                    'department': emp.department.name if emp.department else '',
                    'department_short': emp.department.short_name if emp.department else '',
                    'phone': emp.phone,
                    'room': emp.room or '',
                    'internal_phone': emp.internal_phone or '',
                    'email': emp.email or '',
                    'hierarchy': emp.get_hierarchy_display()
                })

                # Ограничиваем количество результатов для производительности
                if len(results) >= 20:
                    break

        # Сортируем результаты по релевантности
        results.sort(key=lambda x: (
            query_lower not in (x['full_name'] or '').lower(),
            query_lower not in (x['position'] or '').lower(),
            x['full_name']
        ))

        return JsonResponse({'results': results[:15]})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@method_decorator(login_required, name='dispatch')
class ImportView(ListView):
    template_name = 'employees/import.html'

    def get(self, request):
        form = ImportForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = ImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                result = self.process_excel_file(request.FILES['excel_file'], request.user)
                return JsonResponse(result)
            except Exception as e:
                return JsonResponse({'status': 'failed', 'error': str(e)})
        return JsonResponse({'status': 'failed', 'error': 'Invalid form'})

    def process_excel_file(self, file, user):
        try:
            df = pd.read_excel(file, dtype=str)
        except Exception as e:
            raise ValueError(f"Ошибка чтения файла: {str(e)}")

        # Заменяем NaN, None и строки 'nan' на пустые строки
        df = df.fillna('')
        df = df.replace(['nan', 'None', 'NONE', 'null', 'NULL'], '', regex=True)

        required_columns = [
            'Инициалы', 'ФИО', 'Должность', 'Структурное подразделение 1',
            'Структурное подразделение 2', 'Структурное подразделение 3',
            'Структурное подразделение 4', 'Телефон', 'Внутренний телефон', 'Кабинет', 'Уровень'
        ]

        # Проверяем наличие всех required_columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Отсутствуют обязательные столбцы: {', '.join(missing_columns)}")

        added = 0
        updated = 0
        errors = []

        with transaction.atomic():
            for index, row in df.iterrows():
                try:
                    # Функция для очистки значений
                    def clean_value(value, is_level=False):
                        if value is None or pd.isna(value) or str(value).strip().lower() in ['', 'nan', 'none', 'null']:
                            return '' if not is_level else 7  # Специалист по умолчанию

                        value_str = str(value).strip()

                        if is_level:
                            try:
                                level = int(float(value_str))
                                return max(1, min(8, level))  # Ограничиваем диапазон 1-8
                            except (ValueError, TypeError):
                                return 7  # Специалист по умолчанию
                        return value_str

                    # Обрабатываем подразделения с извлечением short_name
                    dept_names = []
                    for i in range(1, 5):
                        col_name = f'Структурное подразделение {i}'
                        dept_name = clean_value(row.get(col_name, ''))
                        if dept_name:
                            full_name, short_name = extract_short_name(dept_name)
                            dept_names.append((full_name, short_name))

                    # Строим иерархию подразделений
                    parent = None
                    current_level = 1

                    for full_name, short_name in dept_names:
                        dept, created = Department.objects.get_or_create(
                            name=full_name,
                            parent=parent,
                            defaults={
                                'short_name': short_name,
                                'level': current_level
                            }
                        )

                        # Обновляем short_name если он изменился
                        if not created and short_name and dept.short_name != short_name:
                            dept.short_name = short_name
                            dept.save()

                        parent = dept
                        current_level += 1

                    # Определяем уровень иерархии
                    position = clean_value(row['Должность'])
                    hierarchy = clean_value(row['Уровень'], is_level=True)

                    # Если уровень не указан или указан некорректно, определяем по должности
                    if hierarchy == 7:  # Только если не указан явно или указан как специалист
                        hierarchy = determine_hierarchy_from_position(position)

                    employee_data = {
                        'initials': clean_value(row['Инициалы']),
                        'full_name': clean_value(row['ФИО']),
                        'position': position,
                        'department': parent,
                        'phone': clean_value(row['Телефон']),
                        'internal_phone': clean_value(row['Внутренний телефон']),
                        'room': clean_value(row['Кабинет']),
                        'hierarchy': hierarchy,
                        'email': clean_value(row.get('Email', ''))
                    }

                    if not employee_data['full_name']:
                        errors.append(f"Строка {index + 2}: Отсутствует ФИО")
                        continue

                    employee, created = Employee.objects.update_or_create(
                        full_name=employee_data['full_name'],
                        internal_phone=employee_data['internal_phone'],
                        defaults=employee_data
                    )

                    if created:
                        added += 1
                    else:
                        updated += 1

                except Exception as e:
                    errors.append(f"Строка {index + 2}: {str(e)}")

        status = 'success' if not errors else 'partial' if added + updated > 0 else 'failed'

        ImportLog.objects.create(
            file_name=file.name,
            status=status,
            total_records=len(df),
            added=added,
            updated=updated,
            errors='\n'.join(errors),
            user=user if user.is_authenticated else None
        )

        return {
            'status': status,
            'total': len(df),
            'added': added,
            'updated': updated,
            'errors': errors
        }

class ImportLogListView(ListView):
    model = ImportLog
    template_name = 'employees/import_log.html'
    context_object_name = 'import_logs'
    paginate_by = 20
    ordering = ['-uploaded_at']

```


-----

# Файл: __init__.py

```

```


-----

# Файл: templates\employees\confirm_delete_modal.html

```
<div class="modal fade" id="deleteModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Подтверждение удаления</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <p>Вы уверены, что хотите удалить этого сотрудника?</p>
                <p id="deleteEmployeeInfo" class="fw-bold"></p>
                <div class="alert alert-warning">
                    <i class="bi bi-exclamation-triangle"></i> Это действие нельзя отменить!
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Отмена</button>
                <button type="button" class="btn btn-danger" id="confirmDelete">
                    <i class="bi bi-trash"></i> Удалить
                </button>
            </div>
        </div>
    </div>
</div>

```


-----

# Файл: templates\employees\department_node.html

```
<div class="department-level-{{ dept_data.level }} department-card">
    <h5 class="department-title">
        <i class="bi bi-building"></i>
        {{ dept_data.department.name }}
        {% if dept_data.department.short_name %}
            <small class="text-muted">({{ dept_data.department.short_name }})</small>
        {% endif %}
    </h5>

    {% if dept_data.employees %}
    <div class="employees-list">
        {% for employee in dept_data.employees %}
        <div class="card employee-card mb-2">
            <div class="card-body">
                <div class="row align-items-center">
                    <div class="col-md-8">
                        <h6 class="employee-name">{{ employee.full_name }}</h6>
                        <p class="employee-position mb-1">{{ employee.position }}</p>
                        <div class="employee-contacts">
                            {% if employee.phone %}<span class="me-3"><i class="bi bi-telephone"></i> {{ employee.phone }}</span>{% endif %}
                            {% if employee.internal_phone %}<span class="me-3"><i class="bi bi-telephone-plus"></i> {{ employee.internal_phone }}</span>{% endif %}
                            {% if employee.email %}<span><i class="bi bi-envelope"></i> {{ employee.email }}</span>{% endif %}
                        </div>
                    </div>
                    <div class="col-md-4 text-end">
                        <span class="badge hierarchy-badge-{{ employee.hierarchy }}">
                            {{ employee.get_hierarchy_display }}
                        </span>
                        <div class="btn-group mt-2">
                            <button class="btn btn-sm btn-outline-primary edit-btn" data-id="{{ employee.id }}">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger delete-btn" data-id="{{ employee.id }}">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    {% if dept_data.children %}
        {% for child in dept_data.children %}
            {% include 'employees/department_node.html' with dept_data=child %}
        {% endfor %}
    {% endif %}
</div>

```


-----

# Файл: templates\employees\import.html

```
{% extends 'base.html' %}
{% load static %}

{% block content %}
<div class="row">
    <div class="col-md-8 mx-auto">
        <div class="card">
            <div class="card-header">
                <h4 class="card-title">Импорт данных из Excel</h4>
            </div>
            <div class="card-body">
                <div class="alert alert-info">
                    <h5>Требования к файлу:</h5>
                    <ul class="mb-0">
                        <li>Формат: XLSX</li>
                        <li>Столбцы должны быть в следующем порядке:</li>
                        <ol>
                            <li>Инициалы (Иванов И.И.)</li>
                            <li>ФИО (Иванов Иван Иванович)</li>
                            <li>Должность (Специалист)</li>
                            <li>Структурное подразделение 1</li>
                            <li>Структурное подразделение 2</li>
                            <li>Структурное подразделение 3</li>
                            <li>Структурное подразделение 4</li>
                            <li>Телефон</li>
                            <li>Внутренний телефон</li>
                            <li>Уровень иерархии (1-5)</li>
                        </ol>
                    </ul>
                </div>

                <form id="importForm" enctype="multipart/form-data">
                    {% csrf_token %}
                    <div class="mb-3">
                        <label for="excel_file" class="form-label">Выберите Excel файл</label>
                        <input type="file" class="form-control" id="excel_file" name="excel_file" accept=".xlsx" required>
                    </div>

                    <button type="submit" class="btn btn-primary" id="importBtn">
                        <i class="bi bi-upload"></i> Загрузить файл
                    </button>
                </form>

                <div id="importResult" class="mt-4" style="display: none;">
                    <div class="alert alert-success" id="successAlert" style="display: none;">
                        <h5>Импорт завершен успешно!</h5>
                        <p id="successMessage"></p>
                    </div>

                    <div class="alert alert-warning" id="partialAlert" style="display: none;">
                        <h5>Импорт завершен частично</h5>
                        <p id="partialMessage"></p>
                    </div>

                    <div class="alert alert-danger" id="errorAlert" style="display: none;">
                        <h5>Ошибка импорта</h5>
                        <p id="errorMessage"></p>
                    </div>

                    <div id="errorDetails" style="display: none;">
                        <h6>Детали ошибок:</h6>
                        <pre id="errorDetailsContent" class="bg-light p-3"></pre>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
class ImportManager {
    constructor() {
        this.form = document.getElementById('importForm');
        this.importBtn = document.getElementById('importBtn');
        this.initEventListeners();
    }

    initEventListeners() {
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.importFile();
        });
    }

    async importFile() {
        const formData = new FormData(this.form);
        const originalBtnText = this.importBtn.innerHTML;

        try {
            this.importBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Загрузка...';
            this.importBtn.disabled = true;

            const response = await fetch('{% url "import" %}', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                },
            });

            const result = await response.json();
            this.showResult(result);

        } catch (error) {
            this.showResult({
                status: 'failed',
                error: 'Ошибка сети: ' + error.message
            });
        } finally {
            this.importBtn.innerHTML = originalBtnText;
            this.importBtn.disabled = false;
        }
    }

    showResult(result) {
        const resultDiv = document.getElementById('importResult');
        resultDiv.style.display = 'block';

        // Скрываем все алерты
        document.getElementById('successAlert').style.display = 'none';
        document.getElementById('partialAlert').style.display = 'none';
        document.getElementById('errorAlert').style.display = 'none';
        document.getElementById('errorDetails').style.display = 'none';

        if (result.status === 'success') {
            const successAlert = document.getElementById('successAlert');
            document.getElementById('successMessage').textContent =
                `Добавлено: ${result.added}, Обновлено: ${result.updated}, Всего записей: ${result.total}`;
            successAlert.style.display = 'block';

        } else if (result.status === 'partial') {
            const partialAlert = document.getElementById('partialAlert');
            document.getElementById('partialMessage').textContent =
                `Добавлено: ${result.added}, Обновлено: ${result.updated}, Всего записей: ${result.total}.
                 Ошибок: ${result.errors ? result.errors.length : 0}`;
            partialAlert.style.display = 'block';

            if (result.errors && result.errors.length > 0) {
                document.getElementById('errorDetailsContent').textContent = result.errors.join('\n');
                document.getElementById('errorDetails').style.display = 'block';
            }

        } else {
            const errorAlert = document.getElementById('errorAlert');
            document.getElementById('errorMessage').textContent = result.error || 'Неизвестная ошибка';
            errorAlert.style.display = 'block';

            if (result.errors && result.errors.length > 0) {
                document.getElementById('errorDetailsContent').textContent = result.errors.join('\n');
                document.getElementById('errorDetails').style.display = 'block';
            }
        }
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    new ImportManager();
});
</script>
{% endblock %}

```


-----

# Файл: templates\employees\import_log.html

```
{% extends 'base.html' %}

{% block content %}
<div class="row">
    <div class="col-12">
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h4 class="card-title mb-0">История импорта</h4>
                <a href="{% url 'import' %}" class="btn btn-primary btn-sm">
                    <i class="bi bi-arrow-left"></i> Назад к импорту
                </a>
            </div>
            <div class="card-body">
                {% if import_logs %}
                <div class="table-responsive">
                    <table class="table table-striped table-hover">
                        <thead>
                            <tr>
                                <th>Файл</th>
                                <th>Дата загрузки</th>
                                <th>Статус</th>
                                <th>Всего записей</th>
                                <th>Добавлено</th>
                                <th>Обновлено</th>
                                <th>Пользователь</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for log in import_logs %}
                            <tr>
                                <td>{{ log.file_name }}</td>
                                <td>{{ log.uploaded_at|date:"d.m.Y H:i" }}</td>
                                <td>
                                    <span class="badge
                                        {% if log.status == 'success' %}bg-success
                                        {% elif log.status == 'partial' %}bg-warning
                                        {% else %}bg-danger{% endif %}">
                                        {{ log.get_status_display }}
                                    </span>
                                </td>
                                <td>{{ log.total_records }}</td>
                                <td>{{ log.added }}</td>
                                <td>{{ log.updated }}</td>
                                <td>{{ log.user.username|default:"Система" }}</td>
                            </tr>
                            {% if log.errors %}
                            <tr>
                                <td colspan="7">
                                    <div class="alert alert-warning mb-0">
                                        <strong>Ошибки:</strong>
                                        <pre class="mb-0">{{ log.errors }}</pre>
                                    </div>
                                </td>
                            </tr>
                            {% endif %}
                            {% endfor %}
                        </tbody>
                    </table>
                </div>

                {% if is_paginated %}
                <nav aria-label="Page navigation">
                    <ul class="pagination">
                        {% if page_obj.has_previous %}
                        <li class="page-item">
                            <a class="page-link" href="?page={{ page_obj.previous_page_number }}">Предыдущая</a>
                        </li>
                        {% endif %}

                        {% for num in page_obj.paginator.page_range %}
                        <li class="page-item {% if page_obj.number == num %}active{% endif %}">
                            <a class="page-link" href="?page={{ num }}">{{ num }}</a>
                        </li>
                        {% endfor %}

                        {% if page_obj.has_next %}
                        <li class="page-item">
                            <a class="page-link" href="?page={{ page_obj.next_page_number }}">Следующая</a>
                        </li>
                        {% endif %}
                    </ul>
                </nav>
                {% endif %}

                {% else %}
                <div class="alert alert-info">
                    <i class="bi bi-info-circle"></i> История импорта пуста.
                </div>
                {% endif %}
            </div>
        </div>
    </div>
</div>
{% endblock %}

```


-----

# Файл: templates\employees\list.html

```
{% extends 'base.html' %}
{% load static %}

{% block extra_css %}
<style>
    .search-section {
        background: var(--background-color-primary);
        border-radius: var(--cards-radius-2);
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: var(--box-shadow-card);
    }

    .filter-section {
        background: var(--background-color-primary);
        border-radius: var(--cards-radius-2);
        padding: 1.5rem;
        margin-bottom: 2rem;
        box-shadow: var(--box-shadow-card);
    }

    .department-level-1 { margin-left: 0; border-left: 4px solid var(--background-color-accent); }
    .department-level-2 { margin-left: 20px; border-left: 3px solid var(--icon-color-primary); }
    .department-level-3 { margin-left: 40px; border-left: 2px solid var(--text-color-tertiary); }
    .department-level-4 { margin-left: 60px; border-left: 1px solid var(--separator-color-primary); }

    .department-card {
        background: var(--background-color-primary);
        border-radius: var(--cards-radius-2);
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: var(--box-shadow-card);
    }

    .hierarchy-badge-1 { background: var(--background-color-accent); color: white; }
    .hierarchy-badge-2 { background: var(--button-color-primaryHover); color: white; }
    .hierarchy-badge-3 { background: var(--text-color-tertiary); color: white; }
    .hierarchy-badge-4 { background: var(--button-color-quaternary); color: var(--text-color-primary); }
    .hierarchy-badge-5 { background: var(--background-color-tertiary); color: var(--text-color-primary); }
    .hierarchy-badge-6 { background: var(--button-color-quaternaryDisabled); color: var(--text-color-primary); }

    .employee-actions {
        display: flex;
        gap: 0.5rem;
        justify-content: flex-end;
    }

    .employee-contact-info {
        border-top: 1px solid var(--separator-color-primary);
        padding-top: 1rem;
        margin-top: 1rem;
    }

    .no-employees {
        text-align: center;
        padding: 3rem;
        color: var(--text-color-primary);
        background: var(--background-color-primary);
        border-radius: var(--cards-radius-2);
        box-shadow: var(--box-shadow-card);
    }

    .no-employees i {
        font-size: 3rem;
        color: var(--icon-color-primary);
        margin-bottom: 1rem;
    }

    .search-form {
        display: flex;
        gap: 1rem;
        align-items: flex-end;
    }

    @media (max-width: 768px) {
        .search-form {
            flex-direction: column;
            align-items: stretch;
        }

        .employee-card-content .row {
            flex-direction: column;
        }

        .employee-actions {
            justify-content: center;
            margin-top: 1rem;
        }
    }
</style>
{% endblock %}

{% block content %}
<div class="search-section">
    <!-- Форма поиска и фильтров -->
    <form method="get" class="row g-3 align-items-end">
        <div class="col-md-4">
            <label class="form-label fw-bold">Поиск</label>
            <input type="text" name="query" class="form-control"
                   placeholder="ФИО, должность, телефон..." value="{{ request.GET.query }}">
        </div>
        <div class="col-md-3">
            <label class="form-label fw-bold">Подразделение</label>
            {{ search_form.department }}
        </div>
        <div class="col-md-3">
            <label class="form-label fw-bold">Уровень</label>
            {{ search_form.hierarchy }}
        </div>
        <div class="col-md-2">
            <button type="submit" class="btn btn-primary w-100">
                <i class="bi bi-search"></i> Применить
            </button>
        </div>
    </form>
</div>

{% if departments_tree %}
    {% for dept_data in departments_tree %}
        {% include 'employees/department_node.html' with dept_data=dept_data %}
    {% endfor %}
{% else %}
    <div class="no-employees">
        <i class="bi bi-people"></i>
        <h4>Сотрудники не найдены</h4>
        <p class="text-muted">Попробуйте изменить параметры поиска</p>
    </div>
{% endif %}

{% if is_paginated %}
<nav aria-label="Page navigation" class="mt-4">
    <ul class="pagination justify-content-center">
        {% if page_obj.has_previous %}
        <li class="page-item">
            <a class="page-link" href="?page={{ page_obj.previous_page_number }}{% if request.GET.query %}&query={{ request.GET.query }}{% endif %}{% if request.GET.department %}&department={{ request.GET.department }}{% endif %}">
                <i class="bi bi-chevron-left"></i> Предыдущая
            </a>
        </li>
        {% endif %}

        {% for num in page_obj.paginator.page_range %}
        <li class="page-item {% if page_obj.number == num %}active{% endif %}">
            <a class="page-link" href="?page={{ num }}{% if request.GET.query %}&query={{ request.GET.query }}{% endif %}{% if request.GET.department %}&department={{ request.GET.department }}{% endif %}">
                {{ num }}
            </a>
        </li>
        {% endfor %}

        {% if page_obj.has_next %}
        <li class="page-item">
            <a class="page-link" href="?page={{ page_obj.next_page_number }}{% if request.GET.query %}&query={{ request.GET.query }}{% endif %}{% if request.GET.department %}&department={{ request.GET.department }}{% endif %}">
                Следующая <i class="bi bi-chevron-right"></i>
            </a>
        </li>
        {% endif %}
    </ul>
</nav>
{% endif %}

<!-- Модальные окна -->
{% include 'employees/confirm_delete_modal.html' %}

<div class="modal fade" id="employeeModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="modalTitle">Добавить сотрудника</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <form id="employeeForm">
                <div class="modal-body">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">Инициалы</label>
                                <input type="text" name="initials" class="form-control" required>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">ФИО *</label>
                                <input type="text" name="full_name" class="form-control" required>
                            </div>
                        </div>
                    </div>

                    <div class="mb-3">
                        <label class="form-label">Должность *</label>
                        <input type="text" name="position" class="form-control" required>
                    </div>

                    <div class="mb-3">
                        <label class="form-label">Подразделение</label>
                        <select name="department" class="form-select">
                            <option value="">-- Выберите подразделение --</option>
                            {% for dept in departments %}
                            <option value="{{ dept.id }}">{{ dept.name }}</option>
                            {% endfor %}
                        </select>
                    </div>

                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">Телефон *</label>
                                <input type="text" name="phone" class="form-control" required>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">Внутренний телефон *</label>
                                <input type="text" name="internal_phone" class="form-control" required>
                            </div>
                        </div>
                    </div>

                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">Кабинет</label>
                                <input type="text" name="room" class="form-control">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">Уровень иерархии *</label>
                                <select name="hierarchy" class="form-select" required>
                                    <option value="1">Высшее руководство</option>
                                    <option value="2">Руководство</option>
                                    <option value="3" selected>Менеджеры</option>
                                    <option value="4">Специалисты</option>
                                    <option value="5">Ассистенты</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <div class="mb-3">
                        <label class="form-label">Email</label>
                        <input type="email" name="email" class="form-control">
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Отмена</button>
                    <button type="submit" class="btn btn-primary">Сохранить</button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="{% static 'employees/js/main.js' %}"></script>
<script src="{% static 'employees/js/search.js' %}"></script>
{% endblock %}

```
