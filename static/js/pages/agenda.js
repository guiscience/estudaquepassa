async function generateSchedule() {
    const btn = document.querySelector('button[onclick="generateSchedule()"]');
    if (!btn) {
        return;
    }

    btn.textContent = 'Gerando...';
    btn.disabled = true;

    try {
        const resp = await fetch('/api/generate_schedule', { method: 'POST' });
        const data = await resp.json();
        if (data.success) {
            location.reload();
        } else {
            alert('Erro: ' + data.message);
            btn.textContent = 'Gerar Cronograma';
            btn.disabled = false;
        }
    } catch (e) {
        alert('Erro ao gerar cronograma');
        btn.textContent = 'Gerar Cronograma';
        btn.disabled = false;
    }
}
