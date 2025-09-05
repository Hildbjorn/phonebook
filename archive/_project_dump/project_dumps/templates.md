# Файл: layout\base.html

```
<!DOCTYPE html>

{% load static %}
{% load sass_tags %}
{% load django_bootstrap5 %}

<html lang="ru">
  <head>
    <!-- === БАЗОВЫЕ НАСТРОЙКИ === -->
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />

    <!-- === ЗАЩИТА И БЕЗОПАСНОСТЬ === -->
    <meta name="csrfmiddlewaretoken" content="{{ csrf_token }}" />

    <!-- === СТИЛИ === -->
    <!-- Основные стили проекта (компилируются из Sass) -->
    <link href="{% sass_src 'css/style.scss' %}" rel="stylesheet" type="text/css" />

    <!-- === СКРИПТЫ === -->
    <!-- HTMX - библиотека для AJAX-запросов и динамического обновления контента -->
    <script src="{% static 'htmx/htmx.min.js' %}"></script>

    <!-- Bootstrap JavaScript (включает Popper.js для всплывающих элементов) -->
    {% bootstrap_javascript %}

    <!-- jQuery (основная зависимость для многих плагинов) -->
    <script src="{% static 'js/jquery-3.7.1.min.js' %}"></script>

    <!-- Основные скрипты проекта (кастомная логика) -->
    <script type="text/javascript" src="{% static 'js/script.js' %}"></script>

    <!-- === Блок стилей отдельных страниц (если будут) === -->
    {% block extra_css %}

    {% endblock %}

    <!-- === ЗАГОЛОВОК И ФАВИКОНКИ === -->
    <title>
      {% block title %}
        Телефонный справочник
      {% endblock %}
    </title>

    <!-- Фавиконки для всех устройств и браузеров -->
    {% include 'layout/components/favicons.html' %}

    <!-- === ДОПОЛНИТЕЛЬНЫЕ МЕТА-ТЕГИ === -->
    {% block meta_tags %}

    {% endblock %}
  </head>
  <!-- === ТЕЛО СТРАНИЦЫ === -->
  <body>
    <!-- Контейнер для всех модальных окон -->
    {% include 'layout/components/modal.html' %}

    <!-- Шапка сайта (навигация, логотип и т.д.) -->
    {% include 'layout/components/header.html' %}

    <div class="container-fluid mt-4">
      <!-- ==================== Основной контент ==================== -->
      {% block content %}

      {% endblock %}
      <!-- ========================================================== -->
    </div>

    <!-- Кнопка "Наверх" -->
    {% include 'layout/components/scroll_to_top.html' %}
  </body>
</html>

```


-----

# Файл: layout\components\favicons.html

```
{% load static %}
<!-- ========== FAVICONS И МЕТА-ТЕГИ ДЛЯ РАЗЛИЧНЫХ УСТРОЙСТВ ========== -->
<!-- Полный набор favicon для всех устройств и браузеров Сгенерировано с помощью https://realfavicongenerator.net -->

<!-- Стандартные favicon -->
<link rel="apple-touch-icon" sizes="180x180" href="{% static 'img/favicons/apple-touch-icon.png' %}" />
<link rel="icon" type="image/png" sizes="32x32" href="{% static 'img/favicons/favicon-32x32.png' %}" />
<link rel="icon" type="image/png" sizes="16x16" href="{% static 'img/favicons/favicon-16x16.png' %}" />

<!-- WebApp манифест -->
<link rel="manifest" href="{% static 'img/favicons/site.webmanifest' %}" />

<!-- Safari pinned tab icon -->
<link rel="mask-icon" href="{% static 'img/favicons/safari-pinned-tab.svg' %}" color="#00aba9" />

<!-- Короткая иконка -->
<link rel="shortcut icon" href="{% static 'img/favicons/favicon.ico' %}" />

<!-- Мета-теги для Apple и Windows -->
<meta name="apple-mobile-web-app-title" content="B-Model" />
<meta name="application-name" content="B-Model" />
<meta name="msapplication-TileColor" content="#00aba9" />
<meta name="msapplication-config" content="{% static 'img/favicons/browserconfig.xml' %}" />

<!-- Цвет темы -->
<meta name="theme-color" content="#ffffff" />

```


-----

# Файл: layout\components\header.html

```
{% load static %}

<nav class="navbar navbar-expand-lg navbar-dark bg-primary">
  <div class="container">
    <a class="navbar-brand" href="{% url 'employee_list' %}"><i class="bi bi-telephone me-2"></i>Телефонный справочник</a>

    <div class="collapse navbar-collapse">
      <div class="navbar-nav ms-auto">
        <a class="nav-link" href="{% url 'employee_list' %}"><i class="bi bi-people me-1"></i>Сотрудники</a>

        {% if user.is_superuser %}
          <a class="nav-link" href="{% url 'import' %}"><i class="bi bi-upload me-1"></i>Импорт</a>
          <a class="nav-link" href="{% url 'import_log' %}"><i class="bi bi-clock-history me-1"></i>История импорта</a>
        {% endif %}

        {% if user.is_authenticated %}
          <span class="nav-link">Пользователь: {{ user.username }}</span>
        {% endif %}
      </div>
    </div>
  </div>
</nav>

```


-----

# Файл: layout\components\modal.html

```
{% load static %}
<!-- ========== УНИВЕРСАЛЬНОЕ МОДАЛЬНОЕ ОКНО ========== -->
<div class="modal fade" id="modal" data-bs-backdrop="static" data-bs-keyboard="false" tabindex="-1" aria-labelledby="modal" aria-hidden="true">
  <div class="modal-dialog modal-dialog-centered modal-dialog-scrollable modal-lg">
    <div class="modal-content" id="modal-content">
      <!-- Контент будет подгружаться динамически через HTMX -->
    </div>
  </div>
</div>

<!-- ========== БОЛЬШОЕ МОДАЛЬНОЕ ОКНО ДЛЯ ДОКУМЕНТОВ ========== -->
<div class="modal fade" id="largeModal" data-bs-backdrop="static" data-bs-keyboard="false" tabindex="-1" aria-labelledby="largeModal" aria-hidden="true">
  <div class="modal-dialog modal-dialog-centered modal-dialog-scrollable modal-xl">
    <div class="modal-content" id="largeModal-content">
      <!-- Контент будет подгружаться динамически через HTMX -->
    </div>
  </div>
</div>

```


-----

# Файл: layout\components\scroll_to_top.html

```
{% load static %}
<a href="#" class="btn btn-light rounded-circle scroll-to-top" id="scrollToTop" style="display: none; position: fixed; bottom: 1rem; right: 1rem; width: 40px; height: 40px; z-index: 1000;"><i class="bi bi-arrow-up"></i></a>

```
