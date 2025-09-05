class EmployeeManager {
    constructor() {
        this.currentEmployeeId = null;
        this.modal = new bootstrap.Modal(document.getElementById('employeeModal'));
        this.deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));
        this.initEventListeners();
    }

    initEventListeners() {
        // Обработка формы сотрудника
        document.getElementById('employeeForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveEmployee();
        });

        // Обработка кнопок редактирования
        document.addEventListener('click', (e) => {
            if (e.target.closest('.edit-btn')) {
                const btn = e.target.closest('.edit-btn');
                this.editEmployee(btn.dataset.id);
            }

            if (e.target.closest('.delete-btn')) {
                const btn = e.target.closest('.delete-btn');
                this.prepareDelete(btn.dataset.id);
            }
        });

        // Подтверждение удаления
        document.getElementById('confirmDelete').addEventListener('click', () => {
            this.deleteEmployee();
        });

        // Сброс формы при закрытии модального окна
        document.getElementById('employeeModal').addEventListener('hidden.bs.modal', () => {
            this.resetForm();
        });
    }

    async editEmployee(id) {
        try {
            const response = await fetch(`/api/employees/${id}/`);
            if (!response.ok) throw new Error('Ошибка загрузки данных');

            const employee = await response.json();
            this.fillForm(employee);
            this.currentEmployeeId = id;
            document.getElementById('modalTitle').textContent = 'Редактировать сотрудника';
        } catch (error) {
            alert('Ошибка при загрузке данных: ' + error.message);
        }
    }

    fillForm(data) {
        const form = document.getElementById('employeeForm');
        for (const [key, value] of Object.entries(data)) {
            const input = form.querySelector(`[name="${key}"]`);
            if (input) {
                input.value = value || '';
            }
        }
    }

    async saveEmployee() {
        const formData = new FormData(document.getElementById('employeeForm'));
        const data = Object.fromEntries(formData.entries());

        try {
            const url = this.currentEmployeeId
                ? `/api/employees/update/${this.currentEmployeeId}/`
                : '/api/employees/create/';

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                },
                body: JSON.stringify(data),
            });

            const result = await response.json();

            if (result.success) {
                this.modal.hide();
                location.reload(); // Простое обновление для демонстрации
            } else {
                alert('Ошибка при сохранении: ' + JSON.stringify(result.errors));
            }
        } catch (error) {
            alert('Ошибка при сохранении: ' + error.message);
        }
    }

    async prepareDelete(id) {
        try {
            const response = await fetch(`/api/employees/${id}/`);
            if (!response.ok) throw new Error('Ошибка загрузки данных');

            const employee = await response.json();
            document.getElementById('deleteEmployeeInfo').textContent =
                `${employee.full_name} (${employee.position})`;
            this.currentEmployeeId = id;
        } catch (error) {
            alert('Ошибка при загрузке данных: ' + error.message);
        }
    }

    async deleteEmployee() {
        try {
            const response = await fetch(`/api/employees/delete/${this.currentEmployeeId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                },
            });

            const result = await response.json();

            if (result.success) {
                this.deleteModal.hide();
                location.reload(); // Простое обновление для демонстрации
            } else {
                alert('Ошибка при удалении: ' + result.error);
            }
        } catch (error) {
            alert('Ошибка при удалении: ' + error.message);
        }
    }

    resetForm() {
        document.getElementById('employeeForm').reset();
        this.currentEmployeeId = null;
        document.getElementById('modalTitle').textContent = 'Добавить сотрудника';
    }

    getCSRFToken() {
        // Пытаемся получить токен из глобальной переменной
        if (window.CSRF_TOKEN) {
            return window.CSRF_TOKEN;
        }

        // Или из формы
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfInput ? csrfInput.value : '';
    }


}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    new EmployeeManager();
});
