import sqlite3
import os

DB_PATH = 'tjsc_plan.db'

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Erro: {DB_PATH} não encontrado. Execute database.py primeiro.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ── Tabela de usuários ─────────────────────────────────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    print("Tabela 'users' OK.")

    # ── Tabela de progresso por usuário ────────────────────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_progress (
            user_id  INTEGER NOT NULL,
            class_id INTEGER NOT NULL,
            is_completed   INTEGER DEFAULT 0,
            scheduled_date TEXT,
            PRIMARY KEY (user_id, class_id),
            FOREIGN KEY (user_id)  REFERENCES users(id),
            FOREIGN KEY (class_id) REFERENCES classes(id)
        )
    ''')
    print("Tabela 'user_progress' OK.")

    # ── Tabela de cargos ───────────────────────────────────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cargos (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    ''')
    cursor.execute("INSERT OR IGNORE INTO cargos (id, name) VALUES (1, 'Analista Judiciário - Área Judiciária')")
    cursor.execute("INSERT OR IGNORE INTO cargos (id, name) VALUES (2, 'Técnico Judiciário - Área Judiciária')")
    print("Tabela 'cargos' OK (Analista=1, Técnico=2).")

    # ── cargo_id em modules ────────────────────────────────────────────────
    try:
        cursor.execute('ALTER TABLE modules ADD COLUMN cargo_id INTEGER DEFAULT 1')
        print("Coluna 'cargo_id' adicionada a 'modules'.")
    except sqlite3.OperationalError:
        print("Coluna 'cargo_id' em 'modules' já existe.")

    # Módulos compartilhados (cargo_id = NULL → aparecem para TODOS os cargos):
    # Português (7), Informática (8), Transparência/LAI (13), Ética (14)
    cursor.execute("UPDATE modules SET cargo_id = NULL WHERE id IN (7, 8, 13, 14)")
    print("Modulos compartilhados: Portugues, Informatica, Transparencia, Etica -> cargo_id = NULL")

    # Módulos exclusivos do Analista (cargo_id = 1):
    # AFO (6), Adm Geral (9), Gestão de Pessoas (10), Adm Materiais (11), Adm Pública (12)
    cursor.execute("UPDATE modules SET cargo_id = 1 WHERE id IN (6, 9, 10, 11, 12)")
    print("Módulos exclusivos do Analista: AFO, Adm Geral, Gestão de Pessoas, Adm Materiais, Adm Pública")

    # ── cargo_id em users ──────────────────────────────────────────────────
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN cargo_id INTEGER DEFAULT 1')
        print("Coluna 'cargo_id' adicionada a 'users' (default=1 Analista).")
    except sqlite3.OperationalError:
        print("Coluna 'cargo_id' em 'users' já existe.")

    conn.commit()
    conn.close()
    print("\nMigracao concluida com sucesso!")
    print("  - Tecnico Judiciario vera: Portugues, Informatica, Transparencia, Etica")
    print("  - Analista vera tudo (incluindo AFO, Adm Geral etc.)")
    print("  - Para adicionar materias exclusivas do Tecnico, crie modulos com cargo_id=2")

if __name__ == '__main__':
    migrate()
