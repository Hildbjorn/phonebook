from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
import pandas as pd
from .models import Employee, Department, ImportLog
from .forms import EmployeeForm, DepartmentForm, ImportForm

def employee_list(request):
    employees = Employee.objects.all()
    
    # Поиск
    search_query = request.GET.get('q', '')
    if search_query:
        employees = employees.filter(
            Q(full_name__icontains=search_query) |
            Q(position__icontains=search_query) |
            Q(department__name__icontains=search_query)
        )
    
    # Фильтрация по подразделению
    department_id = request.GET.get('department')
    if department_id:
        department = get_object_or_404(Department, id=department_id)
        descendants = department.get_descendants(include_self=True)
        employees = employees.filter(department__in=descendants)
    
    # Пагинация
    paginator = Paginator(employees, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    departments = Department.objects.all()
    
    context = {
        'page_obj': page_obj,
        'employees': page_obj.object_list,
        'departments': departments,
        'search_query': search_query,
    }
    
    if request.headers.get('HX-Request'):
        return render(request, 'employees/partials/employee_cards.html', context)
    
    return render(request, 'employees/list.html', context)

def employee_detail(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    return render(request, 'employees/partials/employee_detail.html', {'employee': employee})

def employee_create(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save()
            messages.success(request, _('Сотрудник успешно добавлен'))
            return HttpResponse('', status=204, headers={'HX-Trigger': 'employeeChanged'})
    else:
        form = EmployeeForm()
    
    return render(request, 'employees/partials/employee_form.html', {'form': form})

def employee_update(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, _('Данные сотрудника обновлены'))
            return HttpResponse('', status=204, headers={'HX-Trigger': 'employeeChanged'})
    else:
        form = EmployeeForm(instance=employee)
    
    return render(request, 'employees/partials/employee_form.html', {'form': form})

def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    
    if request.method == 'POST':
        employee.delete()
        messages.success(request, _('Сотрудник удален'))
        return HttpResponse('', status=204, headers={'HX-Trigger': 'employeeChanged'})
    
    return render(request, 'employees/partials/confirm_delete.html', {'employee': employee})

def department_tree(request):
    departments = Department.objects.all()
    return render(request, 'employees/partials/department_tree.html', {'departments': departments})

def import_excel(request):
    if request.method == 'POST':
        form = ImportForm(request.POST, request.FILES)
        if form.is_valid():
            # Обработка Excel файла
            try:
                df = pd.read_excel(request.FILES['excel_file'])
                # Здесь должна быть логика обработки данных
                messages.success(request, _('Данные успешно импортированы'))
                return redirect('employee_list')
            except Exception as e:
                messages.error(request, f'Ошибка импорта: {str(e)}')
    
    else:
        form = ImportForm()
    
    return render(request, 'employees/import.html', {'form': form})