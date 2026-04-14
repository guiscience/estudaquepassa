import sqlite3

DB_PATH = "tjsc_plan.db"

legislacao_topics = [
    "Organização e funcionamento do Poder Judiciário de Santa Catarina",
    "Regimento Interno do Tribunal de Justiça de Santa Catarina",
    "Normas da Corregedoria-Geral da Justiça",
    "Regime Jurídico dos Servidores Públicos Civis do Estado de Santa Catarina",
]


def update_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO modules (name, cargo_id) VALUES (?, ?)",
        ("Legislação Institucional do PJSC - Nathan Pilonetto (Técnico)", 2),
    )
    module_id = cursor.lastrowid
    print(f"Criado módulo ID {module_id} para Técnico")

    for title in legislacao_topics:
        cursor.execute(
            "INSERT INTO classes (module_id, title, duration_minutes) VALUES (?, ?, ?)",
            (module_id, title, 0),
        )

    conn.commit()
    conn.close()
    print(
        f"Inseridas {len(legislacao_topics)} aulas de Legislação Institucional Técnico (duração: 0)"
    )


if __name__ == "__main__":
    update_db()
