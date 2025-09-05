// Файл: static/js/employees.js

document.addEventListener('DOMContentLoaded', function () {
    initializeEmployeesPage();
});

function initializeEmployeesPage() {
    // Инициализация поиска
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(function (e) {
            const query = e.target.value.trim();
            if (query.length >= 2) {
                searchEmployees(query);
            } else {
                hideSearchResults();
            }
        }, 500));
    }

    // Обработка формы поиска
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const query = searchInput.value.trim();
            if (query) {
                window.location.href = `?query=${encodeURIComponent(query)}`;
            } else {
                window.location.href = '?';
            }
        });
    }

    // Инициализация модальных окон
    initModals();
}

// Функция для поиска сотрудников
function searchEmployees(query) {
    showLoading('searchResults');

    fetch(`/api/employees/search/?query=${encodeURIComponent(query)}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Ошибка сети');
            }
            return response.json();
        })
        .then(data => {
            displaySearchResults(data.results);
        })
        .catch(error => {
            console.error('Ошибка поиска:', error);
            showError('searchResults', 'Ошибка при поиске сотрудников');
        });
}

// Отображение результатов поиска
function displaySearchResults(results) {
    const container = document.getElementById('searchResults');
    if (!results || results.length === 0) {
        container.innerHTML = '<div class="search-result-item">Ничего не найдено</div>';
        container.style.display = 'block';
        return;
    }

    let html = '';
    results.forEach(employee => {
        html += `
            <div class="search-result-item" onclick="showEmployeeDetails(${employee.id})">
                <strong>${employee.full_name}</strong> - ${employee.position}<br>
                <small>${employee.department} | ${employee.phone}</small>
            </div>
        `;
    });

    container.innerHTML = html;
    container.style.display = 'block';
}

// Скрытие результатов поиска
function hideSearchResults() {
    const container = document.getElementById('searchResults');
    container.style.display = 'none';
}

// Загрузка сотрудников по подразделению
function loadDepartmentEmployees(departmentId) {
    showLoading('employeesContent');

    let url = '?';
    if (departmentId) {
        url += `department=${departmentId}`;
    }

    // Простая перезагрузка страницы с фильтром
    window.location.href = url;
}

// Показать детали сотрудника
function showEmployeeDetails(employeeId) {
    const modal = new bootstrap.Modal(document.getElementById('employeeDetailsModal'));
    const modalBody = document.getElementById('employeeDetails');

    modalBody.innerHTML = `
        <div class="text-center">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">Загрузка...</span>
            </div>
            <p>Загрузка информации...</p>
        </div>
    `;

    modal.show();

    fetch(`/api/employees/${employeeId}/`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Ошибка загрузки данных');
            }
            return response.json();
        })
        .then(data => {
            modalBody.innerHTML = `
                <div class="employee-details-content">
                    <h4>${data.full_name}</h4>
                    <div class="hierarchy-badge">${data.hierarchy}</div>
                    
                    <div class="details-grid">
                        <div class="detail-item">
                            <strong>Должность:</strong>
                            <span>${data.position}</span>
                        </div>
                        <div class="detail-item">
                            <strong>Подразделение:</strong>
                            <span>${data.department}</span>
                        </div>
                        <div class="detail-item">
                            <strong>Телефон:</strong>
                            <span>${data.phone}</span>
                        </div>
                        <div class="detail-item">
                            <strong>Внутренний телефон:</strong>
                            <span>${data.internal_phone}</span>
                        </div>
                        <div class="detail-item">
                            <strong>Email:</strong>
                            <span>${data.email}</span>
                        </div>
                        <div class="detail-item">
                            <strong>Кабинет:</strong>
                            <span>${data.room}</span>
                        </div>
                    </div>
                </div>
            `;
        })
        .catch(error => {
            console.error('Ошибка:', error);
            modalBody.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle"></i>
                    Ошибка при загрузке информации о сотруднике
                </div>
            `;
        });
}

