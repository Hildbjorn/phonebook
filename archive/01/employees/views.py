import pandas as pd
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction, models, connection  # ← Добавляем connection
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

from .models import Employee, ImportLog
from .forms import EmployeeForm, ImportForm, SearchForm


from django.views.decorators.csrf import csrf_protect


class EmployeeListView(ListView):
    model = Employee
    template_name = 'employees/list.html'
    context_object_name = 'employees'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('query')
        department = self.request.GET.get('department')
        hierarchy = self.request.GET.get('hierarchy')

        if query:
            queryset = queryset.filter(
                models.Q(full_name__icontains=query) |
                models.Q(position__icontains=query) |
                models.Q(department1__icontains=query) |
                models.Q(department2__icontains=query) |
                models.Q(department3__icontains=query) |
                models.Q(department4__icontains=query)
            )

        if department:
            queryset = queryset.filter(
                models.Q(department1__icontains=department) |
                models.Q(department2__icontains=department) |
                models.Q(department3__icontains=department) |
                models.Q(department4__icontains=department)
            )

        if hierarchy:
            queryset = queryset.filter(hierarchy=hierarchy)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = SearchForm(self.request.GET or None)
        return context

@require_http_methods(["GET"])
def employee_detail_api(request, pk):
    try:
        employee = get_object_or_404(Employee, pk=pk)
        data = {
            'id': employee.id,
            'initials': employee.initials,
            'full_name': employee.full_name,
            'position': employee.position,
            'department1': employee.department1,
            'department2': employee.department2,
            'department3': employee.department3,
            'department4': employee.department4,
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

def sqlite_icontains_search(query):
    """Регистронезависимый поиск для SQLite"""
    try:
        # Создаем функцию для регистронезависимого поиска в SQLite
        def icontains(text, pattern):
            if text is None:
                return False
            return pattern.lower() in text.lower()

        # Регистрируем функцию в SQLite
        connection.connection.create_function("icontains", 2, icontains)

        return Employee.objects.extra(
            where=[f"icontains(full_name, %s) OR icontains(position, %s) OR "
                   f"icontains(department1, %s) OR icontains(department2, %s) OR "
                   f"icontains(department3, %s) OR icontains(department4, %s)"],
            params=[query] * 6
        )[:10]
    except Exception as e:
        # Если возникла ошибка, возвращаем пустой queryset
        print(f"Error in sqlite_icontains_search: {e}")
        return Employee.objects.none()

@require_http_methods(["GET"])
def employee_search_api(request):
    query = request.GET.get('query', '').strip()

    if not query or len(query) < 2:
        return JsonResponse({'results': []})

    try:
        # Получаем всех сотрудников без ограничения
        all_employees = Employee.objects.all()

        query_lower = query.lower()
        results = []

        for emp in all_employees:
            # Проверяем все текстовые поля на совпадение (регистронезависимо)
            search_fields = [
                emp.full_name or '',
                emp.position or '',
                emp.department1 or '',
                emp.department2 or '',
                emp.department3 or '',
                emp.department4 or '',
                emp.room or '',
                emp.internal_phone or '',
                emp.email or ''  # Добавляем email в поиск
            ]

            # Проверяем, содержится ли запрос в любом из полей (регистронезависимо)
            if any(query_lower in (field or '').lower() for field in search_fields):
                results.append({
                    'id': emp.id,
                    'full_name': emp.full_name,
                    'position': emp.position,
                    'department': emp.department1 or emp.department2 or emp.department3 or emp.department4 or '',
                    'phone': emp.phone,
                    'room': emp.room or '',
                    'internal_phone': emp.internal_phone or '',
                    'email': emp.email or ''
                })

                # Ограничиваем количество результатов для производительности
                if len(results) >= 20:  # Увеличиваем лимит
                    break

        # Сортируем результаты по релевантности (сначала полные совпадения в ФИО)
        results.sort(key=lambda x: (
            query_lower not in (x['full_name'] or '').lower(),  # Сначала те, у кого запрос в ФИО
            query_lower not in (x['position'] or '').lower(),   # Затем в должности
            x['full_name']  # Затем по алфавиту
        ))

        return JsonResponse({'results': results[:15]})  # Возвращаем топ-15 результатов

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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
            df = pd.read_excel(file, dtype=str)  # Читаем все как строки
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
                            return '' if not is_level else 3

                        value_str = str(value).strip()

                        if is_level:
                            try:
                                return int(float(value_str)) if value_str else 3
                            except (ValueError, TypeError):
                                return 3
                        return value_str

                    employee_data = {
                        'initials': clean_value(row['Инициалы']),
                        'full_name': clean_value(row['ФИО']),
                        'position': clean_value(row['Должность']),
                        'department1': clean_value(row['Структурное подразделение 1']),
                        'department2': clean_value(row['Структурное подразделение 2']),
                        'department3': clean_value(row['Структурное подразделение 3']),
                        'department4': clean_value(row['Структурное подразделение 4']),
                        'phone': clean_value(row['Телефон']),
                        'internal_phone': clean_value(row['Внутренний телефон']),
                        'room': clean_value(row['Кабинет']),
                        'hierarchy': clean_value(row['Уровень'], is_level=True),
                    }

                    # Валидация обязательных полей
                    if not employee_data['full_name']:
                        errors.append(f"Строка {index + 2}: Отсутствует ФИО")
                        continue

                    # Валидация уровня иерархии
                    if employee_data['hierarchy'] not in [1, 2, 3, 4, 5]:
                        errors.append(f"Строка {index + 2}: Неверный уровень иерархии: {employee_data['hierarchy']}")
                        employee_data['hierarchy'] = 3  # Устанавливаем значение по умолчанию

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
