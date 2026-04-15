import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.environ.get("DATABASE_URL", "tjsc_plan.db")
USE_PG = os.environ.get("DATABASE_URL") is not None

# Priority based on number of questions in exam (80 total for both cargos)
# Higher questions = higher priority to study first

ANALISTA_PRIORITY = {
    # Modulo Conhecimentos Gerais (30 questoes)
    "Portugues - Douglas Wisniewski": 10,
    "Portugues": 10,
    "Legislacao Institucional": 6,
    "Legislacao": 6,
    "Etica e Gestao no Servico Publico": 4,
    "Etica": 4,
    "Informatica e LGPD": 5,
    "Informatica": 5,
    "Direitos Humanos": 5,
    # Modulo Conhecimentos Especificos (50 questoes)
    "Administracao Geral": 12,
    "Admin Geral": 12,
    "Gestao de Pessoas": 8,
    "Adm de Materiais": 6,
    "Materiais": 6,
    "Administracao Publica": 10,
    "Adm Publica": 10,
    "AFO": 10,
    "Transparencia e Controle": 4,
    "Transparencia": 4,
    "LAI": 4,
}

TECNICO_PRIORITY = {
    # Modulo Conhecimentos Gerais (30 questoes)
    "Portugues - Janaina Souto": 10,
    "Portugues": 10,
    "Lingua Portuguesa": 10,
    "Legislacao Institucional": 6,
    "Legislacao": 6,
    "PJSC": 6,
    "Etica e Gestao no Servico Publico": 4,
    "Etica": 4,
    "Informatica": 5,
    "Informatica e Protecao de Dados": 5,
    "Direitos Humanos": 5,
    "Acesso a justica": 5,
    # Modulo Conhecimentos Especificos (50 questoes)
    "Direito Administrativo": 10,
    "Direito Constitucional": 8,
    "Constitutional": 8,
    "Direito Civil": 6,
    "Civil": 6,
    "Direito Processual Civil": 10,
    "Processual Civil": 10,
    "Direito Processual": 10,
    "Direito Penal": 6,
    "Penal": 6,
    "Direito Processual Penal": 10,
    "Processual Penal": 10,
    # Modulo Compartilhado (ambas as prioridades)
    "Transparencia": 4,
    "LAI": 4,
}


def get_module_priority(module_name, cargo_id):
    """Retorna a prioridade (numero de questoes) de um modulo baseado no cargo."""
    if cargo_id == 1:  # Analista
        priority_map = ANALISTA_PRIORITY
    else:  # Tecnico
        priority_map = TECNICO_PRIORITY

    # Normalize - remove accents for matching
    module_lower = module_name.lower()
    replacements = {
        "ã": "a",
        "á": "a",
        "à": "a",
        "â": "a",
        "é": "e",
        "ê": "e",
        "í": "i",
        "ó": "o",
        "ô": "o",
        "õ": "o",
        "ú": "u",
        "ç": "c",
        "ã": "a",
    }
    for old, new in replacements.items():
        module_lower = module_lower.replace(old, new)

    for key, priority in priority_map.items():
        key_normalized = key.lower()
        for old, new in replacements.items():
            key_normalized = key_normalized.replace(old, new)
        if key_normalized in module_lower:
            return priority
    return 0  # Default lowest priority


def generate_schedule_for_user(user_id, start_date_str="2026-04-14", cargo_id=1):
    """
    Gera o cronograma de estudio para um usuário.
    Prioritiza módulos basado no número de questões da prova.
    Suporta SQLite e PostgreSQL.
    """
    if USE_PG:
        import psycopg

        conn = psycopg.connect(DB_PATH)
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row

    cursor = conn.cursor()
    sql_placeholder = "%s" if USE_PG else "?"

    # Get effective cargo_id for user
    if cargo_id is None:
        cursor.execute(
            f"SELECT cargo_id FROM users WHERE id = {sql_placeholder}", (user_id,)
        )
        user_row = cursor.fetchone()
        cargo_id = user_row[0] if user_row else 1

    # Get modules for this cargo (or shared modules)
    cursor.execute(
        f"SELECT id, name FROM modules WHERE cargo_id = {sql_placeholder} OR cargo_id IS NULL ORDER BY id",
        (cargo_id,),
    )
    modules = cursor.fetchall()
    module_list = [(m[0], m[1]) for m in modules]

    # Calculate priority for each module
    module_priority = {}
    module_ids = []
    for m in module_list:
        mid, mname = m
        priority = get_module_priority(mname, cargo_id)
        module_priority[mid] = priority
        module_ids.append(mid)

    # Sort by priority (highest first)
    module_ids_sorted = sorted(
        module_ids, key=lambda mid: module_priority[mid], reverse=True
    )

    print(f"Prioridades para cargo {cargo_id}:")
    for mid in module_ids_sorted:
        m_name = next(m[1] for m in module_list if m[0] == mid)
        print(f"  {m_name}: {module_priority[mid]} questões")

    # Get remaining classes for each module
    module_queues = {}
    for mid in module_ids:
        cursor.execute(
            f"""
            SELECT c.id, c.duration_minutes
            FROM classes c
            LEFT JOIN user_progress up
                ON c.id = up.class_id AND up.user_id = {sql_placeholder}
            WHERE c.module_id = {sql_placeholder}
              AND (up.scheduled_date IS NULL OR up.is_completed = 0)
            ORDER BY c.id
        """,
            (user_id, mid),
        )
        rows = cursor.fetchall()
        module_queues[mid] = [{"id": r[0], "duration_minutes": r[1]} for r in rows]

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
                    date_str = current_date.strftime("%Y-%m-%d")
                    if USE_PG:
                        cursor.execute(
                            f"""
                            INSERT INTO user_progress (user_id, class_id, scheduled_date, is_completed)
                            VALUES ({sql_placeholder}, {sql_placeholder}, {sql_placeholder}, 0)
                            ON CONFLICT(user_id, class_id) DO UPDATE SET scheduled_date = {sql_placeholder}, is_completed = 0
                        """,
                            (user_id, cls["id"], date_str, date_str),
                        )
                    else:
                        cursor.execute(
                            f"""
                            INSERT INTO user_progress (user_id, class_id, scheduled_date, is_completed)
                            VALUES (?, ?, ?, 0)
                            ON CONFLICT(user_id, class_id) DO UPDATE SET scheduled_date = ?, is_completed = 0
                        """,
                            (user_id, cls["id"], date_str, date_str),
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
