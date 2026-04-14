import sqlite3

DB_PATH = "tjsc_plan.db"

regimento_topics = ["Estrutura e competências do Poder Judiciário de Santa Catarina"]


def update_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO modules (name, cargo_id) VALUES (?, ?)",
        ("Regimento Interno TJSC (Técnico)", 2),
    )
    module_id = cursor.lastrowid
    print(f"Criado módulo ID {module_id} para Técnico")

    for title in regimento_topics:
        cursor.execute(
            "INSERT INTO classes (module_id, title, duration_minutes) VALUES (?, ?, ?)",
            (module_id, title, 0),
        )

    conn.commit()
    conn.close()
    print(f"Inserido módulo de Regimento Interno TJSC")


if __name__ == "__main__":
    update_db()
