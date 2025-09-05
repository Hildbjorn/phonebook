from django.urls import path
from . import views

urlpatterns = [
    path('', views.EmployeeListView.as_view(), name='employee_list'),
    path('import/', views.ImportView.as_view(), name='import'),
    path('import/log/', views.ImportLogListView.as_view(), name='import_log'),
    
    # API endpoints
    path('api/employees/search/', views.EmployeeSearchAPIView.as_view(), name='employee_search_api'),
    path('api/employees/<int:pk>/', views.EmployeeDetailAPIView.as_view(), name='employee_detail_api'),
    path('api/employees/form/', views.EmployeeFormAPIView.as_view(), name='employee_form_create'),
    path('api/employees/form/<int:pk>/', views.EmployeeFormAPIView.as_view(), name='employee_form_update'),
    path('api/employees/create/', views.EmployeeCreateAPIView.as_view(), name='employee_create_api'),
    path('api/employees/update/<int:pk>/', views.EmployeeUpdateAPIView.as_view(), name='employee_update_api'),
    path('api/employees/delete/<int:pk>/', views.EmployeeDeleteAPIView.as_view(), name='employee_delete_api'),
    
    # Стандартные Django CRUD представления (альтернатива)
    path('employee/create/', views.EmployeeCreateView.as_view(), name='employee_create'),
    path('employee/update/<int:pk>/', views.EmployeeUpdateView.as_view(), name='employee_update'),
    path('employee/delete/<int:pk>/', views.EmployeeDeleteView.as_view(), name='employee_delete'),
]