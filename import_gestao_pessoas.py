import sqlite3
import re

DB_PATH = 'tjsc_plan.db'

gp_raw = """
Evolução dos Modelos de Gestão de Pessoas | Parte I 00:30:52 Evolução dos Modelos de Gestão de Pessoas | Parte II 00:32:45 Ciclo de Gestão de Pessoas | Parte I 00:33:38 Ciclo de Gestão de Pessoas | Parte II 00:27:33 Ciclo de Gestão de Pessoas | Parte III 00:25:52 Ciclo de Gestão de Pessoas | Parte IV 00:31:08 Ciclo de Gestão de Pessoas | Parte V 00:31:00 Ciclo de Gestão de Pessoas | Parte VI 00:32:16 Liderança | Parte I 00:32:25 Liderança | Parte II 00:31:47 Liderança | Parte III 00:36:18 Motivação | Parte I 00:35:33 Motivação | Parte II 00:25:11 Processo Decisório | Parte I 00:30:03 Processo Decisório | Parte II 00:29:50 Comportamento Organizacional | Parte I 00:31:34 Comportamento Organizacional | Parte II 00:30:12 Comunicação | Parte I 00:30:17 Comunicação | Parte II 00:38:14 Cultura Organizacional | Parte I 00:30:20 Cultura Organizacional | Parte II 00:30:18 Cultura Organizacional | Parte III 00:31:04 Grupos e Equipes | Parte I 00:30:12 Grupos e Equipes | Parte II 00:37:03 Desenvolvimento Organizacional – DO | Parte I 00:30:02 Desenvolvimento Organizacional – DO | Parte II
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

    # Insert Gestão de Pessoas Module
    cursor.execute('INSERT INTO modules (name) VALUES (?)', ("Gestão de Pessoas - Fábio de Assis",))
    module_id = cursor.lastrowid

    classes = parse_classes(gp_raw)
    
    for title, duration in classes:
        cursor.execute('INSERT INTO classes (module_id, title, duration_minutes) VALUES (?, ?, ?)', 
                       (module_id, title, duration))

    # Handle the last one if missing duration
    if "Desenvolvimento Organizacional – DO | Parte II" in gp_raw and "Desenvolvimento Organizacional – DO | Parte II" not in [c[0] for c in classes]:
        cursor.execute('INSERT INTO classes (module_id, title, duration_minutes) VALUES (?, ?, ?)',
                       (module_id, "Desenvolvimento Organizacional – DO | Parte II", 30))

    conn.commit()
    conn.close()
    print(f"Inseridas {len(classes) + 1} aulas de Gestão de Pessoas com sucesso.")

if __name__ == '__main__':
    update_db()
