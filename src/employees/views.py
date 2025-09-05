import pandas as pd
import re
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, View, TemplateView, CreateView, UpdateView, DeleteView
from django.db import transaction, models
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse_lazy, reverse
from django.contrib import messages

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
                all_departments = [department] + list(department.get_all_children())
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

class EmployeeSearchAPIView(View):
    """
    API endpoint для поиска сотрудников
    """
    def get(self, request):
        query = request.GET.get('query', '').strip()

        if not query or len(query) < 2:
            return JsonResponse({'results': []})

        employees = Employee.objects.select_related('department').filter(
            models.Q(full_name__icontains=query) |
            models.Q(position__icontains=query) |
            models.Q(department__name__icontains=query) |
            models.Q(phone__icontains=query)
        )[:15]

        results = [
            {
                'id': emp.id,
                'full_name': emp.full_name,
                'position': emp.position,
                'department': emp.department.name if emp.department else "Без подразделения",
                'phone': emp.phone
            }
            for emp in employees
        ]

        return JsonResponse({'results': results})

class EmployeeDetailAPIView(View):
    """
    API endpoint для получения детальной информации о сотруднике
    """
    def get(self, request, pk):
        employee = get_object_or_404(Employee, pk=pk)
        
        data = {
            'full_name': employee.full_name,
            'position': employee.position,
            'department': employee.department.get_full_path() if employee.department else 'Не указано',
            'phone': employee.phone,
            'internal_phone': employee.internal_phone,
            'email': employee.email or 'Не указан',
            'room': employee.room or 'Не указан',
            'hierarchy': employee.get_hierarchy_display()
        }
        
        return JsonResponse(data)

class ImportView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Представление для импорта данных из Excel (только для суперпользователей)
    """
    template_name = 'employees/import.html'

    def test_func(self):
        return self.request.user.is_superuser

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

class ImportLogListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Представление для просмотра логов импорта (только для суперпользователей)
    """
    model = ImportLog
    template_name = 'employees/import_log.html'
    context_object_name = 'import_logs'
    paginate_by = 20
    ordering = ['-uploaded_at']

    def test_func(self):
        return self.request.user.is_superuser

class EmployeeFormAPIView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    API endpoint для получения HTML формы сотрудника
    """
    def test_func(self):
        return self.request.user.is_superuser

    def get(self, request, pk=None):
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
            <form id="employeeForm" method="post" action="{'/api/employees/update/' + str(pk) + '/' if pk else '/api/employees/create/'}">
                {form.as_p()}
                <input type="hidden" name="csrfmiddlewaretoken" value="{request.META['CSRF_COOKIE']}">
            </form>
        </div>
        <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Отмена</button>
            <button type="submit" form="employeeForm" class="btn btn-primary">Сохранить</button>
        </div>
        """
        
        return HttpResponse(html)

class EmployeeCreateAPIView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Создание нового сотрудника"""
    
    def test_func(self):
        return self.request.user.is_superuser

    def post(self, request):
        try:
            form = EmployeeForm(request.POST)
            if form.is_valid():
                employee = form.save()
                return JsonResponse({'success': True, 'id': employee.id})
            return JsonResponse({'success': False, 'errors': form.errors})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

class EmployeeUpdateAPIView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Обновление данных сотрудника"""
    
    def test_func(self):
        return self.request.user.is_superuser

    def post(self, request, pk):
        try:
            employee = get_object_or_404(Employee, pk=pk)
            form = EmployeeForm(request.POST, instance=employee)
            if form.is_valid():
                employee = form.save()
                return JsonResponse({'success': True, 'id': employee.id})
            return JsonResponse({'success': False, 'errors': form.errors})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

class EmployeeDeleteAPIView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Удаление сотрудника"""
    
    def test_func(self):
        return self.request.user.is_superuser

    def delete(self, request, pk):
        try:
            employee = get_object_or_404(Employee, pk=pk)
            employee.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

# Альтернативные классовые представления для CRUD операций
class EmployeeCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Создание сотрудника через стандартное Django представление"""
    model = Employee
    form_class = EmployeeForm
    template_name = 'employees/employee_form.html'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def get_success_url(self):
        return reverse('employee_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Сотрудник успешно создан')
        return super().form_valid(form)

class EmployeeUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редактирование сотрудника через стандартное Django представление"""
    model = Employee
    form_class = EmployeeForm
    template_name = 'employees/employee_form.html'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def get_success_url(self):
        return reverse('employee_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Сотрудник успешно обновлен')
        return super().form_valid(form)

class EmployeeDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Удаление сотрудника через стандартное Django представление"""
    model = Employee
    template_name = 'employees/employee_confirm_delete.html'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def get_success_url(self):
        return reverse('employee_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Сотрудник успешно удален')
        return super().delete(request, *args, **kwargs)