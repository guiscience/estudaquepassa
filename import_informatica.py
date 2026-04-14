import sqlite3
import re

DB_PATH = 'tjsc_plan.db'

info_raw = """
Hardware | Parte 1 00:33:15 Hardware | Parte 2 00:33:55 Hardware | Parte 3 00:22:35 Hardware | Parte 4 00:31:24 Hardware | Parte 5 00:31:39 Hardware | Parte 6 00:31:47 Software | Parte 1 00:22:11 Software | Parte 2 00:42:02 Sistema Operacional Windows | Parte 1 00:27:10 Sistema Operacional Windows | Parte 2 00:35:45 Sistema Operacional Windows | Parte 3 00:26:58 Sistema Operacional Windows | Parte 4 00:24:14 Redes de Computadores | Parte 1 00:23:12 Redes de Computadores | Parte 2 00:24:27 Redes de Computadores | Parte 3 00:28:46 Redes de Computadores | Parte 4 00:51:53 Conceitos de Internet e Intranet 00:17:46 Segurança da Informação | Parte 1 00:19:46 Segurança da Informação | Parte 2 00:20:59 Segurança da Informação | Parte 3 00:25:47 Segurança da Informação | Parte 4 00:20:45 Segurança da Informação | Parte 5 00:23:33 Segurança da Informação | Parte 6 00:18:44 Segurança da Informação | Parte 7 00:23:02 Segurança da Informação | Parte 8 00:22:27 Segurança da Informação | Parte 9 00:27:18 Segurança da Informação | Parte 10 00:31:06 Lei nº 13.709/2018 | Introdução e Fundamentos 01:00:56 Lei nº 13.709/2018 | Dos Requisitos para o Tratamento de Dados Pessoais 00:48:32 Lei nº 13.709/2018 | Dos Direitos do Titular 00:41:15 Lei nº 13.709/2018 | Tratamento de Dados Pessoais Pelo Poder Público 00:32:12 check Lei nº 13.709/2018 | Transferência Internacional de Dados 00:28:13 check Lei nº 13.709/2018 | Controlador e Operador 00:44:45 check RESUMÃO - Mapeando a Lei 13.709/2018 00:36:01 Questões da Lei nº 13.709, de 14 de agosto de 2018 (LGPD) 00:32:28 Resolução TJ nº 3/2021 do TJSC
"""

def parse_classes(raw_text):
    # Match Title + HH:MM:SS
    pattern = r"(.*?)\s+(\d{1,2}:\d{2}:\d{2})"
    matches = re.findall(pattern, raw_text.strip())
    
    parsed = []
    for title, duration in matches:
        # Clean "check" prefix if present
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

    # Insert Informática Module
    cursor.execute('INSERT INTO modules (name) VALUES (?)', ("Informática e LGPD - Léo Matos",))
    module_id = cursor.lastrowid

    classes = parse_classes(info_raw)
    
    for title, duration in classes:
        cursor.execute('INSERT INTO classes (module_id, title, duration_minutes) VALUES (?, ?, ?)', 
                       (module_id, title, duration))

    # Handling the last one without duration specifically if it wasn't caught
    if "Resolução TJ nº 3/2021" in info_raw and "Resolução TJ nº 3/2021" not in [c[0] for c in classes]:
        cursor.execute('INSERT INTO classes (module_id, title, duration_minutes) VALUES (?, ?, ?)',
                       (module_id, "Resolução TJ nº 3/2021 do TJSC", 30)) # Estimating 30m or adding as todo

    conn.commit()
    conn.close()
    print(f"Inseridas {len(classes) + 1} aulas de Informática com sucesso.")

if __name__ == '__main__':
    update_db()
