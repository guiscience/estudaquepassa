import sqlite3
import re

DB_PATH = 'tjsc_plan.db'

afo_raw = """
Orçamento público: Conceito 00:41:40 Questões de Orçamento público: Conceito inicial - Parte I 00:41:27 Questões de Orçamento público: Conceito inicial - Parte II 00:50:58 Questões de Orçamento público: Conceito inicial - Parte III 00:51:13 Questões de Orçamento público: Conceito inicial - Parte IV 00:37:04 A Constituição e o Sistema Orçamentário Brasileiro - Parte I 00:26:56 A Constituição e o Sistema Orçamentário Brasileiro - Parte II 00:36:20 Questões de a Constituição e o Sistema Orçamentário Brasileiro - Parte I 00:42:25 Questões de a Constituição e o Sistema Orçamentário Brasileiro - Parte II 00:42:03 Questões de a Constituição e o Sistema Orçamentário Brasileiro - Parte III 00:46:11 Questões de a Constituição e o Sistema Orçamentário Brasileiro - Parte IV 00:38:04 Questões de a Constituição e o Sistema Orçamentário Brasileiro - Parte V 00:33:22 Questões de a Constituição e o Sistema Orçamentário Brasileiro - Parte VI 00:34:16 Questões de a Constituição e o Sistema Orçamentário Brasileiro - Parte VII 00:29:27 Questões de a Constituição e o Sistema Orçamentário Brasileiro - Parte VIII 00:41:46 Questões de a Constituição e o Sistema Orçamentário Brasileiro - Parte IX 00:41:46 Técnicas orçamentárias 00:42:58 Princípios orçamentários 00:52:19 Questões de princípios orçamentários - Parte I 00:38:24 Questões de princípios orçamentários - Parte II 00:40:47 Questões de princípios orçamentários - Parte III 00:34:02 Questões de princípios orçamentários - Parte IV 00:44:57 Questões de princípios orçamentários - Parte V 00:36:38 Questões de princípios orçamentários - Parte VI 00:36:48 Questões de princípios orçamentários - Parte VII 00:30:45 Questões de princípios orçamentários - Parte VIII 00:43:29 Questões de princípios orçamentários - Parte IX 00:19:38 Ciclo orçamentário 00:52:12 Questões de Ciclo orçamentário - Parte I 00:40:57 Questões de Ciclo orçamentário - Parte II 00:35:40 Questões de Ciclo orçamentário - Parte III 00:29:05 Questões de Ciclo orçamentário - Parte IV 00:39:09 Questões de Ciclo orçamentário - Parte V 00:26:42 Processo orçamentário 00:42:58 Sistema de planejamento e de orçamento federal 00:43:17 Instrumento de Planejamento e Orçamento: PPA - Plano plurianual 01:05:14 Instrumento de Planejamento e Orçamento: LDO (Lei de Diretrizes Orçamentárias) 00:57:36 Instrumento de Planejamento e Orçamento: LOA (Lei Orçamentária Anual) 01:04:23 Sistema e processo de orçamentação 00:48:31 Classificações orçamentárias 00:33:04 Estrutura programática 00:47:38 Créditos ordinários e Créditos adicionais/Ajustes orçamentários 01:25:50 Questões de Créditos ordinários e Créditos adicionais/Ajustes orçamentários - Parte I 00:27:30 Questões de Créditos ordinários e Créditos adicionais/Ajustes orçamentários - Parte II 00:22:28 Questões de Créditos ordinários e Créditos adicionais/Ajustes orçamentários - Parte III 00:18:10 Questões de Créditos ordinários e Créditos adicionais/Ajustes orçamentários - Parte IV 00:33:22 Questões de Créditos ordinários e Créditos adicionais/Ajustes orçamentários - Parte V 00:36:51 Questões de Créditos ordinários e Créditos adicionais/Ajustes orçamentários - Parte VI 00:42:44 Questões de Créditos ordinários e Créditos adicionais/Ajustes orçamentários - Parte VII 00:28:32 Questões de Créditos ordinários e Créditos adicionais/Ajustes orçamentários - Parte VIII 00:47:55 Receita pública 01:10:46 Receita Pública e suas classificações 00:38:59 Questões de Receita pública - Parte I 00:36:13 Questões de Receita pública - Parte II 00:33:34 Questões de Receita pública - Parte III 00:41:13 Questões de Receita pública - Parte IV 00:22:20 Questões de Receita pública - Parte V 00:35:36 Questões de Receita pública - Parte VI 00:42:04 Questões de Receita pública - Parte VII 00:42:53 Despesa pública 01:25:58 Questões de Despesa pública - Parte I 00:39:52 Questões de Despesa pública - Parte II 00:40:03 Questões de Despesa pública - Parte III 00:39:01 Questões de Despesa pública - Parte IV 00:32:36 Questões de Despesa pública - Parte V 00:33:13 Questões de Despesa pública - Parte VI 00:30:24 Despesas de Exercícios Anteriores 00:29:36 Restos a Pagar 01:06:03 Questões de Restos a Pagar - Parte I 00:38:49 Questões de Restos a Pagar - Parte II 00:35:26 Questões de Restos a Pagar - Parte III 00:36:47 Questões de Restos a Pagar - Parte IV 00:28:13 Regime Fiscal Extraordinário 00:26:52 Suprimento de Fundos 01:07:39 Questões de Suprimento de Fundos - Parte I 00:40:20 Questões de Suprimento de Fundos - Parte II 00:40:24 Questões de Suprimento de Fundos - Parte III 00:27:36 Questões de Suprimento de Fundos - Parte IV 00:34:54 Questões de Suprimento de Fundos - Parte V 00:09:35 Lei Complementar n° 101/2000 - Lei de Responsabilidade Fiscal (LRF) | Parte I 01:01:04 Lei Complementar n° 101/2000 - Lei de Responsabilidade Fiscal (LRF) | Parte II 00:58:02 Lei Complementar n° 101/2000 - Lei de Responsabilidade Fiscal (LRF) | Parte III 00:58:52 Questões de Lei de Responsabilidade Fiscal - Parte I 00:41:36 Questões de Lei de Responsabilidade Fiscal - Parte II 00:17:56 Questões de Lei de Responsabilidade Fiscal - Parte III 00:39:55 Questões de Lei de Responsabilidade Fiscal - Parte IV 00:43:50 Questões de Lei de Responsabilidade Fiscal - Parte V 01:52:28 Lei nº 4.320 de 1964 | Parte I 01:03:41 Lei nº 4.320 de 1964 | Parte II 00:58:22 Lei nº 4.320 de 1964 | Parte III 01:01:02 Questões da Lei nº 4.320 de 1964 01:30:41 Maratona de Questões 01:03:32
"""

