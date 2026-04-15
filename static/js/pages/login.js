document.addEventListener('DOMContentLoaded', () => {
    const authForm = document.getElementById('auth-form');
    const registerForm = document.getElementById('register-form');
    const btnToggle = document.getElementById('btn-toggle-register');

    if (!authForm || !registerForm || !btnToggle) {
        return;
    }

    btnToggle.addEventListener('click', () => {
        authForm.style.display = 'none';
        registerForm.style.display = 'block';
        const usernameInput = document.getElementById('reg-username');
        if (usernameInput) {
            usernameInput.focus();
        }
    });
});
