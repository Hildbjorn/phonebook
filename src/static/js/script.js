// Файл: static/js/main.js

// Основные функции для всего сайта
document.addEventListener('DOMContentLoaded', function () {
    initializeMainFeatures();
});

function initializeMainFeatures() {
    // Инициализация кнопки "Наверх"
    initScrollToTop();

    // Инициализация всех tooltips
    initTooltips();

    // Инициализация всех popovers
    initPopovers();

    // Обработка CSRF токенов для AJAX запросов
    initCSRF();
}

// Кнопка "Наверх"
function initScrollToTop() {
    const scrollToTopBtn = document.getElementById('scrollToTop');
    if (scrollToTopBtn) {
        window.addEventListener('scroll', function () {
            if (window.pageYOffset > 300) {
                scrollToTopBtn.style.display = 'block';
            } else {
                scrollToTopBtn.style.display = 'none';
            }
        });

        scrollToTopBtn.addEventListener('click', function (e) {
            e.preventDefault();
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
}

// Инициализация tooltips
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Инициализация popovers
function initPopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// CSRF токены для AJAX
function initCSRF() {
    // Устанавливаем CSRF токен для всех AJAX запросов
    const csrftoken = getCSRFToken();

    // Функция для получения CSRF токена
    window.getCSRFToken = function () {
        return csrftoken || document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    };

    // Добавляем CSRF токен ко всем AJAX запросам
    const originalFetch = window.fetch;
    window.fetch = function (...args) {
        const [url, options = {}] = args;

        if (options.method && options.method !== 'GET') {
            options.headers = options.headers || {};
            options.headers['X-CSRFToken'] = getCSRFToken();
        }

        return originalFetch.call(this, url, options);
    };
}

// Утилитарные функции
function formatPhoneNumber(phone) {
    if (!phone) return '';

    // Простой форматтер телефонов
    const cleaned = phone.replace(/\D/g, '');

    if (cleaned.length === 11) {
        return `+7 (${cleaned.substring(1, 4)}) ${cleaned.substring(4, 7)}-${cleaned.substring(7, 9)}-${cleaned.substring(9)}`;
    }

    if (cleaned.length === 10) {
        return `+7 (${cleaned.substring(0, 3)}) ${cleaned.substring(3, 6)}-${cleaned.substring(6, 8)}-${cleaned.substring(8)}`;
    }

    return phone;
}

// Дебаунс функция
function debounce(func, wait, immediate) {
    let timeout;
    return function () {
        const context = this, args = arguments;
        const later = function () {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}

// Форматирование даты
function formatDate(dateString, format = 'dd.MM.yyyy') {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return dateString;

    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear();
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');

    return format
        .replace('dd', day)
        .replace('MM', month)
        .replace('yyyy', year)
        .replace('HH', hours)
        .replace('mm', minutes);
}

// Валидация email
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Копирование в буфер обмена
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Скопировано в буфер обмена', 'success');
    }).catch(err => {
        console.error('Ошибка копирования:', err);
        showNotification('Ошибка при копировании', 'error');
    });
}