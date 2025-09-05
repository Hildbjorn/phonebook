document.addEventListener('DOMContentLoaded', function () {
    const importForm = document.getElementById('importForm');
    const importBtn = document.getElementById('importBtn');
    const importResult = document.getElementById('importResult');

    if (importForm) {
        importForm.addEventListener('submit', function (e) {
            e.preventDefault();

            const formData = new FormData(this);
            const fileInput = document.getElementById('excel_file');

            if (!fileInput.files[0]) {
                alert('Пожалуйста, выберите файл');
                return;
            }

            importBtn.disabled = true;
            importBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Загрузка...';

            fetch('/import/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            })
                .then(response => response.json())
                .then(data => {
                    importResult.style.display = 'block';

                    // Скрываем все алерты
                    document.getElementById('successAlert').style.display = 'none';
                    document.getElementById('partialAlert').style.display = 'none';
                    document.getElementById('errorAlert').style.display = 'none';
                    document.getElementById('errorDetails').style.display = 'none';

                    if (data.status === 'success') {
                        document.getElementById('successAlert').style.display = 'block';
                        document.getElementById('successMessage').textContent =
                            `Успешно обработано: ${data.total} записей. Добавлено: ${data.added}, Обновлено: ${data.updated}`;
                    }
                    else if (data.status === 'partial') {
                        document.getElementById('partialAlert').style.display = 'block';
                        document.getElementById('partialMessage').textContent =
                            `Обработано: ${data.total} записей. Добавлено: ${data.added}, Обновлено: ${data.updated}. Ошибок: ${data.errors.length}`;

                        if (data.errors.length > 0) {
                            document.getElementById('errorDetails').style.display = 'block';
                            document.getElementById('errorDetailsContent').textContent = data.errors.join('\n');
                        }
                    }
                    else {
                        document.getElementById('errorAlert').style.display = 'block';
                        document.getElementById('errorMessage').textContent = data.error || 'Произошла неизвестная ошибка';
                    }
                })
                .catch(error => {
                    importResult.style.display = 'block';
                    document.getElementById('errorAlert').style.display = 'block';
                    document.getElementById('errorMessage').textContent = 'Ошибка сети: ' + error.message;
                })
                .finally(() => {
                    importBtn.disabled = false;
                    importBtn.innerHTML = '<i class="bi bi-upload"></i> Загрузить файл';
                });
        });
    }
});