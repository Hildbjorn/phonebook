# Файл: admin.py

```
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

# Файл: forms.py

```
from django import forms
from .models import Employee, Department

class EmployeeForm(forms.ModelForm):
    """
    Форма для создания и редактирования сотрудников
    """
    class Meta:
        model = Employee
        fields = '__all__'
        widgets = {
            'initials': forms.TextInput(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control tel'}),
            'internal_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'room': forms.TextInput(attrs={'class': 'form-control'}),
            'hierarchy': forms.Select(attrs={'class': 'form-control'}),
        }


class ImportForm(forms.Form):
    """
    Форма для импорта данных из Excel
    """
    excel_file = forms.FileField(
        label='Excel файл',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx',
            'hx-post': '/import/',
            'hx-target': '#importResult',
            'hx-swap': 'innerHTML',
            'hx-encoding': 'multipart/form-data'
        })
    )


class SearchForm(forms.Form):
    """
    Форма для поиска и фильтрации сотрудников
    """
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по ФИО, должности, отделам...',
            'hx-get': '/api/employees/search/',
            'hx-target': '#searchResults',
            'hx-trigger': 'keyup changed delay:500ms',
            'hx-swap': 'innerHTML'
        })
    )
```


-----

# Файл: models.py

```
from django.db import models
from django.contrib.auth.models import User

class Department(models.Model):
    """
    Модель структурного подразделения с иерархической структурой
    """
    name = models.CharField(max_length=200, verbose_name="Название")
    short_name = models.CharField(max_length=50, blank=True, verbose_name="Короткое название")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                              verbose_name="Родительское подразделение", 
                              related_name='children')
    level = models.IntegerField(default=1, verbose_name="Уровень")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['level', 'name']
        verbose_name = 'Структурное подразделение'
        verbose_name_plural = 'Структурные подразделения'

    def __str__(self):
        return self.name

    def get_full_path(self):
        """Возвращает полный путь подразделения в иерархии"""
        parts = []
        current = self
        while current:
            parts.append(current.name)
            current = current.parent
        return ' → '.join(reversed(parts))

    def get_all_children(self):
        """Возвращает все дочерние подразделения рекурсивно"""
        children = list(self.children.all())
        for child in self.children.all():
            children.extend(child.get_all_children())
        return children

    def get_tree_data(self):
        """Возвращает данные для древовидного отображения"""
        return {
            'id': self.id,
            'name': self.name,
            'short_name': self.short_name,
            'level': self.level,
            'children': [child.get_tree_data() for child in self.children.all().order_by('name')]
        }


class Employee(models.Model):
    """
    Модель сотрудника/абонента телефонной книги
    """
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
        ordering = ['department__level', 'department__name', 'hierarchy', 'full_name']
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'
        unique_together = ['full_name', 'internal_phone']

    def __str__(self):
        return f"{self.full_name} ({self.position})"

    def get_hierarchy_display(self):
        """Возвращает отображаемое название уровня иерархии"""
        return dict(self.HIERARCHY_LEVELS).get(self.hierarchy, 'Неизвестно')


class ImportLog(models.Model):
    """
    Модель для логирования операций импорта данных
    """
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

    def get_status_display(self):
        """Возвращает отображаемое название статуса"""
        return dict(self.STATUS_CHOICES).get(self.status, 'Неизвестно')
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
    path('import/', views.ImportView.as_view(), name='import'),
    path('import/log/', views.ImportLogListView.as_view(), name='import_log'),
    # API
    path('api/employees/search/', views.employee_search_api, name='employee_search_api'),
    path('api/employees/<int:pk>/', views.employee_detail_api, name='employee_detail_api'),
    path('api/employees/form/', views.employee_form_api, name='employee_form_create'),
    path('api/employees/form/<int:pk>/', views.employee_form_api, name='employee_form_update'),
    path('api/employees/create/', views.employee_create_api, name='employee_create_api'),
    path('api/employees/update/<int:pk>/', views.employee_update_api, name='employee_update_api'),
    path('api/employees/delete/<int:pk>/', views.employee_delete_api, name='employee_delete_api'),
]
```


-----

# Файл: views.py

```
from django.shortcuts import render

