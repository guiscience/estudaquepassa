import sqlite3
from datetime import datetime, timedelta

DB_PATH = 'tjsc_plan.db'


def generate_schedule_for_user(user_id, start_date_str='2026-04-14'):
    """
    Gera o cronograma de estudo para um único usuário.
    Escreve em user_progress (scheduled_date), não na tabela classes.
    Apenas aulas sem scheduled_date ainda são agendadas (incremental).
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    modules    = cursor.execute('SELECT id FROM modules').fetchall()
    module_ids = [m['id'] for m in modules]

    # Apenas aulas sem data agendada para este usuário
    module_queues = {}
    for mid in module_ids:
        rows = cursor.execute('''
            SELECT c.id, c.duration_minutes
            FROM classes c
            LEFT JOIN user_progress up
                ON c.id = up.class_id AND up.user_id = ?
            WHERE c.module_id = ?
              AND (up.scheduled_date IS NULL)
            ORDER BY c.id
        ''', (user_id, mid)).fetchall()
        module_queues[mid] = [dict(r) for r in rows]

    current_date     = datetime.strptime(start_date_str, '%Y-%m-%d')
    active_module_idx = 0

    while any(module_queues.values()):
        weekday = current_date.weekday()  # 0=Seg … 6=Dom

        if weekday == 6:  # Domingo = descanso
            current_date += timedelta(days=1)
            continue

        daily_budget = 360 if weekday < 5 else 240  # Seg-Sex: 6h / Sáb: 4h
        used_minutes = 0

        while used_minutes < daily_budget and any(module_queues.values()):
            attempts = 0
            while attempts < len(module_ids):
                mid = module_ids[active_module_idx]
                if module_queues[mid]:
                    cls = module_queues[mid].pop(0)
                    cursor.execute('''
                        INSERT INTO user_progress (user_id, class_id, scheduled_date, is_completed)
                        VALUES (?, ?, ?, 0)
                        ON CONFLICT(user_id, class_id)
                        DO UPDATE SET scheduled_date = ?
                    ''', (user_id, cls['id'],
                          current_date.strftime('%Y-%m-%d'),
                          current_date.strftime('%Y-%m-%d')))
                    used_minutes += cls['duration_minutes']
                    active_module_idx = (active_module_idx + 1) % len(module_ids)
                    break
                else:
                    active_module_idx = (active_module_idx + 1) % len(module_ids)
                    attempts += 1

            if attempts == len(module_ids):
                break  # Sem mais aulas

        current_date += timedelta(days=1)

    conn.commit()
    conn.close()
    print(f"Cronograma gerado para user_id={user_id} com sucesso!")


def generate_schedule(start_date_str='2026-04-14'):
    """Mantido para compatibilidade: gera para TODOS os usuários cadastrados."""
    conn = sqlite3.connect(DB_PATH)
    users = conn.execute('SELECT id FROM users').fetchall()
    conn.close()
    for u in users:
        generate_schedule_for_user(u['id'], start_date_str)


# ── Execução direta ────────────────────────────────────────────────────────
def setup_schedule_column():
    """Não é mais necessário — scheduled_date vive em user_progress."""
    pass


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        uid = int(sys.argv[1])
        date = sys.argv[2] if len(sys.argv) > 2 else '2026-04-14'
        generate_schedule_for_user(uid, date)
    else:
        print("Uso: python generate_schedule.py <user_id> [data_inicio]")
        print("Exemplo: python generate_schedule.py 1 2026-04-14")
        print("Ou use a rota /api/generate_schedule no app web após fazer login.")
