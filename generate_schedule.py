import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.environ.get("DATABASE_URL", "tjsc_plan.db")
USE_PG = os.environ.get("DATABASE_URL") is not None

# Priority based on number of questions in exam (80 total for both cargos)
# Higher questions = higher priority to study first

ANALISTA_PRIORITY = {
    # Módulo Conhecimentos Gerais (30 questões)
    "Portugues - Douglas Wisniewski": 10,
    "Legislacao Institucional": 6,
    "Etica e Gestao no Servico Publico": 4,
    "Informatica e LGPD": 5,
    "Direitos Humanos": 5,
    # Módulo Conhecimentos Específicos (50 questões)
    "Administracao Geral": 12,
    "Gestao de Pessoas": 8,
    "Adm de Materiais": 6,
    "Administracao Publica": 10,
    "AFO": 10,
    "Transparencia e Controle": 4,
}

TECNICO_PRIORITY = {
    # Módulo Conhecimentos Gerais (30 questões)
    "Portugues - Janaina Souto": 10,
    "Legislacao Institucional": 6,
    "Etica e Gestao no Servico Publico": 4,
    "Informatica - Leo Matos": 5,
    "Direitos Humanos": 5,
    # Módulo Conhecimentos Específicos (50 questões)
    "Direito Administrativo": 10,
    "Direito Constitucional": 8,
    "Direito Civil": 6,
    "Direito Processual Civil": 10,
    "Direito Penal": 6,
    "Direito Processual Penal": 10,
}


def get_module_priority(module_name, cargo_id):
    """Retorna a prioridade (número de questões) de um módulo baseado no cargo."""
    if cargo_id == 1:  # Analista
        priority_map = ANALISTA_PRIORITY
    else:  # Tecnico
        priority_map = TECNICO_PRIORITY

    for key, priority in priority_map.items():
        if key.lower() in module_name.lower():
            return priority
    return 0  # Default lowest priority


def generate_schedule_for_user(user_id, start_date_str="2026-04-14", cargo_id=1):
    """
    Gera o cronograma de estudo para um usuário.
    Prioritiza módulos baseado no número de questões da prova.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get effective cargo_id for user
    if cargo_id is None:
        user_row = cursor.execute(
            "SELECT cargo_id FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        cargo_id = user_row["cargo_id"] if user_row else 1

    # Get modules for this cargo (or shared modules)
    modules = cursor.execute(
        """
        SELECT id, name FROM modules 
        WHERE cargo_id = ? OR cargo_id IS NULL
        ORDER BY id
    """,
        (cargo_id,),
    ).fetchall()

    # Calculate priority for each module
    module_priority = {}
    module_ids = []
    for m in modules:
        priority = get_module_priority(m["name"], cargo_id)
        module_priority[m["id"]] = priority
        module_ids.append(m["id"])

    # Sort by priority (highest first)
    module_ids_sorted = sorted(
        module_ids, key=lambda mid: module_priority[mid], reverse=True
    )

    print(f"Prioridades para cargo {cargo_id}:")
    for mid in module_ids_sorted:
        m_name = next(m["name"] for m in modules if m["id"] == mid)
        print(f"  {m_name}: {module_priority[mid]} questões")

    # Get remaining classes for each module
    module_queues = {}
    for mid in module_ids:
        rows = cursor.execute(
            """
            SELECT c.id, c.duration_minutes
            FROM classes c
            LEFT JOIN user_progress up
                ON c.id = up.class_id AND up.user_id = ?
            WHERE c.module_id = ?
              AND (up.scheduled_date IS NULL OR up.is_completed = 0)
            ORDER BY c.id
        """,
            (user_id, mid),
        ).fetchall()
        module_queues[mid] = [dict(r) for r in rows]

    current_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    active_module_idx = 0
    study_days = 0

    while any(module_queues.values()):
        weekday = current_date.weekday()

        if weekday == 6:  # Sunday = rest
            current_date += timedelta(days=1)
            continue

        # Daily budget: Mon-Fri = 6h, Sat = 4h
        daily_budget = 360 if weekday < 5 else 240
        used_minutes = 0

        # Try to fill the day
        while used_minutes < daily_budget and any(module_queues.values()):
            attempts = 0
            while attempts < len(module_ids_sorted):
                mid = module_ids_sorted[active_module_idx]
                if module_queues[mid]:
                    cls = module_queues[mid].pop(0)
                    cursor.execute(
                        """
                        INSERT INTO user_progress (user_id, class_id, scheduled_date, is_completed)
                        VALUES (?, ?, ?, 0)
                        ON CONFLICT(user_id, class_id)
                        DO UPDATE SET scheduled_date = ?, is_completed = 0
                    """,
                        (
                            user_id,
                            cls["id"],
                            current_date.strftime("%Y-%m-%d"),
                            current_date.strftime("%Y-%m-%d"),
                        ),
                    )
                    used_minutes += cls["duration_minutes"]
                    active_module_idx = (active_module_idx + 1) % len(module_ids_sorted)
                    break
                else:
                    active_module_idx = (active_module_idx + 1) % len(module_ids_sorted)
                    attempts += 1

            if attempts == len(module_ids_sorted):
                break

        if used_minutes > 0:
            study_days += 1
        current_date += timedelta(days=1)

    conn.commit()
    conn.close()
    print(f"Cronograma gerado para user_id={user_id} ({study_days} dias de estudo)!")
    return study_days


def generate_schedule(start_date_str="2026-04-14"):
    """Gera para TODOS os usuários."""
    conn = sqlite3.connect(DB_PATH)
    users = conn.execute("SELECT id, cargo_id FROM users").fetchall()
    conn.close()
    for u in users:
        generate_schedule_for_user(u["id"], start_date_str, u["cargo_id"])


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        uid = int(sys.argv[1])
        date = sys.argv[2] if len(sys.argv) > 2 else "2026-04-14"
        cargo = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        generate_schedule_for_user(uid, date, cargo)
    else:
        print("Uso: python generate_schedule.py <user_id> [data_inicio] [cargo_id]")
        print("Exemplo: python generate_schedule.py 1 2026-04-14 1")
        print("Cargo: 1=Analista, 2=Tecnico")
