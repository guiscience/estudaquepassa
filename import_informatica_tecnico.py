import sqlite3
import re

DB_PATH = "tjsc_plan.db"

informatica_raw = """
Hardware | Parte I 00:37:19
Hardware | Parte II 00:30:25
Hardware | Parte III 00:28:40
Hardware | Parte IV 00:28:14
Hardware | Parte V 00:29:35
Hardware | Parte VI 00:12:27
Hardware - Revisão 00:15:51
Hardware - Questões | Parte I 00:24:27
Hardware - Questões | Parte II 00:30:05
Software 00:26:07
Sistema Operacional Windows 11 | Parte I 01:11:42
Sistema Operacional Windows 11 | Parte II 01:35:44
Sistema Operacional Windows 11 | Parte III 01:12:53
Questões de Sistema Operacional Windows 11 00:49:58
Internet | Parte I 00:55:16
Internet | Parte II 01:57:21
Internet | Parte III 00:48:15
Questões | Internet 01:00:30
Intranet 00:42:44
Questões | Intranet 00:37:14
Busca e Pesquisa 00:36:30
Questões | Busca e Pesquisa 00:59:50
Segurança da Informação - Antivirus | Parte I 00:28:07
Segurança da Informação - Firewall | Parte II 00:24:58
BLOCO I - Segurança da Informação | Parte III 00:33:24
BLOCO I - Segurança da Informação | Parte IV 00:33:46
BLOCO I - Segurança da Informação | Parte V 00:31:10
BLOCO I - Segurança da Informação | Parte VI 00:33:44
BLOCO II - Segurança da Informação | Parte I 00:31:51
BLOCO II - Segurança da Informação | Parte II 00:30:28
BLOCO II - Segurança da Informação | Parte III 00:29:39
BLOCO II - Segurança da Informação | Parte IV 00:32:16
Segurança da Informação | Revisão 00:16:31
Segurança da Informação | Questões: BLOCO I - Parte I 00:29:20
Segurança da Informação | Questões: BLOCO I - Parte II 00:29:57
Segurança da Informação | Questões: BLOCO II - Parte I 00:29:06
Segurança da Informação | Questões: BLOCO II - Parte II 00:33:52
Lei nº 13.709/2018 | Introdução e Fundamentos 01:00:56
Lei nº 13.709/2018 | Dos Requisitos para o Tratamento de Dados Pessoais 00:48:32
Lei nº 13.709/2018 | Dos Direitos do Titular 00:41:15
Lei nº 13.709/2018 | Tratamento de Dados Pessoais Pelo Poder Público 00:32:12
Lei nº 13.709/2018 | Transferência Internacional de Dados 00:28:13
Lei nº 13.709/2018 | Controlador e Operador 00:44:45
RESUMÃO - Mapeando a Lei 13.709/2018 00:36:01
Questões da Lei nº 13.709, de 14 de agosto de 2018 (LGPD) 00:32:28
Resolução TJ nº 3/2021 do TJSC
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
        ("Informática e Proteção de Dados - Léo Matos (Técnico)", 2),
    )
    module_id = cursor.lastrowid
    print(f"Criado módulo ID {module_id} para Técnico")

    classes = parse_classes(informatica_raw)

    for title, duration in classes:
        cursor.execute(
            "INSERT INTO classes (module_id, title, duration_minutes) VALUES (?, ?, ?)",
            (module_id, title, duration),
        )

    conn.commit()
    conn.close()
    print(f"Inseridas {len(classes)} aulas de Informática Técnico com sucesso.")


if __name__ == "__main__":
    update_db()
