import sqlite3
import re

DB_PATH = 'tjsc_plan.db'

transp_raw = """
Lei de Acesso à Informação (Lei nº 12.527/2011) | Parte I 00:12:51 Lei de Acesso à Informação (Lei nº 12.527/2011) | Parte II 00:30:09 Lei de Acesso à Informação (Lei nº 12.527/2011) | Parte III 00:20:40 Lei de Acesso à Informação (Lei nº 12.527/2011) | Parte IV 00:25:53 Lei de Acesso à Informação (Lei nº 12.527/2011) | Parte V 00:23:52 Lei de Accesso à Informação (Lei nº 12.527/2011) | Parte VI 00:30:04 Lei de Acesso à Informação (Lei nº 12.527/2011) | Parte VII 00:30:31 Lei de Acesso à Informação (Lei nº 12.527/2011) | Parte VIII 00:10:17 Lei de Acesso à Informação (Lei nº 12.527/2011) | Parte IX 00:25:35 Lei de Acesso à Informação (Lei nº 12.527/2011) | Parte X 00:20:12 Lei de Acesso à Informação (Lei nº 12.527/2011) | Parte XI 00:25:26 Lei de Acesso à Informação (Lei nº 12.527/2011) | Parte XII 00:27:22 Questões da Lei de Acesso à Informação (Lei nº 12.527/2011) | Parte I 00:30:32 Questões da Lei de Acesso à Informação (Lei nº 12.527/2011) | Parte II 00:34:37 Lei complementar 131/2009
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

    # Insert Transparencia Module
    cursor.execute('INSERT INTO modules (name) VALUES (?)', ("Transparência e Controle - LAI",))
    module_id = cursor.lastrowid

    classes = parse_classes(transp_raw)
    
    for title, duration in classes:
        cursor.execute('INSERT INTO classes (module_id, title, duration_minutes) VALUES (?, ?, ?)', 
                       (module_id, title, duration))

    extra = 0
    if "Lei complementar 131/2009" in transp_raw and "Lei complementar 131/2009" not in [c[0] for c in classes]:
        cursor.execute('INSERT INTO classes (module_id, title, duration_minutes) VALUES (?, ?, ?)',
                       (module_id, "Lei complementar 131/2009", 25))
        extra = 1

    conn.commit()
    conn.close()
    print(f"Inseridas {len(classes) + extra} aulas de Transp e Controle com sucesso.")

if __name__ == '__main__':
    update_db()
