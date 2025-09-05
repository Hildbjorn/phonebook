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
@login_required
@user_passes_test(is_superuser)
def employee_update_api(request, pk):
    """Обновление данных сотрудника"""
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