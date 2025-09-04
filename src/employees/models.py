from django.db import models
from django.contrib.auth.models import User
from mptt.models import MPTTModel, TreeForeignKey
from django.utils.translation import gettext_lazy as _

class Department(MPTTModel):
    name = models.CharField(max_length=200, verbose_name=_("Название"))
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_("Родительское подразделение")
    )
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class MPTTMeta:
        order_insertion_by = ['name']
    
    class Meta:
        verbose_name = _('Подразделение')
        verbose_name_plural = _('Подразделения')
    
    def __str__(self):
        return self.name

class Employee(models.Model):
    HIERARCHY_LEVELS = [
        (1, _('Высшее руководство')),
        (2, _('Руководство')),
        (3, _('Менеджеры')),
        (4, _('Специалисты')),
        (5, _('Ассистенты')),
    ]
    
    # Основная информация
    initials = models.CharField(max_length=50, verbose_name=_("Инициалы"))
    full_name = models.CharField(max_length=200, verbose_name=_("ФИО"))
    position = models.CharField(max_length=200, verbose_name=_("Должность"))
    
    # Связь с подразделением
    department = TreeForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Подразделение")
    )
    
    # Контактная информация
    phone = models.CharField(max_length=20, verbose_name=_("Телефон"))
    internal_phone = models.CharField(max_length=20, verbose_name=_("Внутренний телефон"))
    email = models.EmailField(blank=True, verbose_name=_("Email"))
    room = models.CharField(max_length=50, blank=True, verbose_name=_("Кабинет"))
    
    # Системная информация
    hierarchy = models.IntegerField(choices=HIERARCHY_LEVELS, default=3, verbose_name=_("Уровень иерархии"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['hierarchy', 'full_name']
        verbose_name = _('Сотрудник')
        verbose_name_plural = _('Сотрудники')
        unique_together = ['full_name', 'internal_phone']
    
    def __str__(self):
        return f"{self.full_name} ({self.position})"

class ImportLog(models.Model):
    STATUS_CHOICES = [
        ('success', _('Успешно')),
        ('partial', _('Частично')),
        ('failed', _('Не удалось')),
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
        verbose_name = _('Лог импорта')
        verbose_name_plural = _('Логи импорта')