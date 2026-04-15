document.addEventListener('DOMContentLoaded', () => {
    // ==== Countdown Timer to June 28, 2026 ====
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

    setInterval(updateTimer, 60000); // update every minute
    updateTimer(); // initial call

    // ==== Progress and Daily Goal logic ====
    
    // Checkboxes interaction
    const checkboxes = document.querySelectorAll('.class-status-checkbox');
    
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', async (e) => {
            const classId = e.target.dataset.id;
            const isCompleted = e.target.checked;
            
            // Visual toggle (strikethrough)
            const textSpan = e.target.nextElementSibling.nextElementSibling;
            if(isCompleted) {
                textSpan.classList.add('checked-text');
            } else {
                textSpan.classList.remove('checked-text');
            }

            // Show saving indicator
            textSpan.classList.add('saving');

            // Sync with backend
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
                }
            } catch (error) {
                console.error("Error updating progress:", error);
                textSpan.classList.remove('saving');
                // Revert checkbox on error
                e.target.checked = !isCompleted;
            }
        });
    });

    function updateDashboard(total, completed) {
        // Calculate Percentage
        const percentage = total > 0 ? ((completed / total) * 100).toFixed(1) : 0;
        document.getElementById('overall-progress-text').innerText = `${percentage}%`;
        document.getElementById('overall-progress-bar').style.width = `${percentage}%`;
        
        // Calculate daily goal
        const now = new Date();
        const daysLeft = Math.ceil((examDate - now) / (1000 * 60 * 60 * 24));
        const minutesRemaining = total - completed;
        
        if (daysLeft > 0 && minutesRemaining > 0) {
            const minsPerDay = Math.ceil(minutesRemaining / daysLeft);
            const hrs = Math.floor(minsPerDay / 60);
            const rMins = minsPerDay % 60;
            
            let timeStr = "";
            if (hrs > 0) timeStr += `${hrs}h`;
            if (rMins > 0) timeStr += `${rMins}m`;
            
            document.getElementById('daily-goal').innerText = timeStr || "0m";
            document.getElementById('daily-goal-desc').innerText = "Por dia para fechar o edital";
        } else if (minutesRemaining <= 0) {
            document.getElementById('daily-goal').innerText = "Meta Atingida!";
            document.getElementById('daily-goal').classList.remove('primary-text');
            document.getElementById('daily-goal').classList.add('accent-text');
            document.getElementById('daily-goal-desc').innerText = "Revisar conteúdo!";
        } else {
            document.getElementById('daily-goal').innerText = "Prova Hoje!";
        }
    }

});
