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
