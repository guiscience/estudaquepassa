import sqlite3
import json
import os

DB_PATH = 'tjsc_plan.db'

def setup_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Adiciona a coluna se ela não existir
    try:
        cursor.execute('ALTER TABLE classes ADD COLUMN video_link TEXT')
        print("Coluna 'video_link' adicionada.")
    except sqlite3.OperationalError:
        print("Coluna 'video_link' já existe.")
    conn.commit()
    conn.close()

def import_scraped_data(json_file):
    if not os.path.exists(json_file):
        print(f"Erro: Arquivo {json_file} não encontrado.")
        return

    with open(json_file, 'r', encoding='utf-8') as f:
        scraped_data = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    count = 0
    for item in scraped_data:
        # Tenta encontrar a aula pelo título (aproximado se necessário)
        # item: { 'subject': '...', 'title': '...', 'idAttr': '...' }
        # idAttr format: subject-XXX-topic-YYY-lesson-ZZZ
        
        # Constrói o link real
        # Pattern: https://lms.focusconcursos.com.br/#/curso/1313054044?subject=...&lesson=...
        parts = item['idAttr'].split('-')
        subj_id = parts[1]
        lesson_id = parts[5]
        link = f"https://lms.focusconcursos.com.br/#/curso/1313054044?subject={subj_id}&lesson={lesson_id}"

        # Update the database
        cursor.execute('''
            UPDATE classes 
            SET video_link = ? 
            WHERE title = ?
        ''', (link, item['title']))
        
        if cursor.rowcount > 0:
            count += 1
    
    conn.commit()
    conn.close()
    print(f"Sincronização concluída: {count} aulas atualizadas com links.")

if __name__ == '__main__':
    setup_db()
