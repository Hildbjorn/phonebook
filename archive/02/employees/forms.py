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
