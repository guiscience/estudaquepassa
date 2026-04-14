import sqlite3
import re

DB_PATH = "tjsc_plan.db"

direito_civil_raw = """
Lei de Introdução às Normas do Direito Brasileiro - LINDB - Vigência e Revogação das Leis 00:35:46
Lei de Introdução às Normas do Direito Brasileiro - LINDB - Interpretação e Integração das Leis 00:25:07
Lei de Introdução às Normas do Direito Brasileiro - LINDB - Conflitos das Leis no Tempo e no Espaço 00:35:46
Questões | Lei de introdução às normas do Direito brasileiro 01:06:37
Pessoas naturais: Conceito e Personalidade Jurídica 00:15:37
Pessoas naturais: Capacidade Jurídica e Legitimação 00:13:53
Pessoas naturais: Incapacidades 00:20:21
Pessoas naturais: Cessação da incapacidade 00:20:24
Pessoas naturais: Extinção da personalidade natural 00:23:01
Pessoas naturais: Ausência | Parte 1 00:19:44
Pessoas naturais: Ausência | Parte 2 00:22:02
Pessoas naturais: Nome civil e Estado civil 00:18:26
Pessoas naturais: Domicílio 00:22:24
Questões | Pessoas Naturais 01:07:58
Pessoas jurídicas: Disposições Gerais - Teorias 00:06:16
Pessoas jurídicas: Disposições Gerais - Classificação 00:09:55
Pessoas jurídicas: Conceito e Elementos Caracterizadores 00:05:19
Pessoas jurídicas: Constituição 00:09:53
Pessoas jurídicas: Extinção 00:06:16
Pessoas jurídicas: Associações 00:19:48
Pessoas jurídicas: Fundações 00:24:06
Pessoas jurídicas: Grupos despersonalizadoss 00:12:11
Pessoas jurídicas: Desconsideração da personalidade jurídica 00:37:16
Pessoas jurídicas: Responsabilidade da pessoa jurídica e dos sócios 00:02:59
Pessoas jurídicas: Capacidade e direitos da personalidade - Parte 1 00:27:15
Pessoas jurídicas: Capacidade e direitos da personalidade - Parte 2 00:31:54
Pessoas jurídicas: Sociedades de fato 00:10:25
Questões | Personalidade Jurídica 01:22:59
Dos Bens móveis, imóveis, fungíveis e infungíveis 00:20:04
Dos Bens | Art. 86 ao Art. 103 00:31:44
Bens Corpóreos e incorpóreos 00:03:01
Bens no comércio e fora do comércio 00:19:34
Questões | Domicínio e Bens 00:54:31
Fato jurídico 00:19:34
Negócio jurídico: Disposições gerais 00:19:33
Negócio jurídico: Classificação e interpretação 00:32:12
Negócio jurídico: Elemento do Negócio Jurídico 00:05:40
Negócio jurídico: Representação do Negócio Jurídico 00:14:22
Negócio jurídico: Condição, termo e encargo 00:30:02
Negócio jurídico: Defeitos do negócio jurídico - Conceito e Erro 00:36:24
Negócio jurídico: Defeitos do negócio jurídico - Coação, Lesão e Estado de Perigo 00:32:16
Negócio jurídico: Defeitos do negócio jurídico - Fraude Contra Credores 00:31:05
Negócio Jurídico: Simulação 00:16:08
Negócio jurídico: Defeitos do negócio jurídico - Dolo 00:26:25
Negócio jurídico: Existência, eficácia, validade, invalidade e nulidade do negócio jurídico 00:28:54
Questões | Atos e Fatos Jurídicos e Teoria Geral do Negócio Jurídico 01:34:19
Atos jurídicos lícitos e ilícitos 00:24:07
Questões | Atos Ilícitos 00:41:23
Lei nº 12.682/2012 (dispõe sobre a elaboração e o arquivamento de documentos em meios eletromagnéticos) 
Decreto Federal n. 8.539/2015 (o uso do meio eletrônico para a realização do processo administrativo no âmbito dos órgãos e das entidades da administração pública federal direta)
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
        ("Noções de Direito Civil - Yegor Moreira Junior (Técnico)", 2),
    )
    module_id = cursor.lastrowid
    print(f"Criado módulo ID {module_id} para Técnico")

    classes = parse_classes(direito_civil_raw)

    for title, duration in classes:
        cursor.execute(
            "INSERT INTO classes (module_id, title, duration_minutes) VALUES (?, ?, ?)",
            (module_id, title, duration),
        )

    conn.commit()
    conn.close()
    print(f"Inseridas {len(classes)} aulas de Direito Civil Técnico com sucesso.")


if __name__ == "__main__":
    update_db()
