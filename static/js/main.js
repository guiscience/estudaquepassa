document.addEventListener('DOMContentLoaded', () => {
    const examDate = new Date('2026-06-28T00:00:00');
    
    function updateTimer() {
        const now = new Date();
        const diff = examDate - now;

        if (diff <= 0) {
            const daysEl = document.getElementById('days');
            if (daysEl) daysEl.innerText = '0';
            return;
        }

        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        const daysEl = document.getElementById('days');
        if (daysEl) daysEl.innerText = days;
    }

    setInterval(updateTimer, 60000);
    updateTimer();

    const checkboxes = document.querySelectorAll('.class-status-checkbox');
    
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', async (e) => {
            const classId = e.target.dataset.id;
            const isCompleted = e.target.checked;
            
            // Find the title span - works with both old and new HTML structures
            let titleSpan = null;
            const parent = e.target.parentElement;
            if (parent) {
                titleSpan = parent.querySelector('.qc-class-title') || parent.querySelector('.class-title');
            }
            
            // Show saving state
            if (titleSpan) {
                titleSpan.classList.add('saving');
            }

            console.log('Toggle class:', classId, isCompleted);

            try {
                const response = await fetch('/api/toggle_class', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        class_id: parseInt(classId), 
                        is_completed: isCompleted 
                    })
                });
                
                console.log('Response status:', response.status);
                
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                
                const data = await response.json();
                console.log('Response data:', data);
                
                if(data.success) {
                    // Update visual state
                    if (titleSpan) {
                        titleSpan.classList.remove('saving');
                        if (isCompleted) {
                            titleSpan.classList.add('qc-completed');
                        } else {
                            titleSpan.classList.remove('qc-completed');
                        }
                    }
                    
                    // Update dashboard
                    updateDashboard(data.total_minutes, data.completed_minutes);
                    
                    // Sync with other tabs
                    localStorage.setItem('class_status_changed', Date.now().toString());
                } else {
                    console.error('Server returned error:', data.error);
                    // Revert checkbox
                    e.target.checked = !isCompleted;
                }
            } catch (error) {
                console.error('Error updating progress:', error);
                if (titleSpan) {
                    titleSpan.classList.remove('saving');
                }
                // Revert checkbox on error
                e.target.checked = !isCompleted;
                alert('Erro ao salvar progresso. Tente novamente.');
            }
        });
    });

    function updateDashboard(total, completed) {
        const percentage = total > 0 ? ((completed / total) * 100).toFixed(1) : 0;
        
        // Update progress text
        const progressText = document.getElementById('overall-progress-text');
        const qcProgressPercent = document.getElementById('qc-progress-percent');
        
        if (progressText) progressText.innerText = `${percentage}%`;
        if (qcProgressPercent) qcProgressPercent.innerText = `${percentage}%`;
        
        // Update progress bar
        const progressBar = document.getElementById('overall-progress-bar');
        if (progressBar) progressBar.style.width = `${percentage}%`;
        
        // Update daily goal
        const now = new Date();
        const daysLeft = Math.ceil((examDate - now) / (1000 * 60 * 60 * 24));
        const minutesRemaining = total - completed;
        
        const dailyGoal = document.getElementById('daily-goal');
        
        if (!dailyGoal) return;
        
        if (daysLeft > 0 && minutesRemaining > 0) {
            const minsPerDay = Math.ceil(minutesRemaining / daysLeft);
            const hrs = Math.floor(minsPerDay / 60);
            const rMins = minsPerDay % 60;
            
            dailyGoal.innerText = (hrs > 0 ? hrs + 'h ' : '') + rMins + 'm';
        } else if (minutesRemaining <= 0 && total > 0) {
            dailyGoal.innerText = 'Concluído!';
        } else if (total === 0) {
            dailyGoal.innerText = 'N/A';
        } else {
            dailyGoal.innerText = 'Prova Hoje!';
        }
    }

    // Listen for changes from other tabs
    window.addEventListener('storage', (e) => {
        if (e.key === 'class_status_changed') {
            location.reload();
        }
    });
});
