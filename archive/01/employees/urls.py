from django.urls import path
from . import views

urlpatterns = [
    path('', views.EmployeeListView.as_view(), name='employee_list'),
    path('api/employees/', views.employee_search_api, name='employee_search_api'),
    path('api/employees/<int:pk>/', views.employee_detail_api, name='employee_detail_api'),
    path('api/employees/create/', views.employee_create_api, name='employee_create_api'),
    path('api/employees/update/<int:pk>/', views.employee_update_api, name='employee_update_api'),
    path('api/employees/delete/<int:pk>/', views.employee_delete_api, name='employee_delete_api'),
    path('import/', views.ImportView.as_view(), name='import'),
    path('import/log/', views.ImportLogListView.as_view(), name='import_log'),
]
