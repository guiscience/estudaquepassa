document.addEventListener('DOMContentLoaded', () => {
    const examDate = new Date('2026-06-28T00:00:00');
    
    function updateTimer() {
        const now = new Date();
        const diff = examDate - now;

        if (diff <= 0) {
            document.getElementById('days').innerText = '00';
            document.getElementById('hours').innerText = '00';
            document.getElementById('minutes').innerText = '00';
            return;
        }

        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        const hours = Math.floor((diff / (1000 * 60 * 60)) % 24);
        const minutes = Math.floor((diff / 1000 / 60) % 60);

        document.getElementById('days').innerText = days.toString().padStart(2, '0');
        document.getElementById('hours').innerText = hours.toString().padStart(2, '0');
        document.getElementById('minutes').innerText = minutes.toString().padStart(2, '0');
    }

    setInterval(updateTimer, 60000);
    updateTimer();

    const checkboxes = document.querySelectorAll('.class-status-checkbox');
    
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', async (e) => {
            const classId = e.target.dataset.id;
            const isCompleted = e.target.checked;
            
            const textSpan = e.target.nextElementSibling.nextElementSibling;
            if(isCompleted) {
                textSpan.classList.add('checked-text');
            } else {
                textSpan.classList.remove('checked-text');
            }

            textSpan.classList.add('saving');

            try {
                const response = await fetch('/api/toggle_class', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ class_id: classId, is_completed: isCompleted })
                });
                
                const data = await response.json();
                if(data.success) {
                    updateDashboard(data.total_minutes, data.completed_minutes);
                    textSpan.classList.remove('saving');
                    textSpan.classList.add('saved');
                    setTimeout(() => textSpan.classList.remove('saved'), 1500);
                    
                    // Notify other tabs/pages to update
                    localStorage.setItem('class_status_changed', Date.now().toString());
                }
            } catch (error) {
                console.error("Error updating progress:", error);
                textSpan.classList.remove('saving');
                e.target.checked = !isCompleted;
            }
        });
    });

    function updateDashboard(total, completed) {
        const percentage = total > 0 ? ((completed / total) * 100).toFixed(1) : 0;
        
        const progressText = document.getElementById('overall-progress-text');
        const progressBar = document.getElementById('overall-progress-bar');
        
        if (progressText) progressText.innerText = `${percentage}%`;
        if (progressBar) progressBar.style.width = `${percentage}%`;
        
        const now = new Date();
        const daysLeft = Math.ceil((examDate - now) / (1000 * 60 * 60 * 24));
        const minutesRemaining = total - completed;
        
        const dailyGoal = document.getElementById('daily-goal');
        const dailyGoalDesc = document.getElementById('daily-goal-desc');
        
        if (!dailyGoal) return;
        
        if (daysLeft > 0 && minutesRemaining > 0) {
            const minsPerDay = Math.ceil(minutesRemaining / daysLeft);
            const hrs = Math.floor(minsPerDay / 60);
            const rMins = minsPerDay % 60;
            
            let timeStr = "";
            if (hrs > 0) timeStr += `${hrs}h`;
            if (rMins > 0) timeStr += `${rMins}m`;
            
            dailyGoal.innerText = timeStr || "0m";
            if (dailyGoalDesc) dailyGoalDesc.innerText = "Por dia para fechar o edital";
        } else if (minutesRemaining <= 0 && total > 0) {
            dailyGoal.innerText = "Meta Atingida!";
            dailyGoal.classList.remove('primary-text');
            dailyGoal.classList.add('accent-text');
            if (dailyGoalDesc) dailyGoalDesc.innerText = "Revisar conteúdo!";
        } else if (total === 0) {
            dailyGoal.innerText = "N/A";
            if (dailyGoalDesc) dailyGoalDesc.innerText = "Nenhuma aula inserida";
        } else {
            dailyGoal.innerText = "Prova Hoje!";
        }
    }

    // Listen for changes from other tabs
    window.addEventListener('storage', (e) => {
        if (e.key === 'class_status_changed') {
            location.reload();
        }
    });
});
