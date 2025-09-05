"""
Настройки проекта PhoneBook
Copyright (c) 2025 Artem Fomin
"""

import os
from pathlib import Path

# Базовый директория проекта (корневая папка проекта)
BASE_DIR = Path(__file__).resolve().parent.parent

# Секретный ключ приложения
SECRET_KEY = 'django-insecure-j(_g+2t(2xu##w+t4gp%3m9j1lwprgvylndda@u)xw@oh80s&-'

# Режим отладки (включать только для разработки!)
DEBUG = True

ALLOWED_HOSTS = []

# Установленные приложения проекта
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Сторонние приложения
    'django_htmx',           # HTMX интеграция
    'django_bootstrap5',     # Bootstrap 5
    'sass_processor',        # Компилятор SASS/SCSS
    'widget_tweaks',         # Улучшение виджетов форм
    # Приложения проекта
    'employees'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware', # HTMX поддержка
]

# Корневой конфигуратор URL
ROOT_URLCONF = 'phonebook.urls'

# Настройки шаблонов
TEMPLATES_BASE_DIR = os.path.join(BASE_DIR, 'templates')
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATES_BASE_DIR],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Корневое приложение WSGI
WSGI_APPLICATION = 'phonebook.wsgi.application'

# Конфигурация базы данных
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'phonebook_db.sqlite3',
    }
}

# Валидаторы паролей
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Языковые настройки
LANGUAGE_CODE = 'ru'                  # Язык по умолчанию
TIME_ZONE = 'Europe/Moscow'           # Часовой пояс
USE_I18N = True                       # Включение интернационализации
USE_L10N = True                       # Включение локализации
USE_TZ = True                         # Использование часовых поясов

# Конфигурация статических файлов (CSS, JavaScript, изображения)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR.joinpath('static')]  # Папки со статикой
STATIC_ROOT = BASE_DIR.joinpath('staticfiles')    # Финалная сборка статики

# Обработчики поиска статических файлов
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'sass_processor.finders.CssFinder',  # Для обработки SASS
]

# Медиа-файлы (загружаемые пользователями)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR.joinpath('media')

# Авто-поле для моделей
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Настройки Bootstrap 5
BOOTSTRAP5 = {
    "javascript_url": {
        "url": "/static/bootstrap/js/bootstrap.bundle.min.js",
    },
}

# Настройки иконок
DJANGO_ICONS = {
    "DEFAULT": {
        "renderer": "django_icons_bootstrap_icons.BootstrapIconRenderer"
    }
}

# Путь для хранения скомпилированных CSS-файлов
SASS_PROCESSOR_ROOT = STATIC_ROOT