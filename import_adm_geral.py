import sqlite3
import re

DB_PATH = 'tjsc_plan.db'

adm_raw = """
Teorias Burocrática da Administração 00:37:53 Teoria das Relações Humanas | Parte I 00:30:01 Teoria das Relações Humanas | Parte II 00:33:03 Teoria Clássica - Parte I 00:29:59 Teoria Clássica - Parte II 00:30:21 Teoria Clássica - Parte III 00:21:01 Teoria Científica - Parte I 00:29:54 Teoria Científica - Parte II 00:30:54 Teoria Estruturalista - Parte I 00:30:57 Teoria Estruturalista - Parte II 00:31:03 Teoria Neoclássica - Parte I 00:30:49 Teoria Neoclássica - Parte II 00:35:15 Teoria Neoclássica - Parte III 00:30:16 Teoria dos Sistemas 00:44:55 Teoria Comportamental 00:55:02 Teoria Contingencial | Parte I 00:29:37 Teoria Contingencial | Parte II 00:26:59 Funções da Administração/Processo Organizacional: planejamento, direção, comunicação, controle e avaliação | Parte I 00:25:15 Funções da Administração/Processo Organizacional: planejamento, direção, comunicação, controle e avaliação | Parte II 00:32:26 Características básicas das organizações formais modernas: tipos de estrutura organizacional, natureza, finalidades e critérios de departamentalização | Parte I 00:31:05 Características básicas das organizações formais modernas: tipos de estrutura organizacional, natureza, finalidades e critérios de departamentalização | Parte II 00:35:28 Características básicas das organizações formais modernas: tipos de estrutura organizacional, natureza, finalidades e critérios de departamentalização | Parte III 00:41:04 Planejamento Estratégico | Parte I 00:30:06 Planejamento Estratégico | Parte II 00:30:05 Planejamento Estratégico | Parte III 00:27:02 Gestão da Qualidade | Parte I 00:29:07 Gestão da Qualidade | Parte II 00:19:02 Gestão da Qualidade | Parte III 00:36:45 Gestão por Projetos | Parte I 00:30:19 Gestão por Projetos | Parte II 00:30:24 Gestão por Projetos | Parte III 00:33:24 Gestão por Projetos | Parte IV 00:45:06 Ferramentas e Métodos de Gestão de Projetos: PERT/CPM 00:21:01 Ferramentas e Métodos de Gestão de Projetos: SCRUM 00:20:05 Ferramentas e Métodos de Gestão de Projetos: Kanban 00:17:37 Ferramentas e Métodos de Gestão de Projetos: Matriz RACI
"""

def parse_classes(raw_text):
    pattern = r"(.*?)\s+(\d{1,2}:\d{2}:\d{2})"
    matches = re.findall(pattern, raw_text.strip())
    
    parsed = []
    for title, duration in matches:
        parts = list(map(int, duration.split(':')))
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

    # Insert Administração Module
    cursor.execute('INSERT INTO modules (name) VALUES (?)', ("Administração Geral - Fábio de Assis",))
    module_id = cursor.lastrowid

    classes = parse_classes(adm_raw)
    
    for title, duration in classes:
        cursor.execute('INSERT INTO classes (module_id, title, duration_minutes) VALUES (?, ?, ?)', 
                       (module_id, title, duration))

    # Handle the last one "Matriz RACI" if missing duration
    if "Matriz RACI" in adm_raw and "Matriz RACI" not in [c[0] for c in classes]:
        cursor.execute('INSERT INTO classes (module_id, title, duration_minutes) VALUES (?, ?, ?)',
                       (module_id, "Ferramentas e Métodos de Gestão de Projetos: Matriz RACI", 25))

    conn.commit()
    conn.close()
    print(f"Inseridas {len(classes) + 1} aulas de Adm Geral com sucesso.")

if __name__ == '__main__':
    update_db()
