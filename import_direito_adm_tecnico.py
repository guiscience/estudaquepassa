import sqlite3
import re

DB_PATH = "tjsc_plan.db"

direito_adm_raw = """
Regime Jurídico Administrativo e os Princípios da Administração Pública | Parte I 00:29:56
Regime Jurídico Administrativo e os Princípios da Administração Pública | Parte II 00:29:58
Questões de Princípios 00:09:59
Organização da Administração Pública | Parte I 00:29:57
Organização da Administração Pública | Parte II 00:29:59
Organização da Administração Pública | Parte III 00:30:00
Questões de Organização da Administração Pública 00:09:58
Agentes Públicos | Parte I 00:29:57
Agentes Públicos | Parte II 00:29:59
Agentes Públicos | Parte III 00:30:02
Agentes Públicos | Parte IV 00:29:57
Agentes Públicos | Parte V 00:29:54
Questões de Agentes Públicos 00:10:17
Poderes Administrativos | Parte I 00:29:40
Poderes Administrativos | Parte II 00:29:57
Questões de Poderes Administrativos 00:09:55
Atos Administrativos | Parte I 00:29:55
Atos Administrativos | Parte II 00:30:03
Atos Administrativos | Parte III 00:29:59
Questões de Atos Administrativos 00:09:54
Licitações e Contratos Administrativos | Parte I 00:29:56
Licitações e Contratos Administrativos | Parte II 00:29:58
Licitações e Contratos Administrativos | Parte III 00:30:00
Licitações e Contratos Administrativos | Parte IV 00:29:59
Licitações e Contratos Administrativos | Parte V 00:29:57
Questões de Licitações e Contratos Administrativos 00:09:58
Estrutura administrativa do Poder Judiciário de Santa Catarina e suas funções básicas
"""


def parse_classes(raw_text):
    pattern = r"(.*?)\s+(\d{1,2}:\d{2}:\d{2})"
    matches = re.findall(pattern, raw_text.strip())

    parsed = []
    for title, duration in matches:
        parts = list(map(int, duration.split(":")))
        if len(parts) == 3:
            h, m, s = parts
        else:
            h = 0
            m, s = parts

        total_minutes = (h * 60) + m + (1 if s > 30 else 0)
        parsed.append((title.strip(), total_minutes))
    return parsed


def update_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO modules (name, cargo_id) VALUES (?, ?)",
        ("Direito Administrativo (Técnico)", 2),
    )
    module_id = cursor.lastrowid
    print(f"Criado módulo ID {module_id} para Técnico")

    classes = parse_classes(direito_adm_raw)

    for title, duration in classes:
        cursor.execute(
            "INSERT INTO classes (module_id, title, duration_minutes) VALUES (?, ?, ?)",
            (module_id, title, duration),
        )

    conn.commit()
    conn.close()
    print(
        f"Inseridas {len(classes)} aulas de Direito Administrativo Técnico com sucesso."
    )


if __name__ == "__main__":
    update_db()
