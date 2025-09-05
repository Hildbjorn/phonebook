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