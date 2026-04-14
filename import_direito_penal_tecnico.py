import sqlite3
import re

DB_PATH = "tjsc_plan.db"

direito_penal_raw = """
Princípios do Direito Penal 00:24:43
Crime: Conceito, Tipicidade e Typicidade Concreta 00:18:57
Crime: Tipicidade formal e material 00:30:30
Crime: Tipicidade objetiva e subjetiva 00:29:01
Crime: Diferença entre Crime e Contravenção 00:08:48
Crime: Crime Doloso e Culposo 00:35:03
Crime: Crime Preterdoloso 00:08:52
Crime: Consumação e tentativa 00:33:26
Crime: concurso de crimes 00:40:34
Crime: Punibilidade e causas de extinção da punibilidade 00:19:06
Questões - Teoria Geral do Crime 01:10:04
Teoria da imputation - Imputação Penal Objetiva 00:40:26
Teoria da imputação - Dolo e Culpa 00:31:53
Teoria da imputação - erro de tipo e erro de proibição 00:24:27
Teoria da imputação - iter criminis 00:10:02
Teoria da imputação -desistência voluntária e arrependimento eficaz 00:19:54
Teoria da imputação -arrependimento posterior 00:23:26
Teoria da imputação -crime impossível 00:19:53
Teoria da imputação -crime fortuito 00:10:17
Questões - Teoria da Imputação 01:01:19
Concausalidade 00:37:18
Concurso de pessoas 00:29:34
Questões de Concurso de Pessoas 00:43:02
Extinção da punibilidade - Conceito 00:17:53
Extinção da punibilidade - Morte do agente 00:09:27
Extinção da punibilidade - Anistia, Graça e Indulto 00:25:19
Extinção da punibilidade - Prescrição 00:36:37
Extinção da punibilidade - decadência e perempção 00:14:01
Questões de Extinção da Punibilidade 00:52:46
Contravenções Penais 00:34:11
Crimes hediondos e equiparados 00:22:27
Lei de Drogas - Crimes 00:36:04
Lei de Drogas - Procedimento 00:16:19
Lei de Drogas - Competência 00:04:35
Lei de Drogas - Sanções Penais 00:16:20
Lei 9.613/1998 (Lavagem de dinheiro) - Crimes 00:20:35
Lei 9.613/1998 (Lavagem de dinheiro) - Elementossubjectivos e objeto material 00:10:08
Lei 9.613/1998 (Lavagem de dinheiro) - Competência e Juizado Especial 00:18:16
Crimes Ambientais - Lei 9.605/1998 - Crimes contra a fauna 00:17:39
Crimes Ambientais - Lei 9.605/1998 - Crimes contra a flora 00:25:35
Crimes Ambientais - Lei 9.605/1998 - Crimes de poluição 00:12:53
Crimes Ambientais - Competência e ação penal 00:20:34
Questões de Crimes Especiais 00:39:02
Direito Penal do Enem 00:35:32
"""


def parse_classes(raw_text):
    pattern = r"(.*?)\s+(\d{1,2}:\d{2}:\d{2})"
    matches = re.findall(pattern, raw_text.strip())

    parsed = []
    for title, duration in matches:
        parts = list(map(int, duration.split(":")))
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

    cursor.execute(
        "INSERT INTO modules (name, cargo_id) VALUES (?, ?)",
        ("Noções de Direito Penal (Técnico)", 2),
    )
    module_id = cursor.lastrowid
    print(f"Criado módulo ID {module_id} para Técnico")

    classes = parse_classes(direito_penal_raw)

    for title, duration in classes:
        cursor.execute(
            "INSERT INTO classes (module_id, title, duration_minutes) VALUES (?, ?, ?)",
            (module_id, title, duration),
        )

    conn.commit()
    conn.close()
    print(f"Inseridas {len(classes)} aulas de Direito Penal Técnico com sucesso.")


if __name__ == "__main__":
    update_db()