# Create your views here.
import pandas as pd
import re
import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, View
from django.db import transaction, models
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from .models import Employee, ImportLog, Department
from .forms import EmployeeForm, ImportForm, SearchForm

def is_superuser(user):
    """Проверка, что пользователь суперпользователь"""
    return user.is_superuser

def extract_short_name(full_name):
    """Извлекает сокращенное название из скобок"""
    match = re.search(r'\((.*?)\)', full_name)
    if match:
        short_name = match.group(1)
        clean_name = re.sub(r'\(.*?\)', '', full_name).strip()
        return clean_name, short_name
    return full_name, ''

def get_all_children(self):
    """Возвращает все дочерние подразделения рекурсивно"""
    children = list(self.children.all())  # Теперь это будет работать
    for child in self.children.all():
        children.extend(child.get_all_children())
    return children

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
    """
    Представление для отображения списка сотрудников с фильтрацией
    """
    model = Employee
    template_name = 'employees/list.html'
    context_object_name = 'employees'
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset().select_related('department')
        query = self.request.GET.get('query')
        department_id = self.request.GET.get('department')

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
                all_departments = [department] + department.get_all_children()
                queryset = queryset.filter(department__in=all_departments)
            except Department.DoesNotExist:
                pass

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = SearchForm(self.request.GET or None)
        context['departments_tree'] = self.get_departments_tree()
        context['is_superuser'] = self.request.user.is_superuser
        return context

    def get_departments_tree(self):
        """Возвращает древовидную структуру подразделений"""
        top_level_departments = Department.objects.filter(level=1).order_by('id')
        tree = []
        
        for dept in top_level_departments:
            tree.append(self.build_department_node(dept))
        
        return tree

    def build_department_node(self, department):
        """Рекурсивно строит узел подразделения с дочерними элементами"""
        node = {
            'department': department,
            'employees': list(department.employee_set.all().order_by('hierarchy', 'full_name')),
            'children': []
        }
        
        for child in department.children.all().order_by('name'):
            node['children'].append(self.build_department_node(child))
            
        return node


@require_http_methods(["GET"])
def employee_search_api(request):
    """
    API endpoint для поиска сотрудников
    """
    query = request.GET.get('query', '').strip()

    if not query or len(query) < 2:
        return HttpResponse('')  # Пустой ответ для HTMX

    employees = Employee.objects.select_related('department').filter(
        models.Q(full_name__icontains=query) |
        models.Q(position__icontains=query) |
        models.Q(department__name__icontains=query) |
        models.Q(phone__icontains=query)
    )[:15]

    html = ''.join([
        f'<div class="search-result-item" hx-get="/api/employees/{emp.id}/" hx-target="#employeeDetails" hx-swap="innerHTML">'
        f'  <strong>{emp.full_name}</strong> - {emp.position}<br>'
        f'  <small>{emp.department.name if emp.department else "Без подразделения"} | {emp.phone}</small>'
        f'</div>'
        for emp in employees
    ])

    return HttpResponse(html or '<div class="search-result-item">Ничего не найдено</div>')


@require_http_methods(["GET"])
def employee_detail_api(request, pk):
    """
    API endpoint для получения детальной информации о сотруднике
    """
    employee = get_object_or_404(Employee, pk=pk)
    
    html = f"""
    <div class="card">
        <div class="card-header">
            <h5>{employee.full_name}</h5>
            <span class="badge hierarchy-badge-{employee.hierarchy}">
                {employee.get_hierarchy_display()}
            </span>
        </div>
        <div class="card-body">
            <p><strong>Должность:</strong> {employee.position}</p>
            <p><strong>Подразделение:</strong> {employee.department.get_full_path() if employee.department else 'Не указано'}</p>
            <p><strong>Телефон:</strong> {employee.phone}</p>
            <p><strong>Внутренний телефон:</strong> {employee.internal_phone}</p>
            <p><strong>Email:</strong> {employee.email or 'Не указан'}</p>
            <p><strong>Кабинет:</strong> {employee.room or 'Не указан'}</p>
        </div>
    </div>
    """
    
    return HttpResponse(html)


