from django.db import models
from django.contrib.auth.models import User

class Department(models.Model):
    """
    Модель структурного подразделения с иерархической структурой
    """
    name = models.CharField(max_length=200, verbose_name="Название")
    short_name = models.CharField(max_length=50, blank=True, verbose_name="Короткое название")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                              verbose_name="Родительское подразделение")
    level = models.IntegerField(default=1, verbose_name="Уровень")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['level', 'name']
        verbose_name = 'Структурное подразделение'
        verbose_name_plural = 'Структурные подразделения'

    def __str__(self):
        return self.name

    def get_full_path(self):
        """Возвращает полный путь подразделения в иерархии"""
        parts = []
        current = self
        while current:
            parts.append(current.name)
            current = current.parent
        return ' → '.join(reversed(parts))

    def get_all_children(self):
        """Возвращает все дочерние подразделения рекурсивно"""
        children = list(self.children.all())
        for child in self.children.all():
            children.extend(child.get_all_children())
        return children

    def get_tree_data(self):
        """Возвращает данные для древовидного отображения"""
        return {
            'id': self.id,
            'name': self.name,
            'short_name': self.short_name,
            'level': self.level,
            'children': [child.get_tree_data() for child in self.children.all().order_by('name')]
        }


class Employee(models.Model):
    """
    Модель сотрудника/абонента телефонной книги
    """
    HIERARCHY_LEVELS = [
        (1, 'Высшее руководство (ГД)'),
        (2, 'Первые заместители'),
        (3, 'Заместители'),
        (4, 'Руководители центров'),
        (5, 'Руководители управлений'),
        (6, 'Руководители отделов'),
        (7, 'Специалисты'),
        (8, 'Ассистенты'),
    ]

    initials = models.CharField(max_length=50, verbose_name="Инициалы")
    full_name = models.CharField(max_length=200, verbose_name="ФИО")
    position = models.CharField(max_length=200, verbose_name="Должность")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True,
                                  blank=True, verbose_name="Подразделение")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    internal_phone = models.CharField(max_length=20, verbose_name="Внутренний телефон")
    email = models.EmailField(blank=True, verbose_name="Email")
    room = models.CharField(max_length=50, blank=True, verbose_name="Кабинет")
    hierarchy = models.IntegerField(choices=HIERARCHY_LEVELS, default=7, verbose_name="Уровень иерархии")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['department__level', 'department__name', 'hierarchy', 'full_name']
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'
        unique_together = ['full_name', 'internal_phone']

    def __str__(self):
        return f"{self.full_name} ({self.position})"

    def get_hierarchy_display(self):
        """Возвращает отображаемое название уровня иерархии"""
        return dict(self.HIERARCHY_LEVELS).get(self.hierarchy, 'Неизвестно')


class ImportLog(models.Model):
    """
    Модель для логирования операций импорта данных
    """
    STATUS_CHOICES = [
        ('success', 'Успешно'),
        ('partial', 'Частично'),
        ('failed', 'Не удалось'),
    ]

    file_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    total_records = models.IntegerField()
    added = models.IntegerField()
    updated = models.IntegerField()
    errors = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Лог импорта'
        verbose_name_plural = 'Логи импорта'

    def get_status_display(self):
        """Возвращает отображаемое название статуса"""
        return dict(self.STATUS_CHOICES).get(self.status, 'Неизвестно')