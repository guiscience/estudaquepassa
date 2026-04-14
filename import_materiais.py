import sqlite3
import re

DB_PATH = 'tjsc_plan.db'

mat_raw = """
Conceitos e Classificação de Materiais 00:40:52 Gestão Patrimonial (Controle de bens, Inventário, Alterações e baixa de bens) 00:21:37 Recursos Patrimoniais 00:12:54 Logística reversa 00:10:27 Logística e transformação digital 00:20:34 Gerenciamento da Cadeia de Suprimento 00:17:17 Armazenamento de Materiais 00:24:16 Administração de Compras 00:21:10 Gestão de Estoques
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

    # Insert Adm Materiais Module
    cursor.execute('INSERT INTO modules (name) VALUES (?)', ("Adm de Materiais e Logística - Fábio de Assis",))
    module_id = cursor.lastrowid

    classes = parse_classes(mat_raw)
    
    for title, duration in classes:
        cursor.execute('INSERT INTO classes (module_id, title, duration_minutes) VALUES (?, ?, ?)', 
                       (module_id, title, duration))

    # Handle the last one "Gestão de Estoques" if missing duration
    if "Gestão de Estoques" in mat_raw and "Gestão de Estoques" not in [c[0] for c in classes]:
        cursor.execute('INSERT INTO classes (module_id, title, duration_minutes) VALUES (?, ?, ?)',
                       (module_id, "Gestão de Estoques", 30))

    conn.commit()
    conn.close()
    print(f"Inseridas {len(classes) + 1} aulas de Adm de Materiais com sucesso.")

if __name__ == '__main__':
    update_db()
