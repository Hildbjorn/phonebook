from .models import Employee, ImportLog

def admin_stats(request):
    if request.path.startswith('/admin/'):
        return {
            'employees_count': Employee.objects.count(),
            'import_logs_count': ImportLog.objects.count(),
        }
    return {}
