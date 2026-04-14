import sqlite3
import re

DB_PATH = 'tjsc_plan.db'

ap_raw = """
Modelos Teóricos da Administração Pública | Burocracia 00:50:13 Modelos Teóricos da Administração Pública | Gerencialismo 00:31:09 Modelos Teóricos da Administração Pública | Patrimonialismo 00:46:12 Históricos e Reformas da Administração Pública no Brasil 00:42:13 Governança e gestão pública | Parte I 00:30:08 Governança e gestão pública | Parte II 00:33:14 Governança Corporativa e Compliance 00:34:43 Gestão de resultados na produção de serviços públicos | Parte I 00:29:49 Gestão de resultados na produção de serviços públicos | Parte II
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

    # Insert Adm Publica Module
    cursor.execute('INSERT INTO modules (name) VALUES (?)', ("Administração Pública - Fábio de Assis",))
    module_id = cursor.lastrowid

    classes = parse_classes(ap_raw)
    
    for title, duration in classes:
        cursor.execute('INSERT INTO classes (module_id, title, duration_minutes) VALUES (?, ?, ?)', 
                       (module_id, title, duration))

    extra = 0
    if "Gestão de resultados na produção de serviços públicos | Parte II" in ap_raw and "Gestão de resultados na produção de serviços públicos | Parte II" not in [c[0] for c in classes]:
        cursor.execute('INSERT INTO classes (module_id, title, duration_minutes) VALUES (?, ?, ?)',
                       (module_id, "Gestão de resultados na produção de serviços públicos | Parte II", 30))
        extra = 1

    conn.commit()
    conn.close()
    print(f"Inseridas {len(classes) + extra} aulas de Adm Pública com sucesso.")

if __name__ == '__main__':
    update_db()