@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_superuser), name='dispatch')
class ImportView(View):
    """
    Представление для импорта данных из Excel (только для суперпользователей)
    """
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

        # Проверяем наличие обязательных столбцов
        required_columns = [
            'Инициалы', 'ФИО', 'Должность', 'Структурное подразделение 1',
            'Телефон', 'Внутренний телефон'
        ]
        
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


@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_superuser), name='dispatch')
class ImportLogListView(ListView):
    """
    Представление для просмотра логов импорта (только для суперпользователей)
    """
    model = ImportLog
    template_name = 'employees/import_log.html'
    context_object_name = 'import_logs'
    paginate_by = 20
    ordering = ['-uploaded_at']


# CRUD операции для сотрудников (только для суперпользователей)

@require_http_methods(["GET"])
@login_required
@user_passes_test(is_superuser)
def employee_form_api(request, pk=None):
    """
    API endpoint для получения HTML формы сотрудника
    """
    if pk:
        employee = get_object_or_404(Employee, pk=pk)
        form = EmployeeForm(instance=employee)
        title = "Редактировать сотрудника"
    else:
        form = EmployeeForm()
        title = "Добавить сотрудника"
    
    html = f"""
    <div class="modal-header">
        <h5 class="modal-title">{title}</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
    </div>
    <div class="modal-body">
        <form id="employeeForm" hx-post="{'/api/employees/update/' + str(pk) + '/' if pk else '/api/employees/create/'}" 
              hx-target="#employeesContent" hx-swap="innerHTML">
            {form.as_p()}
        </form>
    </div>
    <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Отмена</button>
        <button type="submit" form="employeeForm" class="btn btn-primary">Сохранить</button>
    </div>
    """
    
    return HttpResponse(html)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
@user_passes_test(is_superuser)
def employee_create_api(request):
    """Создание нового сотрудника"""
    try:
        # Получаем данные из формы, а не из JSON
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save()
            return JsonResponse({'success': True, 'id': employee.id})
        return JsonResponse({'success': False, 'errors': form.errors})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
@login_required
@user_passes_test(is_superuser)
def employee_update_api(request, pk):
    """Обновление данных сотрудника"""
    try:
        employee = get_object_or_404(Employee, pk=pk)
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            employee = form.save()
            return JsonResponse({'success': True, 'id': employee.id})
        return JsonResponse({'success': False, 'errors': form.errors})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["DELETE"])
@login_required
@user_passes_test(is_superuser)
def employee_delete_api(request, pk):
    """Удаление сотрудника"""
    try:
        employee = get_object_or_404(Employee, pk=pk)
        employee.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
```


-----

# Файл: __init__.py

```

```


-----

# Файл: templates\employees\department_node.html

```
<div class="department-node">
  <div class="department-header level-{{ dept_data.department.level }}" hx-get="?department={{ dept_data.department.id }}" hx-target="#employeesContent" hx-swap="innerHTML">
    <i class="bi bi-chevron-right"></i>
    {{ dept_data.department.name }}
    {% if dept_data.department.short_name %}
      <small class="text-muted">({{ dept_data.department.short_name }})</small>
    {% endif %}
  </div>

  {% if dept_data.children %}
    <div class="department-children">
      {% for child_data in dept_data.children %}
        {% include 'employees/department_node.html' with dept_data=child_data %}
      {% endfor %}
    </div>
  {% endif %}
</div>