// Загрузка формы сотрудника
function loadEmployeeForm(employeeId = null) {
    const modal = new bootstrap.Modal(document.getElementById('modal'));
    const modalContent = document.getElementById('modal-content');

    modalContent.innerHTML = `
        <div class="text-center">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">Загрузка...</span>
            </div>
            <p>Загрузка формы...</p>
        </div>
    `;

    let url = '/api/employees/form/';
    if (employeeId) {
        url += `${employeeId}/`;
    }

    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error('Ошибка загрузки формы');
            }
            return response.text();
        })
        .then(html => {
            modalContent.innerHTML = html;

            // Добавляем обработчик отправки формы
            const form = document.getElementById('employeeForm');
            if (form) {
                form.addEventListener('submit', handleEmployeeFormSubmit);
            }

            modal.show();
        })
        .catch(error => {
            console.error('Ошибка:', error);
            modalContent.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle"></i>
                    Ошибка при загрузке формы
                </div>
            `;
        });
}

// Обработчик отправки формы сотрудника
function handleEmployeeFormSubmit(e) {
    e.preventDefault();

    const form = e.target;
    const formData = new FormData(form);
    const url = form.action;
    const method = 'POST';

    const submitButton = form.querySelector('button[type="submit"]');
    const originalText = submitButton.innerHTML;
    submitButton.innerHTML = `
        <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
        Сохранение...
    `;
    submitButton.disabled = true;

    fetch(url, {
        method: method,
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Закрываем модальное окно и обновляем список
                const modal = bootstrap.Modal.getInstance(document.getElementById('modal'));
                modal.hide();

                // Показываем сообщение об успехе
                showNotification('Сотрудник успешно сохранен', 'success');

                // Обновляем содержимое страницы
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                // Показываем ошибки валидации
                showFormErrors(form, data.errors || data.error);
                submitButton.innerHTML = originalText;
                submitButton.disabled = false;
            }
        })
        .catch(error => {
            console.error('Ошибка:', error);
            showNotification('Ошибка при сохранении', 'error');
            submitButton.innerHTML = originalText;
            submitButton.disabled = false;
        });
}

// Удаление сотрудника
function deleteEmployee(employeeId) {
    if (!confirm('Вы уверены, что хотите удалить этого сотрудника?')) {
        return;
    }

    fetch(`/api/employees/delete/${employeeId}/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Сотрудник успешно удален', 'success');
                // Обновляем содержимое страницы
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                showNotification('Ошибка при удалении: ' + (data.error || 'Неизвестная ошибка'), 'error');
            }
        })
        .catch(error => {
            console.error('Ошибка:', error);
            showNotification('Ошибка при удалении сотрудника', 'error');
        });
}

// Вспомогательные функции
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
}

function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="text-center">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">Загрузка...</span>
                </div>
            </div>
        `;
    }
}

function showError(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle"></i>
                ${message}
            </div>
        `;
    }
}

function showNotification(message, type = 'info') {
    // Создаем уведомление
    const alertClass = type === 'success' ? 'alert-success' :
        type === 'error' ? 'alert-danger' : 'alert-info';

    const notification = document.createElement('div');
    notification.className = `alert ${alertClass} alert-dismissible fade show`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
    `;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(notification);

    // Автоматическое скрытие через 5 секунд
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}

function showFormErrors(form, errors) {
    // Очищаем предыдущие ошибки
    const errorElements = form.querySelectorAll('.error-message');
    errorElements.forEach(el => el.remove());

    const errorFields = form.querySelectorAll('.is-invalid');
    errorFields.forEach(el => el.classList.remove('is-invalid'));

    if (typeof errors === 'string') {
        // Общая ошибка
        showNotification(errors, 'error');
        return;
    }

    // Показываем ошибки для конкретных полей
    for (const field in errors) {
        const input = form.querySelector(`[name="${field}"]`);
        if (input) {
            input.classList.add('is-invalid');
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message text-danger small mt-1';
            errorDiv.textContent = errors[field];
            input.parentNode.appendChild(errorDiv);
        }
    }
}

function initModals() {
    // Очистка модальных окон при закрытии
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('hidden.bs.modal', function () {
            const modalContent = this.querySelector('.modal-content');
            if (modalContent) {
                modalContent.innerHTML = '';
            }
        });
    });
}