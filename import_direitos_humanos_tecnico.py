import sqlite3

DB_PATH = "tjsc_plan.db"

direitos_humanos_topics = [
    "Princípios básicos dos direitos humanos",
    "Proteção internacional e constitucional dos direitos fundamentais",
    "Acesso à justiça e garantias processuais",
    "Igualdade, não discriminação e grupos vulneráveis",
    "Políticas judiciárias de inclusão e cidadania",
]


def update_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO modules (name, cargo_id) VALUES (?, ?)",
        ("Direitos Humanos e Acesso à Justiça - Júlio Raizer (Técnico)", 2),
    )
    module_id = cursor.lastrowid
    print(f"Criado módulo ID {module_id} para Técnico")

    for title in direitos_humanos_topics:
        cursor.execute(
            "INSERT INTO classes (module_id, title, duration_minutes) VALUES (?, ?, ?)",
            (module_id, title, 0),
        )

    conn.commit()
    conn.close()
    print(
        f"Inseridas {len(direitos_humanos_topics)} aulas de Direitos Humanos Técnico (duração: 0)"
    )


if __name__ == "__main__":
    update_db()
