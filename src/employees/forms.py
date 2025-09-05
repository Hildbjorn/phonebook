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