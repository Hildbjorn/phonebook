"""
Настройки маршрутов проекта PhoneBook
Copyright (c) 2025 Artem Fomin
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('employees.urls')),
]