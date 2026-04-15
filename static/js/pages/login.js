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

    const concursoSelect = document.getElementById('concurso_id');
    const bancaSelect = document.getElementById('banca_id');
    const disciplinaSelect = document.getElementById('disciplina_id');

    if (concursoSelect && bancaSelect) {
        concursoSelect.addEventListener('change', async () => {
            const concursoId = concursoSelect.value;
            
            const formData = new FormData();
            formData.append('concurso_id', concursoId);

            try {
                const response = await fetch('/api/get_bancas', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                
                bancaSelect.innerHTML = '<option value="">Todas</option>';
                data.bancas.forEach(b => {
                    const option = document.createElement('option');
                    option.value = b.id;
                    option.textContent = b.nome;
                    bancaSelect.appendChild(option);
                });

                if (disciplinaSelect) {
                    disciplinaSelect.innerHTML = '<option value="">Todas</option>';
                }
            } catch (e) {
                console.error('Erro ao carregar bancas:', e);
            }
        });
    }

    if (bancaSelect && disciplinaSelect) {
        bancaSelect.addEventListener('change', async () => {
            const bancaId = bancaSelect.value;
            
            if (!bancaId) {
                disciplinaSelect.innerHTML = '<option value="">Todas</option>';
                return;
            }

            const formData = new FormData();
            formData.append('banca_id', bancaId);

            try {
                const response = await fetch('/api/get_disciplinas', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                
                disciplinaSelect.innerHTML = '<option value="">Todas</option>';
                data.disciplinas.forEach(d => {
                    const option = document.createElement('option');
                    option.value = d.id;
                    option.textContent = d.name;
                    disciplinaSelect.appendChild(option);
                });
            } catch (e) {
                console.error('Erro ao carregar disciplinas:', e);
            }
        });
    }
});
