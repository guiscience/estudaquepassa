import sqlite3

DB_PATH = "tjsc_plan.db"

etica_topics = [
    "Gestão de pessoas e comportamento organizacional, incluindo trabalho em equipe, comunicação e atitudes éticas",
    "Integridade institucional no Poder Judiciário, abordando padrões éticos, transparência, prevenção de irregularidades e observância ao Código de Ética e Conduta do Poder Judiciário de Santa Catarina",
    "Resolução TJ nº 22/2021 do TJSC",
    "Princípios básicos da Administração Pública, como legalidade, moralidade, interesse público, integridade e probidade",
    "Deveres e responsabilidades do servidor, abrangendo conduta, sanções e processos disciplinares",
    "Noções de improbidade administrativa, com destaque para atos proibidos e suas consequências",
]


def update_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO modules (name, cargo_id) VALUES (?, ?)",
        ("Ética e Gestão no Serviço Público (Técnico)", 2),
    )
    module_id = cursor.lastrowid
    print(f"Criado módulo ID {module_id} para Técnico")

    for title in etica_topics:
        cursor.execute(
            "INSERT INTO classes (module_id, title, duration_minutes) VALUES (?, ?, ?)",
            (module_id, title, 0),
        )

    conn.commit()
    conn.close()
    print(f"Inseridas {len(etica_topics)} aulas de Ética Técnico (duração: 0)")


if __name__ == "__main__":
    update_db()