```


-----

# Файл: templates\employees\employees_list_content.html

```
{% for dept_data in departments_tree %}
  <div class="department-section">
    <!-- Заголовок подразделения -->
    <div class="department-title">
      <h4>
        <i class="bi bi-building"></i>
        {{ dept_data.department.name }}
        {% if dept_data.department.short_name %}
          <small class="text-muted">({{ dept_data.department.short_name }})</small>
        {% endif %}
      </h4>
    </div>

    <!-- Сотрудники текущего подразделения -->
    {% if dept_data.employees %}
      <div class="employee-list">
        {% for employee in dept_data.employees %}
          <div class="employee-card">
            <div class="employee-header">
              <h5 class="employee-name">{{ employee.full_name }}</h5>
              <span class="hierarchy-badge level-{{ employee.hierarchy }}">{{ employee.get_hierarchy_display }}</span>
            </div>

            <div class="employee-details">
              <div>
                <strong>Должность:</strong> {{ employee.position }}
              </div>
              <div>
                <strong>Телефон:</strong> {{ employee.phone }}
              </div>
              {% if employee.internal_phone %}
                <div>
                  <strong>Внут.:</strong> {{ employee.internal_phone }}
                </div>
              {% endif %}
              {% if employee.email %}
                <div>
                  <strong>Email:</strong> {{ employee.email }}
                </div>
              {% endif %}
            </div>

            <div class="employee-actions">
              <button class="btn btn-sm btn-outline-info" hx-get="/api/employees/{{ employee.id }}/" hx-target="#employeeDetails" data-bs-toggle="modal" data-bs-target="#employeeDetailsModal"><i class="bi bi-info-circle"></i> Подробнее</button>

              {% if is_superuser %}
                <button class="btn btn-sm btn-outline-primary" hx-get="/api/employees/form/{{ employee.id }}/" hx-target="#modal-content" data-bs-toggle="modal" data-bs-target="#modal"><i class="bi bi-pencil"></i> Редактировать</button>

                <button class="btn btn-sm btn-outline-danger" hx-delete="/api/employees/delete/{{ employee.id }}/" hx-confirm="Вы уверены, что хотите удалить этого сотрудника?" hx-target="#employeesContent" hx-swap="innerHTML"><i class="bi bi-trash"></i> Удалить</button>
              {% endif %}
            </div>
          </div>
        {% endfor %}
      </div>
    {% else %}
      <div class="alert alert-info">
        <i class="bi bi-info-circle"></i> В этом подразделении нет сотрудников
      </div>
    {% endif %}

    <!-- Рекурсивный вывод дочерних подразделений -->
    {% if dept_data.children %}
      {% for child_data in dept_data.children %}
        {% include 'employees/employees_list_content.html' with dept_data=child_data %}
      {% endfor %}
    {% endif %}
  </div>
{% empty %}
  <div class="alert alert-info">
    <i class="bi bi-info-circle"></i> Сотрудники не найдены. Попробуйте изменить параметры поиска.
  </div>
{% endfor %}

<!-- Пагинация -->
{% if is_paginated %}
  <nav aria-label="Page navigation" class="mt-4">
    <ul class="pagination justify-content-center">
      {% if page_obj.has_previous %}
        <li class="page-item">
          <a class="page-link"
            href="?page={{ page_obj.previous_page_number }}{% if request.GET.query %}
              
              &query={{ request.GET.query }}
            {% endif %}{% if request.GET.department %}
              
              &department={{ request.GET.department }}
            {% endif %}">
            <i class="bi bi-chevron-left"></i> Назад
          </a>
        </li>
      {% endif %}

      {% for num in page_obj.paginator.page_range %}
        <li class="page-item {% if page_obj.number == num %}active{% endif %}">
          <a class="page-link"
            href="?page={{ num }}{% if request.GET.query %}
              
              &query={{ request.GET.query }}
            {% endif %}{% if request.GET.department %}
              
              &department={{ request.GET.department }}
            {% endif %}">
            {{ num }}
          </a>
        </li>
      {% endfor %}

      {% if page_obj.has_next %}
        <li class="page-item">
          <a class="page-link"
            href="?page={{ page_obj.next_page_number }}{% if request.GET.query %}
              
              &query={{ request.GET.query }}
            {% endif %}{% if request.GET.department %}
              
              &department={{ request.GET.department }}
            {% endif %}">
            Вперед <i class="bi bi-chevron-right"></i>
          </a>
        </li>
      {% endif %}
    </ul>
  </nav>
{% endif %}

