import sqlite3
import re

DB_PATH = "tjsc_plan.db"

proc_penal_raw = """
Princípios | Parte I 00:52:36
Princípios | Parte II 00:47:50
Princípios | Parte III 01:01:17
Princípios | Parte IV 00:55:16
Questões de Processo Penal | Princípios 01:05:39
Disposições Preliminares 00:49:17
Mapa da Lei | Memorize e Revise 00:48:16
Questões de Processo Penal | Disposições Preliminares 00:43:45
Juiz das Garantias 01:03:14
Mapa da Lei | Memorize e Revise 00:58:30
Inquérito policial | Parte I 01:01:03
Inquérito policial | Parte II 01:01:16
Inquérito policial | Parte III 01:07:46
Mapa da Lei | Memorize e Revise 01:03:19
Questões de Processo Penal | Inquérito Policial 01:14:35
Ação Penal 01:00:34
Mapa da Lei | Memorize e Revise 01:02:11
Questões de Processo Penal | Ação Penal 01:06:28
Sujeitos Processuais: Do Juiz, do Ministério Público, do Acusado e Defensor, dos Assistentes e Auxiliares da Justiça 01:03:25
Mapa da Lei | Memorize e Revise 00:58:32
Citações e Intimações 00:55:40
Sentença | Parte I 01:07:03
Sentença | Parte II 01:12:54
Procedimentos - Processo Comum | Parte I 01:03:24
Procedimentos - Processo Comum | Parte II 01:16:19
Procedimentos - Processo Comum | Parte III 01:04:53
Procedimentos - Processo Comum | Parte IV 01:07:38
Questões de Processo Penal | Procedimentos 00:47:09
Habeas Corpus 00:54:37
Medidas cautelares diversas da prisão | Parte I 01:03:41
Medidas cautelares diversas da prisão | Parte II 00:36:58
Prisão em flagrante | Parte I 01:02:12
Prisão em flagrante | Parte II 00:57:36
Prisão em Flagrante | Parte III 00:26:50
Questões de Processo Penal | Prisão em flagrante 01:06:22
Prisão Preventiva | Parte II 00:13:00
Prisão Preventiva | Parte I 01:02:15
Questões de Processo Penal | Prisão preventiva 01:03:33
Prisão domiciliar 00:27:34
Questões de Processo Penal | Prisão domiciliar 00:56:44
Prisão temporária 01:05:05
Questões de Processo Penal | Prisão temporária 01:00:28
Liberdade provisória 00:36:39
Das Outras Medidas Cautelares 01:07:23
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
        ("Noções de Direito Processual Penal - Priscilla Fernandes (Técnico)", 2),
    )
    module_id = cursor.lastrowid
    print(f"Criado módulo ID {module_id} para Técnico")

    classes = parse_classes(proc_penal_raw)

    for title, duration in classes:
        cursor.execute(
            "INSERT INTO classes (module_id, title, duration_minutes) VALUES (?, ?, ?)",
            (module_id, title, duration),
        )

    conn.commit()
    conn.close()
    print(
        f"Inseridas {len(classes)} aulas de Direito Processual Penal Técnico com sucesso."
    )


if __name__ == "__main__":
    update_db()
