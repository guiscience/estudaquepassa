import sqlite3
import re

DB_PATH = "tjsc_plan.db"

proc_civil_raw = """
Normas Fundamentais do Processo Civil - Parte 1 00:30:37
Normas Fundamentais do Processo Civil - Parte 2 00:31:02
Normas Fundamentais do Processo Civil - Parte 3 00:31:49
Normas Fundamentais do Processo Civil - Parte 4 00:31:35
Normas Fundamentais do Processo Civil - Parte 5 00:37:01
Aplicação das Normas Processuais | Art. 13 ao Art. 15 00:15:29
Jurisdição | Parte 1 00:32:00
Jurisdição | Parte 2 00:33:26
Jurisdição | Parte 3 00:31:21
Jurisdição | Parte 4 00:35:05
Jurisdição | Parte 5 00:31:19
Jurisdição | Parte 6 00:43:50
Jurisdição | Parte 7 00:35:10
Direito de Ação 00:32:08
Direito de Ação | Teorias Explicativas do Direito de Ação 00:34:50
Direito de Ação | Condições e Elementos da Ação 00:32:36
Direito de Ação | Elementos, Condições e Classificação da Ação 00:33:25
Direito de Ação | Classificação da Ação e Sucessão Processual 00:34:39
Direito de Ação | Questões de Fixação 00:12:03
Limites da Jurisdição Nacional | Parte 1 00:30:55
Limites da Jurisdição Nacional | Parte 2 00:10:03
Cooperação Internacional - Disposições Gerais (Art. 26 ao 27) 00:15:24
Cooperação Internacional - Do Auxílio Direto (Art 28 ao 34) 00:26:26
Cooperação Internacional - Da Carta Rogatória (Art. 35 e 36) 00:10:46
Cooperação Internacional - Disposições Comuns às Seções Anteriores (Art. 37 ao 41) 00:09:08
Competência | Parte 1 00:35:54
Competência | Parte 2 00:34:04
Competência | Parte 3 00:33:03
Competência | Parte 4 00:31:31
Competência | Parte 5 00:17:29
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
        ("Noções de Direito Processual Civil - Raquel Bueno (Técnico)", 2),
    )
    module_id = cursor.lastrowid
    print(f"Criado módulo ID {module_id} para Técnico")

    classes = parse_classes(proc_civil_raw)

    for title, duration in classes:
        cursor.execute(
            "INSERT INTO classes (module_id, title, duration_minutes) VALUES (?, ?, ?)",
            (module_id, title, duration),
        )

    conn.commit()
    conn.close()
    print(
        f"Inseridas {len(classes)} aulas de Direito Processual Civil Técnico com sucesso."
    )


if __name__ == "__main__":
    update_db()
