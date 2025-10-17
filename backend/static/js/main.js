document.addEventListener("DOMContentLoaded", function () {
    // NAV MOBILE
    const navMobile = document.getElementById("navMobile");
    const toggleBtn = document.getElementById("mobileToggle");
    const overlay = document.getElementById("mobileOverlay");
    const toggleIcon = document.getElementById("toggleIcon");
    const body = document.body;
    const userMenuToggle = document.getElementById('userMenuToggle');
    const userDropdown = document.getElementById('userDropdown');

    function toggleMobileMenu() {
        if (!navMobile) return;
        const isOpen = navMobile.classList.contains("show");
        if (isOpen) {
            navMobile.classList.remove("show");
            if (overlay) overlay.classList.remove("show");
            body.classList.remove("menu-open");
            if (toggleIcon) toggleIcon.textContent = "☰";
        } else {
            navMobile.classList.add("show");
            if (overlay) overlay.classList.add("show");
            body.classList.add("menu-open");
            if (toggleIcon) toggleIcon.textContent = "✕";
        }
    }

    if (toggleBtn) toggleBtn.addEventListener("click", toggleMobileMenu);
    if (overlay) overlay.addEventListener("click", toggleMobileMenu);

    if (userMenuToggle && userDropdown) {
        userMenuToggle.onclick = function(e) {
            e.stopPropagation();
            userDropdown.classList.toggle('show');
            userMenuToggle.classList.toggle('active');
        };
        document.addEventListener('click', function(event) {
            if (!userMenuToggle.contains(event.target) && !userDropdown.contains(event.target)) {
                userDropdown.classList.remove('show');
                userMenuToggle.classList.remove('active');
            }
        });
    }

    // CÓDIGO DE VERIFICACIÓN
    const codigoInput = document.getElementById('codigo');
    const confirmForm = document.getElementById('confirmForm');
    const timerElement = document.getElementById('timer');
    const countdownElement = document.getElementById('countdown');
    const resendLink = document.getElementById('resendLink');

    if (codigoInput && confirmForm) {
        codigoInput.focus();

        codigoInput.addEventListener('input', function() {
            this.value = this.value.replace(/[^0-9]/g, '');
            if (this.value.length === 6) setTimeout(() => confirmForm.submit(), 500);
        });

        let timeLeft = 80;
        let timerInterval;

        const updateTimer = () => {
            const minutes = Math.floor(timeLeft / 60);
            const seconds = timeLeft % 60;
            if (timerElement) timerElement.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;

            if (timeLeft <= 0) {
                if (countdownElement) countdownElement.style.display = 'none';
                if (resendLink) {
                    resendLink.classList.remove('disabled');
                    resendLink.textContent = 'Reenviar código';
                }
                clearInterval(timerInterval);
            } else {
                timeLeft--;
            }
        };

        timerInterval = setInterval(updateTimer, 1000);
        updateTimer();

        if (resendLink) {
            resendLink.addEventListener('click', function(e) {
                e.preventDefault();
                if (this.classList.contains('disabled')) return;

                this.classList.add('disabled');
                this.textContent = 'Enviando...';

                fetch(window.location.href + '?resend=true', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({ action: 'resend_code' })
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        timeLeft = 80;
                        if (countdownElement) countdownElement.style.display = 'block';
                        this.textContent = 'Código reenviado';
                        clearInterval(timerInterval);
                        timerInterval = setInterval(updateTimer, 1000);
                        showMessage('Código reenviado exitosamente. Revisa tu correo e inbox de spam.', 'success');
                    } else {
                        this.classList.remove('disabled');
                        this.textContent = 'Reenviar código';
                        showMessage(data.message || 'Error al reenviar el código. Inténtalo de nuevo.', 'error');
                    }
                })
                .catch(() => {
                    this.classList.remove('disabled');
                    this.textContent = 'Reenviar código';
                    showMessage('Error de conexión. Por favor intenta de nuevo.', 'error');
                });
            });
        }

        function showMessage(msg, type) {
            let container = document.querySelector('.message-container');
            if (!container) {
                container = document.createElement('div');
                container.className = 'message-container';
                document.querySelector('.info-section')?.after(container);
            }
            container.innerHTML = '';
            const div = document.createElement('div');
            div.className = `alert alert-${type}`;
            div.textContent = msg;
            container.appendChild(div);
            setTimeout(() => div.remove(), 5000);
        }

        confirmForm.addEventListener('submit', function(e) {
            const codigo = codigoInput.value.trim();
            if (codigo.length !== 6 || !/^\d{6}$/.test(codigo)) {
                e.preventDefault();
                alert('El código debe contener 6 dígitos numéricos');
                codigoInput.focus();
            }
        });
    }
});
