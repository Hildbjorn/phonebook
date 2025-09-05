from django import forms
from .models import Employee

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = '__all__'
        widgets = {
            'initials': forms.TextInput(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'department1': forms.TextInput(attrs={'class': 'form-control'}),
            'department2': forms.TextInput(attrs={'class': 'form-control'}),
            'department3': forms.TextInput(attrs={'class': 'form-control'}),
            'department4': forms.TextInput(attrs={'class': 'form-control'}),
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
    department = forms.CharField(required=False, widget=forms.HiddenInput())
    hierarchy = forms.IntegerField(required=False, widget=forms.HiddenInput())
