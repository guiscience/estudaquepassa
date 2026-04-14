import sqlite3
import re

DB_PATH = "tjsc_plan.db"

direito_const_raw = """
Princípios Fundamentais 01:02:39
Questões dos Princípios Fundamentais 01:00:34
Teoria Geral dos Direitos e Garantias Fundamentais 01:02:28
Questões de Teoria geral dos direitos fundamentais 00:35:28
Direitos e Deveres Individuais e Coletivos (Art. 5ª): Princípio da Legalidade e Igualdade 00:32:39
Direitos e Deveres Individuais e Coletivos (Art. 5ª): Vedação à Tortura 00:25:24
Direitos e Deveres Individuais e Coletivos (Art. 5ª): Manifestação do Pensamento 00:35:52
Direitos e Deveres Individuais e Coletivos (Art. 5ª): Direito Religioso 01:02:26
Direitos e Deveres Individuais e Coletivos (Art. 5ª): Censura 00:36:32
Direitos e Deveres Individuais e Coletivos (Art. 5ª): Inviolabilidades 01:01:21
Direitos e Deveres Individuais e Coletivos (Art. 5ª): Liberdades de Trabalho, Locomoção e Acesso à Informação 00:30:53
Direitos e Deveres Individuais e Coletivos (Art. 5ª): Direito a Reunião e Associação 00:45:05
Direitos e Deveres Individuais e Coletivos (Art. 5ª): Direito de Propriedade e Herança 00:45:34
Direitos e Deveres Individuais e Coletivos (Art. 5ª): Defesa do Consumidor 00:10:18
Direitos e Deveres Individuais e Coletivos (Art. 5ª): Garantias e Acesso à Justiça 01:00:55
Direitos e Deveres Individuais e Coletivos (Art. 5ª): Júri 00:35:29
Direitos e Deveres Individuais e Coletivos (Art. 5ª): Aspectos Penais e Processuais Penais (Parte I) 00:30:36
Direitos e Deveres Individuais e Coletivos (Art. 5ª): Aspectos Penais e Processuais Penais (Parte II) 00:30:55
Direitos e Deveres Individuais e Coletivos (Art. 5ª): Prisões 00:30:09
Direitos e Deveres Individuais e Coletivos (Art. 5ª): Habeas Corpus, Habeas Data, Mandado de Segurança, Mandado de Injunção e Ação Popular 01:00:20
Direitos e Deveres Individuais e Coletivos (Art. 5ª): Assistência Judiciária Gratuita, Gratuidade das Certidões e Princípio da Celeridade Processual 00:50:32
Direitos e Deveres Individuais e Coletivos (Art. 5ª): Direitos fundamentais e tratados internacionais 00:32:39
Direitos e Deveres Individuais e Coletivos (Art. 5ª): Crimes e Penas 00:30:56
Súmulas - Art. 5º - STF (Parte I) 00:20:36
Súmulas - Art. 5º - STF (Parte II) 00:30:59
Inviolabilidade - Jurisprudências 01:04:55
Questões dos Direitos e Deveres Individuais e Coletivos | Parte I 00:30:06
Questões dos Direitos e Deveres Individuais e Coletivos | Parte II 00:30:47
Questões dos Direitos e Deveres Individuais e Coletivos | Parte III 00:30:26
Questões dos Direitos e Deveres Individuais e Coletivos | Parte IV 00:32:35
Questões dos Direitos e Deveres Individuais e Coletivos | Parte V 00:30:22
Questões dos Direitos e Deveres Individuais e Coletivos | Parte VI 00:30:17
Questões dos Direitos e Deveres Individuais e Coletivos | Parte VII 00:30:48
Direitos Sociais (Art. 6 ) 00:33:47
Direitos Sociais Coletivos dos Trabalhadores (Art. 7 ) 00:43:53
Direitos Sociais: Direitos constitucionais dos trabalhadores (Art. 8 ao 11 ) 00:40:48
Questões dos Direitos Sociais 01:01:23
Nacionalidade - Parte I 01:00:14
Nacionalidade - Parte II 01:06:36
Questões da Nacionalidade 00:35:27
Direitos Políticos 01:01:17
Partidos Políticos 00:59:49
Questões do Partido Políticos 00:25:19
Da organização do Estado: Da organização Político-Administrativa (Art 18 e 19) 00:35:40
Da organização do Estado: Dos Bens União (Art 20) 00:30:30
Da organização do Estado: Da Competência (Art 21 ao 24) | Parte I 00:30:30
Da organização do Estado: Da Competência (Art 21 ao 24) | Parte II 01:03:42
Resumo da organização do Estado: Da Competência 00:30:30
Questões da Organização Político-administrativa 00:31:17
Da organização do Estado: Dos Estados Federados (Art. 25 ao Art. 28) 01:00:06
Questões de Fixação - Estados 00:30:47
Da organização do Estado: Dos Municípios (Art. 29 e Art. 29-A) 01:02:22
Da organização do Estado: Dos Municípios (Art. 30 e Art. 31) 00:35:52
Da organização do Estado: Distrito Federal (Art. 32) 00:33:11
Da organização do Estado: Território (Art. 33) 00:25:10
Administração Pública | Disposições Gerais - Parte I 00:32:49
Administração Pública | Disposições Gerais - Parte II 00:45:28
Administração Pública | Disposições Gerais - Parte III 00:30:40
Administração Pública | Disposições Gerais - Parte IV 00:34:32
Administração Pública | Disposições Gerais - Parte V 01:02:24
Administração Pública | Disposições Gerais - Parte VI 00:34:34
Administração Pública | Disposições Gerais - Parte VII 00:31:20
Administração Pública | Dos Servidores Públicos - Parte I 00:44:57
Administração Pública | Dos Servidores Públicos - Parte II 01:00:53
Administração Pública | Dos Servidores Públicos - Parte III 00:33:24
Questões da Administração Pública - Parte I 00:32:03
Questões da Administração Pública - Parte II 00:35:23
Questões dos Servidores Públicos - Parte I 01:00:48
Questões dos Servidores Públicos - Parte II 00:32:20
Do Poder Judiciário | Disposições gerais - Parte I 01:00:35
Do Poder Judiciary | Disposições Gerais - Parte II 01:35:04
Do Poder Judiciário | Disposições Gerais - Parte III 01:00:50
Do Poder Judiciário | Disposições Gerais - Parte IV 00:25:09
Do Poder Judiciário | Disposições Gerais - Parte V 00:32:59
Do Poder Judiciário | Dos Tribunais Regionais Federais e dos Juízes Federais 01:05:14
Do Poder Judiciário | Do Tribunal Superior do Trabalho, dos Tribunais Regionais do Trabalho e dos Juízes do Trabalho 00:35:08
Do Poder Judiciário | Dos Tribunais e Juízes Eleitorais 01:00:07
Do Poder Judiciário | Dos Tribunais e Juízes Militares 00:20:41
Do Poder Judiciário | Dos Tribunais e Juízes dos Estados 00:32:15
Do Poder Judiciário | CNJ 00:31:47
Do Poder Judiciário | Supremo Tribunal Federal 00:34:46
Do Poder Judiciário | Supremo Tribunal Federal e Do Superior Tribunal de Justiça - Parte I 00:45:51
Do Poder Judiciário | Supremo Tribunal Federal e Do Superior Tribunal de Justiça - Parte II 01:01:08
Funções Essenciais à Justiça - Parte Geral 00:35:45
Funções Essenciais à Justiça - Ministério Público - Parte I 00:35:18
Funções Essenciais à Justiça - Ministério Público - Parte II 00:35:07
Funções Essenciais à Justiça - Ministério Público - Parte III 00:33:01
Funções Essenciais à Justiça - Ministério Público - Parte IV 00:42:23
Funções Essenciais à Justiça - Ministério Público - Parte V 00:30:21
Funções Essenciais à Justiça - Advocacia Pública 00:30:34
Funções Essenciais à Justiça - Advocacia 00:10:06
Funções Essenciais à Justiça - Defensoria Pública 00:38:53
Estrutura do TJSC: órgãos colegiados, varas e câmaras
Conselho Nacional de Justiça (CNJ): composição, competências e aplicação prática no TJSC
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
        ("Noções de Direito Constitutional - Luciano Franco (Técnico)", 2),
    )
    module_id = cursor.lastrowid
    print(f"Criado módulo ID {module_id} para Técnico")

    classes = parse_classes(direito_const_raw)

    for title, duration in classes:
        cursor.execute(
            "INSERT INTO classes (module_id, title, duration_minutes) VALUES (?, ?, ?)",
            (module_id, title, duration),
        )

    conn.commit()
    conn.close()
    print(
        f"Inseridas {len(classes)} aulas de Direito Constitucional Técnico com sucesso."
    )


if __name__ == "__main__":
    update_db()
