// CSRF токен для работы HTMX
document.addEventListener('htmx:configRequest', function (event) {
    const csrfToken = document.querySelector('meta[name="csrfmiddlewaretoken"]')?.content;
    if (csrfToken) {
        event.detail.headers['X-CSRFToken'] = csrfToken;
    } else {
        console.error("CSRF Token not found in meta tag.");
    }
});

// Инициализация Bootstrap компонентов
function initializeBootstrapComponents() {
    // Popovers
    const popoverList = [...document.querySelectorAll('[data-bs-toggle="popover"]')].map(
        el => new bootstrap.Popover(el)
    );

    // Tooltips
    const tooltipList = [...document.querySelectorAll('[data-bs-toggle="tooltip"]')].map(
        el => new bootstrap.Tooltip(el)
    );
}

// Прозрачность меню при прокрутке
function setupNavbarTransparency() {
    const navbar = document.querySelector('nav.navbar');
    if (!navbar) return;

    document.addEventListener('scroll', function () {
        navbar.classList.toggle('transparent', window.scrollY > 60);
    });
}

// Маска телефона
function initializePhoneMask() {
    const inputs = document.querySelectorAll('.tel');
    if (inputs.length === 0) return;

    inputs.forEach(input => {
        let keyCode;

        function mask(event) {
            event.keyCode && (keyCode = event.keyCode);
            let pos = this.selectionStart;
            if (pos < 3) event.preventDefault();

            let matrix = "+7 (___) ___ ____",
                i = 0,
                def = matrix.replace(/\D/g, ""),
                val = this.value.replace(/\D/g, ""),
                new_value = matrix.replace(/[_\d]/g, function (a) {
                    return i < val.length ? val.charAt(i++) || def.charAt(i) : a;
                });

            i = new_value.indexOf("_");
            if (i !== -1) {
                i < 5 && (i = 3);
                new_value = new_value.slice(0, i);
            }

            let reg = matrix.substr(0, this.value.length).replace(/_+/g,
                function (a) {
                    return "\\d{1," + a.length + "}";
                }).replace(/[+()]/g, "\\$&");

            reg = new RegExp("^" + reg + "$");
            if (!reg.test(this.value) || this.value.length < 5 || keyCode > 47 && keyCode < 58) {
                this.value = new_value;
            }
            if (event.type === "blur" && this.value.length < 5) this.value = "";
        }

        input.addEventListener("input", mask);
        input.addEventListener("focus", mask);
        input.addEventListener("blur", mask);
        input.addEventListener("keydown", mask);
    });
}

// Кнопка "Наверх"
function initScrollToTop() {
    const scrollToTopButton = document.getElementById('scrollToTop');
    if (!scrollToTopButton) return;

    window.addEventListener('scroll', function () {
        scrollToTopButton.style.display = window.pageYOffset > 300 ? 'block' : 'none';
    });

    scrollToTopButton.addEventListener('click', function (e) {
        e.preventDefault();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}

// Главная функция инициализации
function initializeAll() {
    initializeBootstrapComponents();
    setupNavbarTransparency();
    initializePhoneMask();
    initScrollToTop();
}

// Обработчики событий
document.addEventListener('DOMContentLoaded', initializeAll);
document.addEventListener('htmx:afterSwap', function () {
    initializePhoneMask();
});