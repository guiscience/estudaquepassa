import sqlite3
import re

DB_PATH = "tjsc_plan.db"

direito_penal_raw = """
Princípios do Direito Penal 01:55:44
Questões de Princípios 00:24:29
Aplicação da Lei Penal - Parte 1 (Art. 1 ao Art. 3) | Anterioridade da lei, Lei penal no tempo e lei excepcional ou temporária 00:58:05
Aplicação da Lei Penal - Parte 2 (Art. 4 ao Art. Art. 6) | Tempo do crime, territorialidade e lugar do crime 00:54:45
Aplicação da Lei Penal - Parte 3 (Art. 7 ao Art. 12) | Extraterritorialidade, eficácia de sentença estrangeira, contagem de prazo, frações não computáveis da pena e legislação especial 00:59:31
Revisão - Lei Esquematizada - Aplicação da Lei Penal 00:33:20
Questões de Aplicações da Lei Penal 00:35:12
Teoria do Crime: O fato típico e seus elementos | Parte 1 01:20:20
Teoria do Crime: O fato típico e seus elementos | Parte 2 01:28:19
Excludentes de ilicitude; Estado de necessidade; Legítima defesa; Estrito cumprimento do dever legal; Exercicio regular do direito 01:41:36
Potencial consciência da ilicitude; Erro de Proibição; Exigibilidade de conduta diversa; Da Imputabilidade 01:21:29
Teoria do Erro - Erro de Tipo e suas modalidades 01:34:02
Revisão - Lei Esquematizada - Teoria do Crime 00:32:49
Revisão - Lei Esquematizada - Imputabilidade Penal 00:08:11
Questões de Teoria do Crime | Parte I 00:29:17
Questões de Teoria do Crime | Parte II 00:27:24
Questões de Teoria do Crime | Parte III 01:04:40
Questões de Teoria do Crime | Parte IV 00:59:39
Questões de Teoria do Crime | Parte V 01:00:13
Questões de Teoria do Crime | Parte VI 00:34:03
Questões de Culpabilidade | Parte I 00:24:32
Questões de Culpabilidade | Parte II 00:35:12
Questões de Culpabilidade | Parte III 00:48:14
Crimes contra a pessoa - Parte I 01:08:28
Crimes contra a pessoa - Parte II 00:52:41
Crimes contra a pessoa - Parte III 00:16:19
Crimes contra a pessoa - Parte IV 00:50:42
Crimes contra a pessoa - Parte V 01:18:32
Crimes contra a pessoa - Parte VI 00:23:56
Crimes contra a pessoa - Parte VII 00:09:32
Questões de Crimes Contra a Pessoa | Parte I 01:03:02
Questões de Crimes Contra a Pessoa | Parte II 01:00:32
Questões de Crimes Contra a Pessoa | Parte III 01:01:14
Questões de Crimes Contra a Pessoa | Parte IV 01:01:01
Questões de Crimes Contra a Pessoa | Parte V 01:01:06
Questões de Crimes Contra a Pessoa | Parte VI 01:03:45
Questões de Crimes Contra a Pessoa | Parte VII 00:52:48
Crimes contra o patrimônio | Parte I 01:32:45
Crimes contra o patrimônio - Parte II 01:15:20
Crimes contra o patrimônio - Parte III 00:04:24
Crimes contra a Administração Pública 01:03:30
Crimes Contra a Administração da Justiça 01:18:35
Revisão - Lei Esquematizada - Crimes contra a Administração Pública 00:42:28
Crimes Hediondos (Lei nº 8072/1990) 00:50:28
Crimes de abuso de autoridade (Lei nº 13.869/2019) - Parte I 01:05:44
Crimes de abuso de autoridade (Lei nº 13.869/2019) - Parte II 00:08:37
Estatuto da Criança e do Adolescente (Lei nº 8.069/90) | Dos Crimes - Parte I 00:54:15
Estatuto da Criança e do Adolescente (Lei nº 8.069/90) | Dos Crimes - Parte II 00:56:29
Estatuto da Criança e do Adolescente (Lei nº 8.069/90) | Da Prática de Ato Infracional 00:30:05
Estatuto da Criança e do Adolescente (Lei nº 8.069/90) | Aula complementar (Atualizações) 00:24:09
Competência das varas criminais do TJSC (Resolução TJ n. 35/2025, que especifica as competências de todas as unidades judiciárias).
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

    # Delete old module 17 (old Direito Penal)
    cursor.execute("DELETE FROM classes WHERE module_id = 17")
    cursor.execute("DELETE FROM modules WHERE id = 17")
    print("Removido módulo 17 antigo")

    cursor.execute(
        "INSERT INTO modules (name, cargo_id) VALUES (?, ?)",
        ("Noções de Direito Penal - Lucas Henrique Fávero (Técnico)", 2),
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