def parse_classes(raw_text):
    # Regex to find: Title (including | and spaces) followed by HH:MM:SS
    pattern = r"(.*?)\s+(\d{2}:\d{2}:\d{2})"
    matches = re.findall(pattern, raw_text.strip())
    
    parsed = []
    for title, duration in matches:
        h, m, s = map(int, duration.split(':'))
        total_minutes = (h * 60) + m + (1 if s > 30 else 0) # Round up if > 30s
        parsed.append((title.strip(), total_minutes))
    return parsed

def update_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Clear existing sample data if any (or just add to it)
    # Let's reset the DB to ensure clean state for the real data
    cursor.execute('DELETE FROM classes')
    cursor.execute('DELETE FROM modules')
    
    # Insert AFO Module
    cursor.execute('INSERT INTO modules (name) VALUES (?)', ("AFO - Administração Financeira e Orçamentária",))
    module_id = cursor.lastrowid

    classes = parse_classes(afo_raw)
    
    for title, duration in classes:
        cursor.execute('INSERT INTO classes (module_id, title, duration_minutes) VALUES (?, ?, ?)', 
                       (module_id, title, duration))

    conn.commit()
    conn.close()
    print(f"Inseridas {len(classes)} aulas de AFO com sucesso.")

if __name__ == '__main__':
    update_db()
