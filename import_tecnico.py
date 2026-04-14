import sqlite3
import re

DB_PATH = "tjsc_plan.db"

tecnico_raw = """
Ortografia 01:07:47
Questões de Ortografia 00:49:48
Classes Gramaticais e suas funções sintáticas 01:01:54
Questões de Classes de Palavras 00:21:23
Verbos 01:08:23
Questões de Verbos 00:46:39
Termos da oração 01:24:55
Concordância Nominal e Concordância Verbal - Parte I 00:26:04
Concordância Nominal e Concordância Verbal - Parte II 00:07:50
Questões comentadas Concordância Nominal e Concordância Verbal e termos da oração. 00:53:40
Colocação Pronominal 01:04:30
Questões de Pronomes 00:46:16
Regência e Crase 01:09:46
Questões de Regência e Crase 00:51:11
Vozes Verbais e SE 01:11:40
Pronomes Relativos e QUE 01:07:56
Questões de Funções do Que e do Se 00:57:23
Período Composto/Orações Coordenadas e Subordinadas 01:32:11
Questões de Orações Coordenadas e Subordinadas 00:49:05
Pontuação 01:03:16
Questões de Pontuação 00:59:18
Interpretação de texto 00:34:49
Contexto, coesão, denotação, conotação e intertextualidade 00:33:56
Domínio da temática dos parágrafos 00:24:50
Tipos e gêneros textuais 00:39:00
Gêneros textuais e os tipos de coesão 00:28:57
Figuras de linguagem | Parte I 00:37:58
Figuras de linguagem | Parte II 00:28:46
Funções da linguagem, tipos de discurso e variações linguísticas 00:27:52
Questões de Interpretação de texto e tipologia textual 00:29:35
Revisão Final em Questões FGV - Parte I 00:40:34
Revisão Final em Questões FGV - Parte II 00:44:06
Revisão Final em Questões FGV - Parte III 00:44:57
Revisão Final em Questões FGV - Parte IV 00:52:54
Revisão Final em Questões FGV - Parte V 00:40:08
Revisão Final em Questões FGV - Parte VI 00:35:26
Revisão Final em Questões FGV - Parte VII 00:32:58
Revisão Final em Questões FGV - Parte VIII 00:43:41
Revisão Final em Questões FGV - Parte IX 00:25:07
Revisão Final em Questões FGV - Parte X 00:45:18
Revisão Final em Questões FGV - Parte XI 00:31:49
Revisão Final em Questões FGV - Parte XII 00:36:22
Revisão Final em Questões FGV - Parte XIII 00:29:15
Revisão Final em Questões FGV - Parte XIV 00:44:01
Revisão Final em Questões FGV - Parte XV 00:33:35
Revisão Final em Questões FGV - Parte XVI 00:25:52
Revisão Final em Questões FGV - Parte XVII 00:45:26
Revisão Final em Questões FGV - Parte XVIII 00:37:00
Revisão Final em Questões FGV - Parte XIX 00:29:52
Revisão Final em Questões FGV - Parte XX 00:43:12
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
        ("Língua Portuguesa - Janaína Souto (Técnico)", 2),
    )
    module_id = cursor.lastrowid
    print(f"Criado módulo ID {module_id} para Técnico")

    classes = parse_classes(tecnico_raw)

    for title, duration in classes:
        cursor.execute(
            "INSERT INTO classes (module_id, title, duration_minutes) VALUES (?, ?, ?)",
            (module_id, title, duration),
        )

    conn.commit()
    conn.close()
    print(f"Inseridas {len(classes)} aulas de Português Técnico com sucesso.")


if __name__ == "__main__":
    update_db()