```


-----

# Файл: templates\employees\import.html

```
{% extends 'layout/base.html' %}
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
                <li>Уровень иерархии (1-12)</li>
              </ol>
            </ul>
          </div>

          <form id="importForm" enctype="multipart/form-data">
            {% csrf_token %}
            <div class="mb-3">
              <label for="excel_file" class="form-label">Выберите Excel файл</label>
              <input type="file" class="form-control" id="excel_file" name="excel_file" accept=".xlsx" required />
            </div>

            <button type="submit" class="btn btn-primary" id="importBtn"><i class="bi bi-upload"></i> Загрузить файл</button>
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
  <script src="{% static 'js/import.js' %}"></script>
{% endblock %}

```


-----

# Файл: templates\employees\import_log.html

```
{% extends 'layout/base.html' %}

{% block content %}
  <div class="row">
    <div class="col-12">
      <div class="card">
        <div class="card-header d-flex justify-content-between align-items-center">
          <h4 class="card-title mb-0">История импорта</h4>
          <a href="{% url 'import' %}" class="btn btn-primary btn-sm"><i class="bi bi-arrow-left"></i> Назад к импорту</a>
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
                      <td>{{ log.uploaded_at|date:'d.m.Y H:i' }}</td>
                      <td>
                        <span class="badge
                                        {% if log.status == 'success' %}
                            bg-success

                          {% elif log.status == 'partial' %}
                            bg-warning

                          {% else %}
                            bg-danger
                          {% endif %}">
                          {{ log.get_status_display }}
                        </span>
                      </td>
                      <td>{{ log.total_records }}</td>
                      <td>{{ log.added }}</td>
                      <td>{{ log.updated }}</td>
                      <td>{{ log.user.username|default:'Система' }}</td>
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
{% extends 'layout/base.html' %}
{% load static %}

{% block content %}
  <div class="row">
    <!-- Левая панель - фильтры по подразделениям -->
    <div class="col-md-3">
      <div class="card">
        <div class="card-header">
          <h5 class="mb-0">Подразделения</h5>
        </div>
        <div class="card-body">
          <div class="department-tree">
            <div class="department-node">
              <div class="department-header level-0" hx-get="?department=" hx-target="#employeesContent" hx-swap="innerHTML">
                <i class="bi bi-building"></i> Все подразделения
              </div>
            </div>

            {% for dept_data in departments_tree %}
              {% include 'employees/department_node.html' with dept_data=dept_data level=0 %}
            {% endfor %}
          </div>
        </div>
      </div>
    </div>

    <!-- Правая панель - контент -->
    <div class="col-md-7">
      <!-- Поиск -->
      <div class="card search-section">
        <div class="card-body">
          <form method="get" class="row g-2">
            <div class="col-8 col-xl-10">
              <label class="form-label">Поиск сотрудников</label>
              {{ search_form.query }}
            </div>
            <div class="col-4 col-xl-2 d-flex align-items-end">
              <button type="submit" class="btn btn-primary w-100"><i class="bi bi-search"></i> Найти</button>
            </div>
          </form>

          <div id="searchResults" class="search-results mt-2" style="display: none;"></div>
        </div>
      </div>

      <!-- Кнопки действий для суперпользователя -->
      {% if is_superuser %}
        <div class="superuser-actions mb-3">
          <button class="btn btn-success" hx-get="/api/employees/form/" hx-target="#modal-content" hx-swap="innerHTML" data-bs-toggle="modal" data-bs-target="#modal"><i class="bi bi-plus-circle"></i> Добавить сотрудника</button>
          <a href="{% url 'import' %}" class="btn btn-primary"><i class="bi bi-upload"></i> Импорт данных</a>
        </div>
      {% endif %}

      <!-- Контент сотрудников -->
      <div id="employeesContent">
        {% include 'employees/employees_list_content.html' %}
      </div>
    </div>
  </div>

  <!-- Модальное окно для детальной информации -->
  <div class="modal fade" id="employeeDetailsModal" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Информация о сотруднике</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body" id="employeeDetails">Выберите сотрудника для просмотра информации</div>
      </div>
    </div>
  </div>
{% endblock %}

```
