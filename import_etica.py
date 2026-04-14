import sqlite3
import re

DB_PATH = 'tjsc_plan.db'

etica_raw = """
Princípios Expressos: legalidade, impessoalidade, moralidade, publicidade e eficiência 00:33:02 Princípios Implícitos na CF 88 | Parte 1 00:32:59 Princípios Implícitos na CF 88 | Parte 2 00:28:16 Princípios Implícitos na CF 88 | Parte 3 00:17:24 Questões de Princípios 00:25:42 Questões de Princípios 00:37:28 check Lei n. 8.429/1992 - Lei de Improbidade Administrativa | Introdução - Aula 01 00:39:32 check Lei n. 8.429/1992 - Lei de Improbidade Administrativa | Dos atos de improbidade - Aula 02 00:24:55 check Lei n. 8.429/1992 - Lei de Improbidade Administrativa | Dos Atos de Improbidade Administrativa que Causam Prejuízo ao Erário - Aula 03 00:24:11 check Lei n. 8.429/1992 - Lei de Improbidade Administrativa | Dos Atos que Atentam Contra os Princípios da Administração Pública - Aula 04 00:26:58 check Lei n. 8.429/1992 - Lei de Improbidade Administrativa | Penas - Aula 05 00:20:23 check Lei n. 8.429/1992 - Lei de Improbidade Administrativa | Do Processo Administrativo e Judicial - Aula 06 00:38:59 check Lei n. 8.429/1992 - Lei de Improbidade Administrativa | Das disposições Penais Aula 07 00:11:58 Lei 12.846/13 - Lei Anticorrupção - Disposições Gerais | Art. 1 ao 4 00:19:50 Lei 12.846/13 - Lei Anticorrupção - Atos Lesivos à Administração Nacional ou Estrangeira | Art. 5 00:18:01 Lei 12.846/13 - Lei Anticorrupção - Responsabilização Administrativa | Art. 6 ao 7 00:23:46 Lei 12.846/13 - Lei Anticorrupção - Processo Administrativo de Responsabilização | Art. 8 ao 15 00:23:38 Lei 12.846/13 - Lei Anticorrupção - Acordo de Leniência e Responsabilização Judicial | Art. 16 ao 21 00:27:48 Lei 12.846/13 - Lei Anticorrupção - Disposições Finais | Art. 22 ao 31 00:15:47 Deveres e responsabilidades do servidor, abrangendo conduta, sanções e processos disciplinares Integridade institucional no Poder Judiciário, abordando padrões éticos, transparência, prevenção de irregularidades e observância ao Código de Ética e Conduta do Poder Judiciário de Santa Catarina Resolução TJ nº 22/2021 do TJSC Evolução dos Modelos de Gestão de Pessoas | Parte I 00:30:52 Evolução dos Modelos de Gestão de Pessoas | Parte II 00:32:45 Motivação | Parte I 00:35:33 Motivação | Parte II 00:25:11 Liderança | Parte I 00:32:25 Liderança | Parte II 00:31:47 Liderança | Parte III 00:36:18 Grupos e Equipes | Parte I 00:30:12 Grupos e Equipes | Parte II 00:37:03 Comunicação | Parte I 00:30:17 Comunicação | Parte II 00:38:14 Cultura Organizacional | Parte I 00:30:20 Cultura Organizacional | Parte II 00:30:18 Cultura Organizacional | Parte III 00:31:04 Comportamento Organizacional | Parte I 00:31:34 Comportamento Organizacional | Parte II
"""

def parse_classes(raw_text):
    pattern = r"(.*?)\s+(\d{1,2}:\d{2}:\d{2})"
    matches = re.findall(pattern, raw_text.strip())
    
    parsed = []
    for title, duration in matches:
        clean_title = title.replace("check", "").strip()
        parts = list(map(int, duration.split(':')))
        if len(parts) == 3:
            h, m, s = parts
        else:
            h = 0
            m, s = parts
        total_minutes = (h * 60) + m + (1 if s > 30 else 0)
        parsed.append((clean_title, total_minutes))
    return parsed

def update_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('INSERT INTO modules (name) VALUES (?)', ("Ética e Gestão no Serviço Público - Nathan Pilonetto",))
    module_id = cursor.lastrowid

    classes = parse_classes(etica_raw)
    
    # Titles already added to avoid adding the manual missing items twice
    added_titles = set([c[0] for c in classes])

    for title, duration in classes:
        cursor.execute('INSERT INTO classes (module_id, title, duration_minutes) VALUES (?, ?, ?)', 
                       (module_id, title, duration))

    # Add items without duration manually
    missing_items = [
        "Deveres e responsabilidades do servidor, abrangendo conduta, sanções e processos disciplinares",
        "Integridade institucional no Poder Judiciário",
        "Resolução TJ nº 22/2021 do TJSC"
    ]
    for item in missing_items:
        cursor.execute('INSERT INTO classes (module_id, title, duration_minutes) VALUES (?, ?, ?)',
                       (module_id, item, 30))

    conn.commit()
    conn.close()
    print(f"Inseridas {len(classes) + len(missing_items)} aulas de Ética com sucesso.")

if __name__ == '__main__':
    update_db()
