from django.db import models
from django.contrib.auth.models import User

class Employee(models.Model):
    HIERARCHY_LEVELS = [
        (1, 'Высшее руководство'),
        (2, 'Руководство'),
        (3, 'Менеджеры'),
        (4, 'Специалисты'),
        (5, 'Ассистенты'),
    ]

    initials = models.CharField(max_length=50, verbose_name="Инициалы")
    full_name = models.CharField(max_length=200, verbose_name="ФИО")
    position = models.CharField(max_length=200, verbose_name="Должность")
    department1 = models.CharField(max_length=200, blank=True, verbose_name="Структурное подразделение 1")
    department2 = models.CharField(max_length=200, blank=True, verbose_name="Структурное подразделение 2")
    department3 = models.CharField(max_length=200, blank=True, verbose_name="Структурное подразделение 3")
    department4 = models.CharField(max_length=200, blank=True, verbose_name="Структурное подразделение 4")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    internal_phone = models.CharField(max_length=20, verbose_name="Внутренний телефон")
    email = models.EmailField(blank=True, verbose_name="Email")
    room = models.CharField(max_length=50, blank=True, verbose_name="Кабинет")
    hierarchy = models.IntegerField(choices=HIERARCHY_LEVELS, default=3, verbose_name="Уровень иерархии")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['hierarchy', 'full_name']
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'
        unique_together = ['full_name', 'internal_phone']

    def __str__(self):
        return f"{self.full_name} ({self.position})"

class ImportLog(models.Model):
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
