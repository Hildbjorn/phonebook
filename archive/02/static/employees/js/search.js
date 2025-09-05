class SearchManager {
    constructor() {
        this.searchInput = document.getElementById('search-input');
        this.searchResults = document.getElementById('search-results');
        this.debounceTimer = null;
        this.initEventListeners();
    }

    initEventListeners() {
        this.searchInput.addEventListener('input', (e) => {
            this.debounceSearch(e.target.value);
        });

        this.searchInput.addEventListener('focus', () => {
            if (this.searchInput.value.length > 2 && this.searchResults.children.length > 0) {
                this.searchResults.style.display = 'block';
            }
        });

        document.addEventListener('click', (e) => {
            if (!this.searchResults.contains(e.target) && e.target !== this.searchInput) {
                this.searchResults.style.display = 'none';
            }
        });
    }

    debounceSearch(query) {
        clearTimeout(this.debounceTimer);

        if (query.length < 2) {
            this.searchResults.style.display = 'none';
            this.searchResults.innerHTML = '';
            return;
        }

        this.debounceTimer = setTimeout(() => {
            this.performSearch(query);
        }, 300);
    }

    async performSearch(query) {
        try {
            this.showLoading();

            const response = await fetch(`/api/employees/?query=${encodeURIComponent(query)}`);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            this.displayResults(data.results || []);

        } catch (error) {
            console.error('Search error:', error);
            this.displayError(error.message);
        }
    }

    showLoading() {
        this.searchResults.innerHTML = '<div class="search-result-item"><div class="spinner-border spinner-border-sm" role="status"></div> Поиск...</div>';
        this.searchResults.style.display = 'block';
    }

    displayResults(results) {
        this.searchResults.innerHTML = '';

        if (results.length === 0) {
            this.searchResults.innerHTML = '<div class="search-result-item">Ничего не найдено</div>';
        } else {
            results.forEach(employee => {
                const item = document.createElement('div');
                item.className = 'search-result-item';

                // Добавляем отображение кабинета, если он есть
                const roomInfo = employee.room ? ` • Каб. ${employee.room}` : '';

                item.innerHTML = `
                    <strong>${this.escapeHtml(employee.full_name)}</strong><br>
                    <small>${this.escapeHtml(employee.position)} • ${this.escapeHtml(employee.phone)}${roomInfo}</small>
                `;
                item.addEventListener('click', () => {
                    window.location.href = `?query=${encodeURIComponent(employee.full_name)}`;
                    this.searchResults.style.display = 'none';
                });
                this.searchResults.appendChild(item);
            });
        }

        this.searchResults.style.display = 'block';
    }

    displayError(message) {
        this.searchResults.innerHTML = `
            <div class="search-result-item text-danger">
                <i class="bi bi-exclamation-triangle"></i> Ошибка поиска: ${this.escapeHtml(message)}
            </div>
        `;
        this.searchResults.style.display = 'block';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Инициализация поиска
document.addEventListener('DOMContentLoaded', () => {
    new SearchManager();
});
