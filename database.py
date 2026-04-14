import sqlite3
import os

DB_PATH = 'tjsc_plan.db'

def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH) # Reset for our initial execution
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''
        CREATE TABLE modules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_id INTEGER,
            title TEXT NOT NULL,
            duration_minutes INTEGER NOT NULL,
            is_completed INTEGER DEFAULT 0,
            FOREIGN KEY (module_id) REFERENCES modules (id)
        )
    ''')

    # Insert sample data (User will provide real Focus classes later)
    modules = [
        ('1', 'Língua Portuguesa'),
        ('2', 'Leis do PJSC'),
        ('3', 'Informática'),
        ('4', 'Direito Constitucional'),
        ('5', 'Direito Administrativo')
    ]
    cursor.executemany('INSERT INTO modules (id, name) VALUES (?, ?)', modules)

    # Example classes (module_id, title, duration)
    classes = [
        (1, 'Interpretação de Texto - Aula 1', 30),
        (1, 'Ortografia Oficial - Aula 2', 45),
        (1, 'Sintaxe - Aula 3', 40),
        (2, 'Estatuto dos Servidores - Aula 1', 60),
        (2, 'Regimento Interno TJSC - Aula 2', 50),
        (3, 'Sistemas Operacionais - Aula 1', 35),
        (4, 'Princípios Fundamentais - Aula 1', 50),
        (4, 'Direitos e Garantias - Aula 2', 60),
        (5, 'Atos Administrativos - Aula 1', 45),
        (5, 'Licitações Nova Lei - Aula 2', 70),
    ]
    cursor.executemany('INSERT INTO classes (module_id, title, duration_minutes) VALUES (?, ?, ?)', classes)

    conn.commit()
    conn.close()
    print("Database initialized successfully with sample data.")

if __name__ == '__main__':
    init_db()
