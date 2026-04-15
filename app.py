from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "tjsc2026-chave-secreta-troque-em-producao"

# Database config - PostgreSQL on Railway, SQLite locally
DB_PATH = os.environ.get("DATABASE_URL", "tjsc_plan.db")
USE_PG = os.environ.get("DATABASE_URL") is not None


def get_db_connection():
    if USE_PG:
        import psycopg

        conn = psycopg.connect(DB_PATH)
        # Add execute method that converts ? to %s and returns dict-like rows
        original_execute = conn.execute

        def new_execute(sql, params=()):
            sql = sql.replace("?", "%s")
            cursor = original_execute(sql, params)

            # Make it have fetchone/fetchall methods that return dict-like with numeric access too
            class Result:
                def __init__(self, cursor):
                    self._cursor = cursor
                    self._cols = (
                        [desc[0] for desc in self._cursor.description]
                        if self._cursor.description
                        else []
                    )

                def fetchone(self):
                    row = self._cursor.fetchone()
                    if row is None:
                        return None
                    # Convert to dict that also supports numeric index
                    d = dict(zip(self._cols, row))
                    # Add numeric key access for compatibility
                    for i, v in enumerate(row):
                        d[i] = v
                    return d

                def fetchall(self):
                    rows = self._cursor.fetchall()
                    if not rows:
                        return []
                    result = []
                    for row in rows:
                        d = dict(zip(self._cols, row))
                        for i, v in enumerate(row):
                            d[i] = v
                        result.append(d)
                    return result

            return Result(cursor)

        conn.execute = new_execute
        return conn
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn


# Helper to get cargos list (works with both SQLite and PostgreSQL)
def get_cargos():
    conn = get_db_connection()
    if USE_PG:
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM cargos ORDER BY id")
        cargos = [{"id": r[0], "name": r[1]} for r in cur.fetchall()]
    else:
        cargos = conn.execute("SELECT * FROM cargos ORDER BY id").fetchall()
    conn.close()
    return cargos


# Auto-create database on first run
import sys

if USE_PG:
    import psycopg

    try:
        conn = psycopg.connect(DB_PATH)
        cur = conn.cursor()

        # Drop and recreate tables
        cur.execute("DROP TABLE IF EXISTS user_progress CASCADE")
        cur.execute("DROP TABLE IF EXISTS classes CASCADE")
        cur.execute("DROP TABLE IF EXISTS modules CASCADE")
        cur.execute("DROP TABLE IF EXISTS users CASCADE")
        cur.execute("DROP TABLE IF EXISTS cargos CASCADE")

        cur.execute(
            """CREATE TABLE IF NOT EXISTS modules (id SERIAL PRIMARY KEY, name TEXT, cargo_id INTEGER)"""
        )
        cur.execute(
            """CREATE TABLE IF NOT EXISTS classes (id SERIAL PRIMARY KEY, module_id INTEGER, title TEXT, duration_minutes INTEGER)"""
        )
        cur.execute(
            """CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT, cargo_id INTEGER DEFAULT 1)"""
        )
        cur.execute(
            """CREATE TABLE IF NOT EXISTS user_progress (user_id INTEGER, class_id INTEGER, is_completed INTEGER DEFAULT 0, scheduled_date TEXT, PRIMARY KEY (user_id, class_id))"""
        )
        cur.execute(
            """CREATE TABLE IF NOT EXISTS cargos (id SERIAL PRIMARY KEY, name TEXT)"""
        )

        cur.execute("INSERT INTO cargos (id, name) VALUES (1, 'Analista')")
        cur.execute("INSERT INTO cargos (id, name) VALUES (2, 'Tecnico')")

        # AFO - Analista (92 classes)
        cur.execute(
            "INSERT INTO modules (id, name, cargo_id) VALUES (1, 'AFO - Administracao Financeira e Orcamentaria - Marcelo Adriano', 1)"
        )

        afo_classes = [
            ("Orcamento publica: Conceito", 42),
            ("Questoes de Orcamento publica: Conceito inicial - Parte I", 42),
            ("Questoes de Orcamento publica: Conceito inicial - Parte II", 51),
            ("Questoes de Orcamento publica: Conceito inicial - Parte III", 51),
            ("Questoes de Orcamento publica: Conceito inicial - Parte IV", 37),
            ("A Constituicao e o Sistema Orcamentario Brasileiro - Parte I", 27),
            ("A Constituicao e o Sistema Orcamentario Brasileiro - Parte II", 37),
            (
                "Questoes de a Constituicao e o Sistema Orcamentario Brasileiro - Parte I",
                43,
            ),
            (
                "Questoes de a Constituicao e o Sistema Orcamentario Brasileiro - Parte II",
                42,
            ),
            (
                "Questoes de a Constituicao e o Sistema Orcamentario Brasileiro - Parte III",
                46,
            ),
            (
                "Questoes de a Constituicao e o Sistema Orcamentario Brasileiro - Parte IV",
                38,
            ),
            (
                "Questoes de a Constituicao e o Sistema Orcamentario Brasileiro - Parte V",
                33,
            ),
            (
                "Questoes de a Constituicao e o Sistema Orcamentario Brasileiro - Parte VI",
                34,
            ),
            (
                "Questoes de a Constituicao e o Sistema Orcamentario Brasileiro - Parte VII",
                29,
            ),
            (
                "Questoes de a Constituicao e o Sistema Orcamentario Brasileiro - Parte VIII",
                42,
            ),
            (
                "Questoes de a Constituicao e o Sistema Orcamentario Brasileiro - Parte IX",
                42,
            ),
            ("Tecnicas orcamentarias", 43),
            ("Principios orcamentarios", 53),
            ("Questoes de principios orcamentarios - Parte I", 38),
            ("Questoes de principios orcamentarios - Parte II", 41),
            ("Questoes de principios orcamentarios - Parte III", 34),
            ("Questoes de principios orcamentarios - Parte IV", 45),
            ("Questoes de principios orcamentarios - Parte V", 37),
            ("Questoes de principios orcamentarios - Parte VI", 37),
            ("Questoes de principios orcamentarios - Parte VII", 31),
            ("Questoes de principios orcamentarios - Parte VIII", 44),
            ("Questoes de principios orcamentarios - Parte IX", 20),
            ("Ciclo orcamentario", 52),
            ("Questoes de Ciclo orcamentario - Parte I", 41),
            ("Questoes de Ciclo orcamentario - Parte II", 36),
            ("Questoes de Ciclo orcamentario - Parte III", 29),
            ("Questoes de Ciclo orcamentario - Parte IV", 39),
            ("Questoes de Ciclo orcamentario - Parte V", 27),
            ("Processo orcamentario", 43),
            ("Sistema de planejamento e de orçamento federal", 43),
            ("Instrumento de Planejamento e Orçamento: PPA", 65),
            ("Instrumento de Planejamento e Orçamento: LDO", 58),
            ("Instrumento de Planejamento e Orçamento: LOA", 64),
            ("Sistema e processo de orcamentacao", 49),
            ("Classificacoes orcamentarias", 33),
            ("Estrutura programatica", 48),
            ("Creditos ordinarios e Creditos adicionais", 86),
            ("Questoes de Creditos - Parte I", 28),
            ("Questoes de Creditos - Parte II", 23),
            ("Questoes de Creditos - Parte III", 18),
            ("Questoes de Creditos - Parte IV", 33),
            ("Questoes de Creditos - Parte V", 37),
            ("Questoes de Creditos - Parte VI", 43),
            ("Questoes de Creditos - Parte VII", 29),
            ("Questoes de Creditos - Parte VIII", 48),
            ("Receita publica", 71),
            ("Receita Publica e suas classificacoes", 39),
            ("Questoes de Receita publica - Parte I", 36),
            ("Questoes de Receita publica - Parte II", 34),
            ("Questoes de Receita publica - Parte III", 41),
            ("Questoes de Receita publica - Parte IV", 22),
            ("Questoes de Receita publica - Parte V", 36),
            ("Questoes de Receita publica - Parte VI", 42),
            ("Questoes de Receita publica - Parte VII", 43),
            ("Despesa publica", 86),
            ("Questoes de Despesa publica - Parte I", 40),
            ("Questoes de Despesa publica - Parte II", 40),
            ("Questoes de Despesa publica - Parte III", 39),
            ("Questoes de Despesa publica - Parte IV", 33),
            ("Questoes de Despesa publica - Parte V", 33),
            ("Questoes de Despesa publica - Parte VI", 30),
            ("Despesas de Exercicios Anteriores", 30),
            ("Restos a Pagar", 66),
            ("Questoes de Restos a Pagar - Parte I", 39),
            ("Questoes de Restos a Pagar - Parte II", 35),
            ("Questoes de Restos a Pagar - Parte III", 37),
            ("Questoes de Restos a Pagar - Parte IV", 28),
            ("Regime Fiscal Extraordinario", 27),
            ("Suprimento de Fundos", 68),
            ("Questoes de Suprimento de Fundos - Parte I", 40),
            ("Questoes de Suprimento de Fundos - Parte II", 40),
            ("Questoes de Suprimento de Fundos - Parte III", 28),
            ("Questoes de Suprimento de Fundos - Parte IV", 35),
            ("Questoes de Suprimento de Fundos - Parte V", 10),
            ("Lei Complementar 101/2000 - LRF - Parte I", 61),
            ("Lei Complementar 101/2000 - LRF - Parte II", 58),
            ("Lei Complementar 101/2000 - LRF - Parte III", 59),
            ("Questoes de LRF - Parte I", 42),
            ("Questoes de LRF - Parte II", 18),
            ("Questoes de LRF - Parte III", 40),
            ("Questoes de LRF - Parte IV", 44),
            ("Questoes de LRF - Parte V", 112),
            ("Lei 4.320 de 1964 - Parte I", 64),
            ("Lei 4.320 de 1964 - Parte II", 58),
            ("Lei 4.320 de 1964 - Parte III", 61),
            ("Questoes da Lei 4.320 de 1964", 91),
            ("Maratona de Questoes", 64),
        ]

        for title, dur in afo_classes:
            cur.execute(
                "INSERT INTO classes (module_id, title, duration_minutes) VALUES (1, %s, %s)",
                (title, dur),
            )

        # Portuguese Analista - Douglas Wisniewski (104 classes)
        cur.execute(
            "INSERT INTO modules (id, name, cargo_id) VALUES (2, 'Portugues - Douglas Wisniewski', 1)"
        )

        portuguese_classes = [
            ("Estrutura e Formacao de Palavras - Parte 1", 33),
            ("Estrutura e Formacao de Palavras - Parte 2", 53),
            ("Questoes FGV - Formacao de palavras", 30),
            ("Acentuacao Grafica - Parte 1", 31),
            ("Acentuacao Grafica - Parte 2", 42),
            ("Questoes FGV - Acentuacao grafica", 30),
            ("Ortografia - Parte 1", 43),
            ("Ortografia - Parte 2", 59),
            ("Questoes FGV - Ortografia", 41),
            ("Ortografia Oficial", 16),
            ("Fonetica e Fonologia", 25),
            ("Questoes FGV - Fonetica e Fonologia", 24),
            ("Uso do Hifen", 58),
            ("Questoes FGV - Uso do Hifen", 27),
            ("Classes Gramaticais - Parte 1", 40),
            ("Classes Gramaticais - Parte 2", 26),
            ("Classes Gramaticais - Parte 3", 53),
            ("Classes Gramaticais - Parte 4", 38),
            ("Questoes FGV - Classes Gramaticais", 61),
            ("Interjeicao", 38),
            ("Adverbios", 41),
            ("Questoes FGV - Adverbios", 51),
            ("Verbos - modos verbais", 34),
            ("Verbos - tempos verbais", 29),
            ("Verbos - conjugacao verbal", 20),
            ("Verbos - conjugacao verbal modos", 14),
            ("Verbos - modo imperativo", 32),
            ("Questoes FGV - Verbos", 55),
            ("Vozes Verbais - Parte 1", 33),
            ("Vozes Verbais - Parte 2", 42),
            ("Questoes FGV - Vozes Verbais", 64),
            ("Conjuncões Subordinadas", 52),
            ("Questoes FGV - Conjuncões Subordinadas", 54),
            ("Colocacao Pronominal - Parte 1a", 30),
            ("Colocacao Pronominal - Parte 1b", 42),
            ("Colocacao Pronominal - Parte 2", 32),
            ("Questoes FGV - Colocacao Pronominal", 55),
            ("Pronomes Relativos", 62),
            ("Funcoes do Que", 41),
            ("Questoes FGV - Funcoes do Que e Pronomes Relativos", 40),
            ("Funcoes do Se", 38),
            ("Questoes FGV - Funcoes do Se", 56),
            ("Transitividade Verbal - Parte 1", 46),
            ("Transitividade Verbal - Parte 2", 26),
            ("Questoes FGV - Transitividade Verbal", 39),
            ("Tipos de Sujeito - Parte 1", 33),
            ("Tipos de Sujeito - Parte 2", 36),
            ("Tipos de Sujeito - Parte 3", 21),
            ("Questoes FGV - Tipos de Sujeito e Predicado", 79),
            ("Tipos de Predicado", 40),
            ("Funcoes Sintaticas", 56),
            ("Questoes FGV - Funcoes Sintaticas", 74),
            ("Oracoes Subordinadas - Parte 1", 39),
            ("Oracoes Subordinadas - Parte 2", 35),
            ("Oracoes Subordinadas - Parte 3", 33),
            ("Questoes FGV - Oracoes Subordinadas", 36),
            ("Oracoes Coordenadas", 24),
            ("Questoes FGV - Oracoes Coordenadas", 49),
            ("Concordancia Verbal - Parte 1", 47),
            ("Concordancia Verbal - Parte 2", 66),
            ("Concordancia Verbal - Parte 3", 26),
            ("Questoes FGV - Concordancia Verbal e nominal", 93),
            ("Concordancia Nominal - Parte 1", 31),
            ("Concordancia Nominal - Parte 2", 33),
            ("Concordancia Nominal - Parte 3", 23),
            ("Regencia Verbal e Nominal - Parte 1", 37),
            ("Regencia Verbal e Nominal - Parte 2", 48),
            ("Regencia Verbal e Nominal - Parte 3", 34),
            ("Regencia Verbal e Nominal - Parte 4", 38),
            ("Regencia Verbal e Nominal - Parte 5", 34),
            ("Questoes FGV - Regencia", 73),
            ("Crase - Parte 1", 42),
            ("Crase - Parte 2", 25),
            ("Crase - Parte 3", 29),
            ("Crase - Parte 4", 26),
            ("Crase - Parte 5", 30),
            ("Questoes FGV - Crase", 94),
            ("Pontuacao - Parte 1", 40),
            ("Pontuacao - Parte 2", 44),
            ("Pontuacao - Parte 3", 61),
            ("Questoes FGV - Pontuacao", 58),
            ("Interpretacao e Compreensao de Textos - Parte 1a", 39),
            ("Interpretacao e Compreensao de Textos - Parte 1b", 34),
            ("Interpretacao e Compreensao de Textos - Parte 2", 19),
            ("Questoes FGV - Interpretacao e Compreensao", 132),
            ("Tipologia Textual", 48),
            ("Questoes FGV - Tipologia Textual", 48),
            ("Coesao Textual - Parte 1", 34),
            ("Coesao Textual - Parte 2", 21),
            ("Coesao Textual - Parte 3", 27),
            ("Coesao Textual - Parte 4", 40),
            ("Questoes FGV - Coesao Textual", 78),
            ("Denotacao e Conotacao", 33),
            ("Questoes FGV - Denotacao e Conotacao", 40),
            ("Figuras de Linguagem - Parte 1", 41),
            ("Figuras de Linguagem - Parte 2", 42),
            ("Figuras de Linguagem - Parte 3", 35),
            ("Questoes FGV - Figuras de Linguagem", 61),
            ("Funcoes da Linguagem", 48),
            ("Questoes FGV - Funcoes da Linguagem", 44),
            ("Intertextualidade", 35),
            ("Questoes FGV - Intertextualidade", 48),
            ("Paralelismo Sintatico", 18),
            ("Questoes FGV - Paralelismo Sintatico", 69),
        ]

        for title, dur in portuguese_classes:
            cur.execute(
                "INSERT INTO classes (module_id, title, duration_minutes) VALUES (2, %s, %s)",
                (title, dur),
            )

        # Shared modules - Informatics (Leo Matos)
        cur.execute(
            "INSERT INTO modules (id, name, cargo_id) VALUES (3, 'Informatica e LGPD - Leo Matos', NULL)"
        )

        informatica_classes = [
            ("Hardware - Parte 1", 33),
            ("Hardware - Parte 2", 34),
            ("Hardware - Parte 3", 23),
            ("Hardware - Parte 4", 31),
            ("Hardware - Parte 5", 32),
            ("Hardware - Parte 6", 32),
            ("Software - Parte 1", 22),
            ("Software - Parte 2", 42),
            ("Sistema Operacional Windows - Parte 1", 27),
            ("Sistema Operacional Windows - Parte 2", 36),
            ("Sistema Operacional Windows - Parte 3", 27),
            ("Sistema Operacional Windows - Parte 4", 24),
            ("Redes de Computadores - Parte 1", 23),
            ("Redes de Computadores - Parte 2", 24),
            ("Redes de Computadores - Parte 3", 29),
            ("Redes de Computadores - Parte 4", 52),
            ("Conceitos de Internet e Intranet", 18),
            ("Seguranca da Informacao - Parte 1", 20),
            ("Seguranca da Informacao - Parte 2", 21),
            ("Seguranca da Informacao - Parte 3", 26),
            ("Seguranca da Informacao - Parte 4", 21),
            ("Seguranca da Informacao - Parte 5", 24),
            ("Seguranca da Informacao - Parte 6", 19),
            ("Seguranca da Informacao - Parte 7", 23),
            ("Seguranca da Informacao - Parte 8", 22),
            ("Seguranca da Informacao - Parte 9", 27),
            ("Seguranca da Informacao - Parte 10", 31),
            ("Lei 13.709/2018 - Introducao e Fundamentos", 61),
            ("Lei 13.709/2018 - Requisitos Tratamento Dados", 49),
            ("Lei 13.709/2018 - Direitos do Titular", 41),
            ("Lei 13.709/2018 - Tratamento pelo Poder Publico", 32),
            ("Lei 13.709/2018 - Transferencia Internacional de Dados", 28),
            ("Lei 13.709/2018 - Controlador e Operador", 45),
            ("Resumo - Mapeando a Lei 13.709/2018", 36),
            ("Questoes da Lei 13.709/2018 (LGPD)", 32),
            ("Resolucao TJ 3/2021 do TJSC", 0),
        ]

        for title, dur in informatica_classes:
            cur.execute(
                "INSERT INTO classes (module_id, title, duration_minutes) VALUES (3, %s, %s)",
                (title, dur),
            )

        cur.execute(
            "INSERT INTO modules (id, name, cargo_id) VALUES (4, 'Administracao Geral - Fabio de Assis', 1)"
        )

        adm_geral_classes = [
            ("Teorias Burucratica da Administracao", 38),
            ("Teoria das Relacoes Humanas - Parte I", 30),
            ("Teoria das Relacoes Humanas - Parte II", 33),
            ("Teoria Classica - Parte I", 30),
            ("Teoria Classica - Parte II", 30),
            ("Teoria Classica - Parte III", 21),
            ("Teoria Cientifica - Parte I", 30),
            ("Teoria Cientifica - Parte II", 31),
            ("Teoria Estruturalista - Parte I", 31),
            ("Teoria Estruturalista - Parte II", 31),
            ("Teoria Neoclassica - Parte I", 31),
            ("Teoria Neoclassica - Parte II", 35),
            ("Teoria Neoclassica - Parte III", 30),
            ("Teoria dos Sistemas", 45),
            ("Teoria Comportamental", 55),
            ("Teoria Contingencial - Parte I", 30),
            ("Teoria Contingencial - Parte II", 27),
            ("Funcoes da Administracao - Parte I", 25),
            ("Funcoes da Administracao - Parte II", 32),
            ("Caracteristicas das Organizacoes - Parte I", 31),
            ("Caracteristicas das Organizacoes - Parte II", 35),
            ("Caracteristicas das Organizacoes - Parte III", 41),
            ("Planejamento Estrategico - Parte I", 30),
            ("Planejamento Estrategico - Parte II", 30),
            ("Planejamento Estrategico - Parte III", 27),
            ("Gestao da Qualidade - Parte I", 29),
            ("Gestao da Qualidade - Parte II", 19),
            ("Gestao da Qualidade - Parte III", 37),
            ("Gestao por Projetos - Parte I", 30),
            ("Gestao por Projetos - Parte II", 30),
            ("Gestao por Projetos - Parte III", 33),
            ("Gestao por Projetos - Parte IV", 45),
            ("Ferramentas Gestao Projetos: PERT/CPM", 21),
            ("Ferramentas Gestao Projetos: SCRUM", 20),
            ("Ferramentas Gestao Projetos: Kanban", 18),
            ("Ferramentas Gestao Projetos: Matriz RACI", 0),
        ]

        for title, dur in adm_geral_classes:
            cur.execute(
                "INSERT INTO classes (module_id, title, duration_minutes) VALUES (4, %s, %s)",
                (title, dur),
            )

        cur.execute(
            "INSERT INTO modules (id, name, cargo_id) VALUES (5, 'Gestao de Pessoas - Fabio de Assis', 1)"
        )

        gestao_pessoas_classes = [
            ("Evolucao dos Modelos de Gestao de Pessoas - Parte I", 31),
            ("Evolucao dos Modelos de Gestao de Pessoas - Parte II", 33),
            ("Ciclo de Gestao de Pessoas - Parte I", 34),
            ("Ciclo de Gestao de Pessoas - Parte II", 28),
            ("Ciclo de Gestao de Pessoas - Parte III", 26),
            ("Ciclo de Gestao de Pessoas - Parte IV", 31),
            ("Ciclo de Gestao de Pessoas - Parte V", 31),
            ("Ciclo de Gestao de Pessoas - Parte VI", 32),
            ("Lideranca - Parte I", 32),
            ("Lideranca - Parte II", 32),
            ("Lideranca - Parte III", 36),
            ("Motivacao - Parte I", 36),
            ("Motivacao - Parte II", 25),
            ("Processo Decisorio - Parte I", 30),
            ("Processo Decisorio - Parte II", 30),
            ("Comportamento Organizacional - Parte I", 32),
            ("Comportamento Organizacional - Parte II", 30),
            ("Comunicacao - Parte I", 30),
            ("Comunicacao - Parte II", 38),
            ("Cultura Organizacional - Parte I", 30),
            ("Cultura Organizacional - Parte II", 30),
            ("Cultura Organizacional - Parte III", 31),
            ("Grupos e Equipes - Parte I", 30),
            ("Grupos e Equipes - Parte II", 37),
            ("Desenvolvimento Organizacional - Parte I", 30),
            ("Desenvolvimento Organizacional - Parte II", 0),
        ]

        for title, dur in gestao_pessoas_classes:
            cur.execute(
                "INSERT INTO classes (module_id, title, duration_minutes) VALUES (5, %s, %s)",
                (title, dur),
            )

        cur.execute(
            "INSERT INTO modules (id, name, cargo_id) VALUES (6, 'Adm de Materiais - Fabio de Assis', 1)"
        )

        adm_materiais_classes = [
            ("Conceitos e Classificacao de Materiais", 41),
            ("Gestao Patrimonial", 22),
            ("Recursos Patrimoniais", 13),
            ("Logistica reversa", 10),
            ("Logistica e transformacao digital", 21),
            ("Gerenciamento da Cadeia de Suprimento", 17),
            ("Armazenamento de Materiais", 24),
            ("Administracao de Compras", 21),
            ("Gestao de Estoques", 37),
        ]

        for title, dur in adm_materiais_classes:
            cur.execute(
                "INSERT INTO classes (module_id, title, duration_minutes) VALUES (6, %s, %s)",
                (title, dur),
            )

        cur.execute(
            "INSERT INTO modules (id, name, cargo_id) VALUES (7, 'Administracao Publica - Fabio de Assis', 1)"
        )

        adm_publica_classes = [
            ("Modelos Teoricos da Adm Publica - Burocracia", 50),
            ("Modelos Teoricos da Adm Publica - Gerencialismo", 31),
            ("Modelos Teoricos da Adm Publica - Patrimonialismo", 46),
            ("Historicos e Reformas da Adm Publica no Brasil", 42),
            ("Governanca e gestao publica - Parte I", 30),
            ("Governanca e gestao publica - Parte II", 33),
            ("Governanca Corporativa e Compliance", 35),
            ("Gestao de resultados - Parte I", 30),
            ("Gestao de resultados - Parte II", 27),
        ]

        for title, dur in adm_publica_classes:
            cur.execute(
                "INSERT INTO classes (module_id, title, duration_minutes) VALUES (7, %s, %s)",
                (title, dur),
            )

        cur.execute(
            "INSERT INTO modules (id, name, cargo_id) VALUES (8, 'Transparencia e Controle - LAI', NULL)"
        )

        transparencia_classes = [
            ("Lei de Acesso a Informacao (Lei 12.527/2011) - Parte I", 13),
            ("Lei de Acesso a Informacao (Lei 12.527/2011) - Parte II", 30),
            ("Lei de Acesso a Informacao (Lei 12.527/2011) - Parte III", 21),
            ("Lei de Acesso a Informacao (Lei 12.527/2011) - Parte IV", 26),
            ("Lei de Acesso a Informacao (Lei 12.527/2011) - Parte V", 24),
            ("Lei de Acesso a Informacao (Lei 12.527/2011) - Parte VI", 30),
            ("Lei de Acesso a Informacao (Lei 12.527/2011) - Parte VII", 31),
            ("Lei de Acesso a Informacao (Lei 12.527/2011) - Parte VIII", 10),
            ("Lei de Acesso a Informacao (Lei 12.527/2011) - Parte IX", 26),
            ("Lei de Acesso a Informacao (Lei 12.527/2011) - Parte X", 20),
            ("Lei de Acesso a Informacao (Lei 12.527/2011) - Parte XI", 25),
            ("Lei de Acesso a Informacao (Lei 12.527/2011) - Parte XII", 27),
            ("Questoes da Lei de Acesso a Informacao - Parte I", 31),
            ("Questoes da Lei de Acesso a Informacao - Parte II", 35),
            ("Lei complementar 131/2009", 17),
        ]

        for title, dur in transparencia_classes:
            cur.execute(
                "INSERT INTO classes (module_id, title, duration_minutes) VALUES (8, %s, %s)",
                (title, dur),
            )

        cur.execute(
            "INSERT INTO modules (id, name, cargo_id) VALUES (9, 'Etica e Gestao no Servico Publico - Nathan Pilonetto', NULL)"
        )

        etica_classes = [
            (
                "Principios Expressos: legalidade, impessoalidade, moralidade, publicidade e eficiencia",
                33,
            ),
            ("Principios Implicitos na CF 88 - Parte 1", 33),
            ("Principios Implicitos na CF 88 - Parte 2", 28),
            ("Principios Implicitos na CF 88 - Parte 3", 17),
            ("Questoes de Principios - Parte 1", 26),
            ("Questoes de Principios - Parte 2", 38),
            ("Lei 8.429/1992 - Improbidade Administrativa - Introducao", 40),
            ("Lei 8.429/1992 - Atos de Improbidade", 25),
            ("Lei 8.429/1992 - Atos que Causam Prejuizo ao Erario", 24),
            ("Lei 8.429/1992 - Atentam Contra os Principios da Adm Publica", 27),
            ("Lei 8.429/1992 - Penas", 20),
            ("Lei 8.429/1992 - Processo Administrativo e Judicial", 39),
            ("Lei 8.429/1992 - Disposicoes Penais", 12),
            ("Lei 12.846/13 - Lei Anticorrupcao - Disposicoes Gerais", 20),
            ("Lei 12.846/13 - Atos Lesivos", 18),
            ("Lei 12.846/13 - Responsabilizacao Administrativa", 24),
            ("Lei 12.846/13 - Processo de Responsabilizacao", 24),
            ("Lei 12.846/13 - Acordo de Leniencia", 28),
            ("Lei 12.846/13 - Disposicoes Finais", 16),
            ("Gestao de pessoas e comportamento organizacional", 30),
            ("Trabalho em equipe, comunicacao e atitudes eticas", 30),
            ("Integridade institucional no Poder Judiario", 30),
            ("Resolucao TJ 22/2021 do TJSC", 25),
            ("Deveres e responsabilidades do servidor", 30),
            ("Conduta, sancoes e processos disciplinares", 30),
            ("Nocoes de improbidade administrativa", 30),
        ]

        for title, dur in etica_classes:
            cur.execute(
                "INSERT INTO classes (module_id, title, duration_minutes) VALUES (9, %s, %s)",
                (title, dur),
            )

        # Tecnico modules
        cur.execute(
            "INSERT INTO modules (id, name, cargo_id) VALUES (10, 'Portugues - Janaina Souto (Tecnico)', 2)"
        )

        portuguese_tec_classes = [
            ("Ortografia", 68),
            ("Questoes de Ortografia", 50),
            ("Classes Gramaticais e suas funcoes sintaticas", 62),
            ("Questoes de Classes de Palavras", 21),
            ("Verbos", 69),
            ("Questoes de Verbos", 47),
            ("Termos da oracao", 85),
            ("Concordancia Nominal e Concordancia Verbal - Parte I", 26),
            ("Concordancia Nominal e Concordancia Verbal - Parte II", 8),
            (
                "Questoes comentadas Concordancia Nominal e Concordancia Verbal e termos da oracao",
                54,
            ),
            ("Colocacao Pronominal", 65),
            ("Questoes de Pronomes", 46),
            ("Regencia e Crase", 70),
            ("Questoes de Regencia e Crase", 52),
            ("Vozes Verbais e SE", 72),
            ("Pronomes Relativos e QUE", 68),
            ("Questoes de Funcoes do Que e do Se", 58),
            ("Periodo Composto/Oracoes Coordenadas e Subordinadas", 93),
            ("Questoes de Oracoes Coordenadas e Subordinadas", 49),
            ("Pontuacao", 64),
            ("Questoes de Pontuacao", 60),
            ("Interpretacao de texto", 35),
            ("Contexto, coesao, denotacao, conotacao e intertextualidade", 34),
            ("Dominio da tematica dos paragrafos", 25),
            ("Tipos e generos textuais", 39),
            ("Generos textuais e os tipos de coesao", 29),
            ("Figuras de linguagem - Parte I", 38),
            ("Figuras de linguagem - Parte II", 28),
            ("Funcoes da linguagem, tipos de discurso e variacoes linguisticas", 28),
            ("Questoes de Interpretacao de texto e tipologia textual", 30),
            ("Revisao Final em Questoes FGV - Parte I", 41),
            ("Revisao Final em Questoes FGV - Parte II", 44),
            ("Revisao Final em Questoes FGV - Parte III", 45),
            ("Revisao Final em Questoes FGV - Parte IV", 53),
            ("Revisao Final em Questoes FGV - Parte V", 40),
            ("Revisao Final em Questoes FGV - Parte VI", 35),
            ("Revisao Final em Questoes FGV - Parte VII", 33),
            ("Revisao Final em Questoes FGV - Parte VIII", 44),
            ("Revisao Final em Questoes FGV - Parte IX", 25),
            ("Revisao Final em Questoes FGV - Parte X", 45),
            ("Revisao Final em Questoes FGV - Parte XI", 32),
            ("Revisao Final em Questoes FGV - Parte XII", 36),
            ("Revisao Final em Questoes FGV - Parte XIII", 29),
            ("Revisao Final em Questoes FGV - Parte XIV", 44),
            ("Revisao Final em Questoes FGV - Parte XV", 34),
            ("Revisao Final em Questoes FGV - Parte XVI", 26),
            ("Revisao Final em Questoes FGV - Parte XVII", 45),
            ("Revisao Final em Questoes FGV - Parte XVIII", 37),
            ("Revisao Final em Questoes FGV - Parte XIX", 30),
            ("Revisao Final em Questoes FGV - Parte XX", 43),
        ]

        for title, dur in portuguese_tec_classes:
            cur.execute(
                "INSERT INTO classes (module_id, title, duration_minutes) VALUES (10, %s, %s)",
                (title, dur),
            )
        for i in range(1, 16):
            cur.execute(
                "INSERT INTO classes (module_id, title, duration_minutes) VALUES (10, %s, %s)",
                (f"Portugues Tec Aula {i}", 35),
            )

        cur.execute(
            "INSERT INTO modules (id, name, cargo_id) VALUES (11, 'Direito Civil - Yegor Moreira (Tecnico)', 2)"
        )

        civil_tec_classes = [
            ("LINDB - V vigencia e Revogacao das Leis", 36),
            ("LINDB - Interpretacao e Integracao das Leis", 25),
            ("LINDB - Conflitos das Leis no Tempo e no Espaco", 36),
            ("Questoes - LINDB", 67),
            ("Pessoas naturais: Conceito e Personalidade Juridica", 16),
            ("Pessoas naturais: Capacidade Juridica e Legitimacao", 14),
            ("Pessoas naturais: Incapacidades", 20),
            ("Pessoas naturais: Cessacao da incapacidade", 20),
            ("Pessoas naturais: Extincao da personalidade natural", 23),
            ("Pessoas naturais: Ausencia - Parte 1", 20),
            ("Pessoas naturais: Ausencia - Parte 2", 22),
            ("Pessoas naturais: Nome civil e Estado civil", 18),
            ("Pessoas naturais: Domicilio", 22),
            ("Questoes - Pessoas Naturais", 68),
            ("Pessoas juridicas: Disposicoes Gerais - Teorias", 6),
            ("Pessoas juridicas: Disposicoes Gerais - Classificacao", 10),
            ("Pessoas juridicas: Conceito e Elementos Caracterizadores", 5),
            ("Pessoas juridicas: Constituicao", 10),
            ("Pessoas juridicas: Extincao", 6),
            ("Pessoas juridicas: Associacoes", 20),
            ("Pessoas juridicas: Fundacoes", 24),
            ("Pessoas juridicas: Grupos despersonalizados", 12),
            ("Pessoas juridicas: Desconsideracao da personalidade juridica", 37),
            ("Pessoas juridicas: Responsabilidade da pessoa juridica e dos socios", 3),
            ("Pessoas juridicas: Capacidade e direitos da personalidade - Parte 1", 27),
            ("Pessoas juridicas: Capacidade e direitos da personalidade - Parte 2", 32),
            ("Pessoas juridicas: Sociedades de fato", 10),
            ("Questoes - Personalidade Juridica", 83),
            ("Dos Bens moveis, imoveis, fungiveis e infungiveis", 20),
            ("Dos Bens - Art. 86 ao Art. 103", 32),
            ("Bens Corporeos e incorporeos", 3),
            ("Bens no comercio e fora do comercio", 20),
            ("Questoes - Domicilio e Bens", 55),
            ("Fato juridico", 20),
            ("Negocio juridico: Disposicoes gerais", 20),
            ("Negocio juridico: Classificacao e interpretacao", 32),
            ("Negocio juridico: Elemento do Negocio Juridico", 6),
            ("Negocio juridico: Representacao do Negocio Juridico", 14),
            ("Negocio juridico: Condicao, termo e encargo", 30),
            ("Negocio juridico: Defeitos - Conceito e Erro", 36),
            ("Negocio juridico: Defeitos - Coacao, Lesao e Estado de Perigo", 32),
            ("Negocio juridico: Defeitos - Fraude Contra Credores", 31),
            ("Negocio Juridico: Simulacao", 16),
            ("Negocio juridico: Defeitos - Dolo", 26),
            (
                "Negocio juridico: Existecia, eficacia, validade, invalidade e nulidade",
                29,
            ),
            (
                "Questoes - Atos e Fatos Juridicos e Teoria Geral do Negocio Juridico",
                35,
            ),
            ("Atos juridicos licitos e ilicitos", 24),
            ("Questoes - Atos Ilicitos", 41),
            ("Lei 12.682/2012 e Decreto 8.539/2015", 30),
        ]

        for title, dur in civil_tec_classes:
            cur.execute(
                "INSERT INTO classes (module_id, title, duration_minutes) VALUES (11, %s, %s)",
                (title, dur),
            )

        cur.execute(
            "INSERT INTO modules (id, name, cargo_id) VALUES (12, 'Direito Administrativo - Matheus Carvalho (Tecnico)', 2)"
        )

        adm_tec_classes = [
            (
                "Regime Juridico Administrativo e os Principios da Adm Publica - Parte I",
                30,
            ),
            (
                "Regime Juridico Administrativo e os Principios da Adm Publica - Parte II",
                30,
            ),
            ("Questoes de Principios", 10),
            ("Organizacao da Adm Publica - Parte I", 30),
            ("Organizacao da Adm Publica - Parte II", 30),
            ("Organizacao da Adm Publica - Parte III", 30),
            ("Questoes de Organizacao da Adm Publica", 10),
            ("Agentes Publicos - Parte I", 30),
            ("Agentes Publicos - Parte II", 30),
            ("Agentes Publicos - Parte III", 30),
            ("Agentes Publicos - Parte IV", 30),
            ("Agentes Publicos - Parte V", 30),
            ("Questoes de Agentes Publicos", 10),
            ("Poderes Administrativos - Parte I", 30),
            ("Poderes Administrativos - Parte II", 30),
            ("Questoes de Poderes Administrativos", 10),
            ("Atos Administrativos - Parte I", 30),
            ("Atos Administrativos - Parte II", 30),
            ("Atos Administrativos - Parte III", 30),
            ("Questoes de Atos Administrativos", 10),
            ("Licitacoes e Contratos Administrativos - Parte I", 30),
            ("Licitacoes e Contratos Administrativos - Parte II", 30),
            ("Licitacoes e Contratos Administrativos - Parte III", 30),
            ("Licitacoes e Contratos Administrativos - Parte IV", 30),
            ("Licitacoes e Contratos Administrativos - Parte V", 30),
            ("Questoes de Licitacoes e Contratos Administrativos", 10),
            ("Estrutura administrativa do Poder Judiario de SC", 20),
        ]

        for title, dur in adm_tec_classes:
            cur.execute(
                "INSERT INTO classes (module_id, title, duration_minutes) VALUES (12, %s, %s)",
                (title, dur),
            )

        cur.execute(
            "INSERT INTO modules (id, name, cargo_id) VALUES (13, 'Direito Constitucional - Luciano Franco (Tecnico)', 2)"
        )

        const_tec_classes = [
            ("Principios Fundamentais", 63),
            ("Questoes dos Principios Fundamentais", 61),
            ("Teoria Geral dos Direitos e Garantias Fundamentais", 63),
            ("Questoes de Teoria geral dos direitos fundamentais", 35),
            (
                "Direitos e Deveres Individuais - Principio da Legalidade e Igualdade",
                33,
            ),
            ("Direitos e Deveres Individuais - Vedacao a Tortura", 25),
            ("Direitos e Deveres Individuais - Manifestacao do Pensamento", 36),
            ("Direitos e Deveres Individuais - Direito Religioso", 63),
            ("Direitos e Deveres Individuais - Censura", 36),
            ("Direitos e Deveres Individuais - Inviolabilidades", 61),
            (
                "Direitos e Deveres Individuais - Liberdades de Trabalho, Locomocao e Acesso a Informacao",
                31,
            ),
            ("Direitos e Deveres Individuais - Direito de Reuniao e Associacao", 45),
            ("Direitos e Deveres Individuais - Direito de Propriedade e Heranca", 45),
            ("Direitos e Deveres Individuais - Defesa do Consumidor", 10),
            ("Direitos e Deveres Individuais - Garantias e Acesso a Justica", 61),
            ("Direitos e Deveres Individuais - Juri", 35),
            (
                "Direitos e Deveres Individuais - Aspectos Penais e Processuais Penais - Parte I",
                31,
            ),
            (
                "Direitos e Deveres Individuais - Aspectos Penais e Processuais Penais - Parte II",
                31,
            ),
            ("Direitos e Deveres Individuais - Prisoes", 30),
            (
                "Direitos e Deveres Individuais - Habeas Corpus, Habeas Data, Mandado de Seguranca, Mandado de Injuncao e Acao Popular",
                60,
            ),
            (
                "Direitos e Deveres Individuais - Assistencia Judiciaria Gratuita e Celeridade Processual",
                51,
            ),
            (
                "Direitos e Deveres Individuais - Direitos fundamentais e tratados internacionais",
                33,
            ),
            ("Direitos e Deveres Individuais - Crimes e Penas", 31),
            ("Sumulas - Art. 5º - STF - Parte I", 21),
            ("Sumulas - Art. 5º - STF - Parte II", 31),
            ("Inviolabilidade - Jurisprudencias", 65),
            ("Questoes dos Direitos e Deveres Individuais e Coletivos - Parte I", 30),
            ("Questoes dos Direitos e Deveres Individuais e Coletivos - Parte II", 31),
            ("Questoes dos Direitos e Deveres Individuais e Coletivos - Parte III", 30),
            ("Questoes dos Direitos e Deveres Individuais e Coletivos - Parte IV", 33),
            ("Questoes dos Direitos e Deveres Individuais e Coletivos - Parte V", 30),
            ("Questoes dos Direitos e Deveres Individuais e Coletivos - Parte VI", 30),
            ("Questoes dos Direitos e Deveres Individuais e Coletivos - Parte VII", 31),
            ("Direitos Sociais - Art. 6º", 34),
            ("Direitos Sociais Coletivos dos Trabalhadores - Art. 7º", 44),
            (
                "Direitos Sociais - Direitos constitucionais dos trabalhadores - Art. 8 ao 11",
                41,
            ),
            ("Questoes dos Direitos Sociais", 62),
            ("Nacionalidade - Parte I", 60),
            ("Nacionalidade - Parte II", 67),
            ("Questoes da Nacionalidade", 35),
            ("Direitos Políticos", 61),
            ("Partidos Políticos", 60),
            ("Questoes do Partido Políticos", 25),
            (
                "Organizacao do Estado - Organizacao Politico-Administrativa - Art 18 e 19",
                36,
            ),
            ("Organizacao do Estado - Dos Bens Uniao - Art. 20", 30),
            ("Organizacao do Estado - Da Competencia - Art. 21 ao 24 - Parte I", 31),
            ("Organizacao do Estado - Da Competencia - Art. 21 ao 24 - Parte II", 64),
            ("Resumo da organizacao do Estado - Da Competencia", 30),
            ("Questoes da Organizacao Politico-administrativa", 31),
            ("Organizacao do Estado - Dos Estados Federados - Art. 25 ao Art. 28", 60),
            ("Questoes de Fixacao - Estados", 31),
            ("Organizacao do Estado - Dos Municipios - Art. 29 e Art. 29-A", 62),
            ("Organizacao do Estado - Dos Municipios - Art. 30 e Art. 31", 36),
            ("Organizacao do Estado - Distrito Federal - Art. 32", 33),
            ("Organizacao do Estado - Territorio - Art. 33", 25),
            ("Adm Publica - Disposicoes Gerais - Parte I", 33),
            ("Adm Publica - Disposicoes Gerais - Parte II", 45),
            ("Adm Publica - Disposicoes Gerais - Parte III", 31),
            ("Adm Publica - Disposicoes Gerais - Parte IV", 35),
            ("Adm Publica - Disposicoes Gerais - Parte V", 62),
            ("Adm Publica - Disposicoes Gerais - Parte VI", 35),
            ("Adm Publica - Disposicoes Gerais - Parte VII", 31),
            ("Adm Publica - Dos Servidores Publicos - Parte I", 45),
            ("Adm Publica - Dos Servidores Publicos - Parte II", 61),
            ("Adm Publica - Dos Servidores Publicos - Parte III", 33),
            ("Questoes da Adm Publica - Parte I", 32),
            ("Questoes da Adm Publica - Parte II", 35),
            ("Questoes dos Servidores Publicos - Parte I", 61),
            ("Questoes dos Servidores Publicos - Parte II", 32),
            ("Do Poder Judiario - Disposicoes gerais - Parte I", 61),
            ("Do Poder Judiario - Disposicoes Gerais - Parte II", 95),
            ("Do Poder Judiario - Disposicoes Gerais - Parte III", 61),
            ("Do Poder Judiario - Disposicoes Gerais - Parte IV", 25),
            ("Do Poder Judiario - Disposicoes Gerais - Parte V", 33),
            (
                "Do Poder Judiario - Dos Tribunais Regionais Federais e dos Juizes Federais",
                65,
            ),
            ("Do Poder Judiario - Do TST, TRT e Juizes do Trabalho", 35),
            ("Do Poder Judiario - Dos Tribunais e Juizes Eleitorais", 60),
            ("Do Poder Judiario - Dos Tribunais e Juizes Militares", 21),
            ("Do Poder Judiario - Dos Tribunais e Juizes dos Estados", 32),
            ("Do Poder Judiario - CNJ", 32),
            ("Do Poder Judiario - STF", 35),
            ("Do Poder Judiario - STF e STJ - Parte I", 46),
            ("Do Poder Judiario - STF e STJ - Parte II", 61),
            ("Funcoes Essenciais a Justica - Parte Geral", 36),
            ("Funcoes Essenciais a Justica - Ministerio Publico - Parte I", 35),
            ("Funcoes Essenciais a Justica - Ministerio Publico - Parte II", 35),
            ("Funcoes Essenciais a Justica - Ministerio Publico - Parte III", 33),
            ("Funcoes Essenciais a Justica - Ministerio Publico - Parte IV", 42),
            ("Funcoes Essenciais a Justica - Ministerio Publico - Parte V", 30),
            ("Funcoes Essenciais a Justica - Advocacia Publica", 31),
            ("Funcoes Essenciais a Justica - Advocacia", 10),
            ("Funcoes Essenciais a Justica - Defensoria Publica", 39),
            ("Estrutura do TJSC: orgaos colegiados, varas e camaras", 30),
            (
                "Conselho Nacional de Justica - CNJ: composicao, competencias e aplicacao pratica no TJSC",
                30,
            ),
        ]

        for title, dur in const_tec_classes:
            cur.execute(
                "INSERT INTO classes (module_id, title, duration_minutes) VALUES (13, %s, %s)",
                (title, dur),
            )

        cur.execute(
            "INSERT INTO modules (id, name, cargo_id) VALUES (14, 'Direito Penal - Lucas Henrique Favero (Tecnico)', 2)"
        )

        penal_tec_classes = [
            ("Principios do Direito Penal", 116),
            ("Questoes de Principios", 25),
            (
                "Aplicacao da Lei Penal - Parte 1 - Anterioridade da lei, Lei penal no tempo",
                59,
            ),
            (
                "Aplicacao da Lei Penal - Parte 2 - Tempo do crime, territorialidade e lugar do crime",
                55,
            ),
            (
                "Aplicacao da Lei Penal - Parte 3 - Extraterritorialidade e legislacao especial",
                60,
            ),
            ("Revisao - Lei Esquematizada - Aplicacao da Lei Penal", 34),
            ("Questoes de Aplicacoes da Lei Penal", 36),
            ("Teoria do Crime: O fato tipico e seus elementos - Parte 1", 81),
            ("Teoria do Crime: O fato tipico e seus elementos - Parte 2", 89),
            ("Excludentes de ilicitude; Estado de necessidade; Legitima defesa", 102),
            (
                "Potencial consciencia da ilicitude; Erro de Proibicao; Imputabilidade",
                82,
            ),
            ("Teoria do Erro - Erro de Tipo e suas modalidades", 114),
            ("Revisao - Lei Esquematizada - Teoria do Crime", 33),
            ("Revisao - Lei Esquematizada - Imputabilidade Penal", 8),
            ("Questoes de Teoria do Crime - Parte I", 30),
            ("Questoes de Teoria do Crime - Parte II", 28),
            ("Questoes de Teoria do Crime - Parte III", 65),
            ("Questoes de Teoria do Crime - Parte IV", 60),
            ("Questoes de Teoria do Crime - Parte V", 61),
            ("Questoes de Teoria do Crime - Parte VI", 34),
            ("Questoes de Culpabilidade - Parte I", 25),
            ("Questoes de Culpabilidade - Parte II", 36),
            ("Questoes de Culpabilidade - Parte III", 49),
            ("Crimes contra a pessoa - Parte I", 69),
            ("Crimes contra a pessoa - Parte II", 53),
            ("Crimes contra a pessoa - Parte III", 16),
            ("Crimes contra a pessoa - Parte IV", 51),
            ("Crimes contra a pessoa - Parte V", 79),
            ("Crimes contra a pessoa - Parte VI", 24),
            ("Crimes contra a pessoa - Parte VII", 10),
            ("Questoes de Crimes Contra a Pessoa - Parte I", 63),
            ("Questoes de Crimes Contra a Pessoa - Parte II", 61),
            ("Questoes de Crimes Contra a Pessoa - Parte III", 62),
            ("Questoes de Crimes Contra a Pessoa - Parte IV", 62),
            ("Questoes de Crimes Contra a Pessoa - Parte V", 62),
            ("Questoes de Crimes Contra a Pessoa - Parte VI", 64),
            ("Questoes de Crimes Contra a Pessoa - Parte VII", 53),
            ("Crimes contra o patrimonio - Parte I", 93),
            ("Crimes contra o patrimonio - Parte II", 76),
            ("Crimes contra o patrimonio - Parte III", 4),
            ("Crimes contra a Administracao Publica", 64),
            ("Crimes Contra a Administracao da Justica", 79),
            ("Revisao - Lei Esquematizada - Crimes contra a Admin Publica", 43),
            ("Crimes Hediondos - Lei 8072/1990", 51),
            ("Crimes de abuso de autoridade - Lei 13.869/2019 - Parte I", 66),
            ("Crimes de abuso de autoridade - Lei 13.869/2019 - Parte II", 9),
            ("Estatuto da Crianca e do Adolescente - Dos Crimes - Parte I", 55),
            ("Estatuto da Crianca e do Adolescente - Dos Crimes - Parte II", 57),
            (
                "Estatuto da Crianca e do Adolescente - Da Pratica de Ato Infracional",
                30,
            ),
            ("Estatuto da Crianca e do Adolescente - Atualizacoes", 24),
            ("Competencia das varas criminais do TJSC - Resolucao TJ 35/2025", 30),
        ]

        for title, dur in penal_tec_classes:
            cur.execute(
                "INSERT INTO classes (module_id, title, duration_minutes) VALUES (14, %s, %s)",
                (title, dur),
            )

        cur.execute(
            "INSERT INTO modules (id, name, cargo_id) VALUES (15, 'Direito Processual Penal - Priscilla Fernandes (Tecnico)', 2)"
        )

        proc_penal_tec_classes = [
            ("Principios - Parte I", 53),
            ("Principios - Parte II", 48),
            ("Principios - Parte III", 62),
            ("Principios - Parte IV", 55),
            ("Questoes de Processo Penal - Principios", 66),
            ("Disposicoes Preliminares", 49),
            ("Mapa da Lei - Memorize e Revise", 48),
            ("Questoes de Processo Penal - Disposicoes Preliminares", 44),
            ("Juiz das Garantias", 63),
            ("Mapa da Lei - Memorize e Revise", 58),
            ("Inquerito policial - Parte I", 61),
            ("Inquerito policial - Parte II", 61),
            ("Inquerito policial - Parte III", 67),
            ("Mapa da Lei - Memorize e Revise", 63),
            ("Questoes de Processo Penal - Inquerito Policial", 75),
            ("Acao Penal", 61),
            ("Mapa da Lei - Memorize e Revise", 62),
            ("Questoes de Processo Penal - Acao Penal", 66),
            ("Sujeitos Processuais: Juiz, MP, Acusado, Defensor, Assistentes", 64),
            ("Mapa da Lei - Memorize e Revise", 58),
            ("Citacoes e Intimacoes", 56),
            ("Sentenca - Parte I", 67),
            ("Sentenca - Parte II", 73),
            ("Procedimentos - Processo Comum - Parte I", 63),
            ("Procedimentos - Processo Comum - Parte II", 76),
            ("Procedimentos - Processo Comum - Parte III", 65),
            ("Procedimentos - Processo Comum - Parte IV", 68),
            ("Questoes de Processo Penal - Procedimentos", 47),
            ("Habeas Corpus", 55),
            ("Medidas cautelares diversas da prisao - Parte I", 64),
            ("Medidas cautelares diversas da prisao - Parte II", 37),
            ("Prisao em flagrante - Parte I", 62),
            ("Prisao em flagrante - Parte II", 58),
            ("Prisao em Flagrante - Parte III", 27),
            ("Questoes de Processo Penal - Prisao em flagrante", 66),
            ("Prisao Preventiva - Parte II", 13),
            ("Prisao Preventiva - Parte I", 62),
            ("Questoes de Processo Penal - Prisao preventiva", 64),
            ("Prisao domiciliar", 28),
            ("Questoes de Processo Penal - Prisao domiciliar", 57),
            ("Prisao temporaria", 65),
            ("Questoes de Processo Penal - Prisao temporaria", 60),
            ("Liberdade provisoria", 37),
            ("Das Outras Medidas Cautelares", 67),
        ]

        for title, dur in proc_penal_tec_classes:
            cur.execute(
                "INSERT INTO classes (module_id, title, duration_minutes) VALUES (15, %s, %s)",
                (title, dur),
            )

        cur.execute(
            "INSERT INTO modules (id, name, cargo_id) VALUES (16, 'Direito Processual Civil - Raquel Bueno (Tecnico)', 2)"
        )

        proc_civil_tec_classes = [
            ("Normas Fundamentais do Processo Civil - Parte 1", 31),
            ("Normas Fundamentais do Processo Civil - Parte 2", 31),
            ("Normas Fundamentais do Processo Civil - Parte 3", 32),
            ("Normas Fundamentais do Processo Civil - Parte 4", 32),
            ("Normas Fundamentais do Processo Civil - Parte 5", 37),
            ("Aplicacao das Normas Processuais - Art. 13 ao Art. 15", 15),
            ("Jurisdicao - Parte 1", 32),
            ("Jurisdicao - Parte 2", 33),
            ("Jurisdicao - Parte 3", 31),
            ("Jurisdicao - Parte 4", 35),
            ("Jurisdicao - Parte 5", 31),
            ("Jurisdicao - Parte 6", 44),
            ("Jurisdicao - Parte 7", 35),
            ("Direito de Acao", 32),
            ("Direito de Acao - Teorias Explicativas", 35),
            ("Direito de Acao - Condicoes e Elementos da Acao", 33),
            ("Direito de Acao - Elementos, Condicoes e Classificacao", 33),
            ("Direito de Acao - Classificacao da Acao e Sucessao Processual", 35),
            ("Direito de Acao - Questoes de Fixacao", 12),
            ("Limites da Jurisdicao Nacional - Parte 1", 31),
            ("Limites da Jurisdicao Nacional - Parte 2", 10),
            ("Cooperacao Internacional - Disposicoes Gerais - Art. 26 ao 27", 15),
            ("Cooperacao Internacional - Do Auxilio Direto - Art 28 ao 34", 26),
            ("Cooperacao Internacional - Da Carta Rogatoria - Art. 35 e 36", 11),
            ("Cooperacao Internacional - Disposicoes Comuns - Art. 37 ao 41", 9),
            ("Competencia - Parte 1", 36),
            ("Competencia - Parte 2", 34),
            ("Competencia - Parte 3", 33),
            ("Competencia - Parte 4", 32),
            ("Competencia - Parte 5", 17),
        ]

        for title, dur in proc_civil_tec_classes:
            cur.execute(
                "INSERT INTO classes (module_id, title, duration_minutes) VALUES (16, %s, %s)",
                (title, dur),
            )

        cur.execute(
            "INSERT INTO modules (id, name, cargo_id) VALUES (17, 'Informatica - Leo Matos (Tecnico)', 2)"
        )

        info_tec_classes = [
            ("Hardware - Parte I", 37),
            ("Hardware - Parte II", 30),
            ("Hardware - Parte III", 29),
            ("Hardware - Parte IV", 28),
            ("Hardware - Parte V", 30),
            ("Hardware - Parte VI", 12),
            ("Hardware - Revisao", 16),
            ("Hardware - Questoes - Parte I", 24),
            ("Hardware - Questoes - Parte II", 30),
            ("Software", 26),
            ("Sistema Operacional Windows 11 - Parte I", 72),
            ("Sistema Operacional Windows 11 - Parte II", 96),
            ("Sistema Operacional Windows 11 - Parte III", 73),
            ("Questoes de Sistema Operacional Windows 11", 50),
            ("Internet - Parte I", 55),
            ("Internet - Parte II", 118),
            ("Internet - Parte III", 48),
            ("Questoes - Internet", 60),
            ("Intranet", 43),
            ("Questoes - Intranet", 37),
            ("Busca e Pesquisa", 37),
            ("Questoes - Busca e Pesquisa", 60),
            ("Seguranca da Informacao - Antivirus - Parte I", 28),
            ("Seguranca da Informacao - Firewall - Parte II", 25),
            ("Seguranca da Informacao - BLOCO I - Parte III", 33),
            ("Seguranca da Informacao - BLOCO I - Parte IV", 34),
            ("Seguranca da Informacao - BLOCO I - Parte V", 31),
            ("Seguranca da Informacao - BLOCO I - Parte VI", 34),
            ("Seguranca da Informacao - BLOCO II - Parte I", 32),
            ("Seguranca da Informacao - BLOCO II - Parte II", 30),
            ("Seguranca da Informacao - BLOCO II - Parte III", 30),
            ("Seguranca da Informacao - BLOCO II - Parte IV", 32),
            ("Seguranca da Informacao - Revisao", 17),
            ("Seguranca da Informacao - Questoes: BLOCO I - Parte I", 29),
            ("Seguranca da Informacao - Questoes: BLOCO I - Parte II", 30),
            ("Seguranca da Informacao - Questoes: BLOCO II - Parte I", 29),
            ("Seguranca da Informacao - Questoes: BLOCO II - Parte II", 34),
            ("Lei 13.709/2018 - LGPD - Introducao e Fundamentos", 61),
            ("Lei 13.709/2018 - LGPD - Dos Requisitos para o Tratamento de Dados", 49),
            ("Lei 13.709/2018 - LGPD - Dos Direitos do Titular", 41),
            ("Lei 13.709/2018 - LGPD - Tratamento de Dados pelo Poder Publico", 32),
            ("Lei 13.709/2018 - LGPD - Transferencia Internacional de Dados", 28),
            ("Lei 13.709/2018 - LGPD - Controlador e Operador", 45),
            ("Lei 13.709/2018 - LGPD - RESUMAO - Mapeando a Lei", 36),
            ("Questoes da Lei 13.709/2018 - LGPD", 32),
            ("Resolucao TJ 3/2021 do TJSC", 20),
        ]

        for title, dur in info_tec_classes:
            cur.execute(
                "INSERT INTO classes (module_id, title, duration_minutes) VALUES (17, %s, %s)",
                (title, dur),
            )

        conn.commit()
        conn.close()
        print("PostgreSQL database fully initialized with AFO and all modules!")
    except Exception as e:
        print(f"DB init error: {e}")
        sys.exit(1)

        cur.execute("INSERT INTO cargos (id, name) VALUES (1, 'Analista')")
        cur.execute("INSERT INTO cargos (id, name) VALUES (2, 'Tecnico')")

        # Analista modules (id 1-6)
        modules_data = [
            (1, "AFO - Administracao Financeira e Orcamentaria", 1),
            (2, "Portugues - Douglas Wisniewski", 1),
            (3, "Informatica e LGPD - Leo Matos", None),
            (4, "Administracao Geral - Fabio de Assis", 1),
            (5, "Gestao de Pessoas - Fabio de Assis", 1),
            (6, "Adm de Materiais e Logistica - Fabio de Assis", 1),
            (7, "Administracao Publica - Fabio de Assis", 1),
            (8, "Transparencia e Controle - LAI", None),
            (9, "Etica e Gestao no Servico Publico - Nathan Pilonetto", None),
            # Tecnico modules (id 10-18)
            (10, "Lingua Portuguesa - Janaina Souto (Tecnico)", 2),
            (11, "Direito Civil - Yegor Moreira (Tecnico)", 2),
            (12, "Direito Administrativo (Tecnico)", 2),
            (13, "Direito Constitucional (Tecnico)", 2),
            (14, "Direito Penal (Tecnico)", 2),
            (15, "Direito Processual Penal (Tecnico)", 2),
            (16, "Direito Processual Civil (Tecnico)", 2),
            (17, "Informatica e Protecao de Dados (Tecnico)", 2),
        ]

        for mid, name, cid in modules_data:
            cur.execute(
                "INSERT INTO modules (id, name, cargo_id) VALUES (%s, %s, %s)",
                (mid, name, cid),
            )

        # Add classes for each module from local DB
        # Module 1 - AFO (92 classes)
        afo_classes = [
            ("Orcamento publica: Conceito", 41),
            ("Questoes de Orcamento publica: Conceito inicial - Parte I", 41),
            ("Questoes de Orcamento publica: Conceito inicial - Parte II", 50),
            ("Questoes de Orcamento publica: Conceito inicial - Parte III", 51),
            ("Questoes de Orcamento publica: Conceito inicial - Parte IV", 37),
            ("A Constituicao e o Sistema Orcamentario Brasileiro - Parte I", 26),
            ("A Constituicao e o Sistema Orcamentario Brasileiro - Parte II", 36),
            (
                "Questoes de a Constituicao e o Sistema Orcamentario Brasileiro - Parte I",
                42,
            ),
            (
                "Questoes de a Constituicao e o Sistema Orcamentario Brasileiro - Parte II",
                42,
            ),
            (
                "Questoes de a Constituicao e o Sistema Orcamentario Brasileiro - Parte III",
                46,
            ),
            (
                "Questoes de a Constituicao e o Sistema Orcamentario Brasileiro - Parte IV",
                38,
            ),
            (
                "Questoes de a Constituicao e o Sistema Orcamentario Brasileiro - Parte V",
                33,
            ),
            (
                "Questoes de a Constituicao e o Sistema Orcamentario Brasileiro - Parte VI",
                34,
            ),
            (
                "Questoes de a Constituicao e o Sistema Orcamentario Brasileiro - Parte VII",
                29,
            ),
            (
                "Questoes de a Constituicao e o Sistema Orcamentario Brasileiro - Parte VIII",
                41,
            ),
            (
                "Questoes de a Constituicao e o Sistema Orcamentario Brasileiro - Parte IX",
                41,
            ),
        ]
        for title, dur in afo_classes[:10]:
            cur.execute(
                "INSERT INTO classes (module_id, title, duration_minutes) VALUES (1, %s, %s)",
                (title, dur),
            )

        # Module 2 - Portuguese (104 classes)
        for i in range(1, 11):
            cur.execute(
                "INSERT INTO classes (module_id, title, duration_minutes) VALUES (2, %s, %s)",
                (f"Portugues Aula {i}", 30 + i * 5),
            )

        # Module 3 - Informatics (36 classes)
        for i in range(1, 8):
            cur.execute(
                "INSERT INTO classes (module_id, title, duration_minutes) VALUES (3, %s, %s)",
                (f"Informatica Aula {i}", 30 + i * 5),
            )

        # Module 4 - Adm Geral (36 classes)
        for i in range(1, 8):
            cur.execute(
                "INSERT INTO classes (module_id, title, duration_minutes) VALUES (4, %s, %s)",
                (f"Adm Geral Aula {i}", 30 + i * 5),
            )

        # Module 5 - Gestao Pessoas (26 classes)
        for i in range(1, 6):
            cur.execute(
                "INSERT INTO classes (module_id, title, duration_minutes) VALUES (5, %s, %s)",
                (f"Gestao Pessoas Aula {i}", 35),
            )

        # Module 6 - Adm Materiais (9 classes)
        for i in range(1, 4):
            cur.execute(
                "INSERT INTO classes (module_id, title, duration_minutes) VALUES (6, %s, %s)",
                (f"Adm Materiais Aula {i}", 40),
            )

        # Module 7 - Adm Publica (9 classes)
        for i in range(1, 4):
            cur.execute(
                "INSERT INTO classes (module_id, title, duration_minutes) VALUES (7, %s, %s)",
                (f"Adm Publica Aula {i}", 40),
            )

        # Module 8 - Transparencia (15 classes)
        for i in range(1, 5):
            cur.execute(
                "INSERT INTO classes (module_id, title, duration_minutes) VALUES (8, %s, %s)",
                (f"Transparencia Aula {i}", 35),
            )

        # Module 9 - Etica (37 classes)
        for i in range(1, 8):
            cur.execute(
                "INSERT INTO classes (module_id, title, duration_minutes) VALUES (9, %s, %s)",
                (f"Etica Aula {i}", 35),
            )

        # Tecnico modules
        # Portuguese (50 classes)
        for i in range(1, 11):
            cur.execute(
                "INSERT INTO classes (module_id, title, duration_minutes) VALUES (10, %s, %s)",
                (f"Portugues Tecnico Aula {i}", 30 + i * 3),
            )

        # Civil Law (48 classes)
        for i in range(1, 10):
            cur.execute(
                "INSERT INTO classes (module_id, title, duration_minutes) VALUES (11, %s, %s)",
                (f"Direito Civil Aula {i}", 35),
            )

        # Administrative (26 classes)
        for i in range(1, 6):
            cur.execute(
                "INSERT INTO classes (module_id, title, duration_minutes) VALUES (12, %s, %s)",
                (f"Direito Adm Aula {i}", 40),
            )

        # Constitutional (92 classes)
        for i in range(1, 11):
            cur.execute(
                "INSERT INTO classes (module_id, title, duration_minutes) VALUES (13, %s, %s)",
                (f"Direito Const Aula {i}", 35),
            )

        # Penal (50 classes)
        for i in range(1, 11):
            cur.execute(
                "INSERT INTO classes (module_id, title, duration_minutes) VALUES (14, %s, %s)",
                (f"Direito Penal Aula {i}", 35),
            )

        # Processual Penal (44 classes)
        for i in range(1, 9):
            cur.execute(
                "INSERT INTO classes (module_id, title, duration_minutes) VALUES (15, %s, %s)",
                (f"Proc Penal Aula {i}", 35),
            )

        # Processual Civil (30 classes)
        for i in range(1, 7):
            cur.execute(
                "INSERT INTO classes (module_id, title, duration_minutes) VALUES (16, %s, %s)",
                (f"Proc Civil Aula {i}", 35),
            )

        # Informatics Tech (45 classes)
        for i in range(1, 10):
            cur.execute(
                "INSERT INTO classes (module_id, title, duration_minutes) VALUES (17, %s, %s)",
                (f"Informatica Tech Aula {i}", 30 + i * 2),
            )

        conn.commit()
        conn.close()
        print("PostgreSQL database fully initialized!")
    except Exception as e:
        print(f"DB init error: {e}")
        sys.exit(1)

# ── Flask-Login setup ──────────────────────────────────────────────────────
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Faca login para continuar."
login_manager.login_message_category = "error"


class User(UserMixin):
    def __init__(self, id, username, cargo_id, cargo_name=""):
        self.id = id
        self.username = username
        self.cargo_id = cargo_id  # None-safe; treated as 1 if NULL
        self.cargo_name = cargo_name

    @property
    def effective_cargo_id(self):
        return self.cargo_id if self.cargo_id is not None else 1


@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    row = conn.execute(
        """
        SELECT u.*, c.name AS cargo_name
        FROM users u
        LEFT JOIN cargos c ON u.cargo_id = c.id
        WHERE u.id = ?
    """,
        (user_id,),
    ).fetchone()
    conn.close()
    if row:
        return User(
            row["id"], row["username"], row["cargo_id"], row["cargo_name"] or ""
        )
    return None


# ── Auth routes ────────────────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    cargos = get_cargos()

    if request.method == "POST":
        action = request.form.get("action")
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Preencha todos os campos.", "error")
            return render_template("login.html", cargos=cargos)

        conn = get_db_connection()

        if action == "register":
            cargo_id = int(request.form.get("cargo_id", 1))

            if conn.execute(
                "SELECT id FROM users WHERE username = ?", (username,)
            ).fetchone():
                flash("Nome de usuario ja existe. Escolha outro.", "error")
                conn.close()
                return render_template("login.html", cargos=cargos)

            conn.execute(
                "INSERT INTO users (username, password_hash, cargo_id) VALUES (?, ?, ?)",
                (username, generate_password_hash(password), cargo_id),
            )
            conn.commit()
            row = conn.execute(
                """
                SELECT u.*, c.name AS cargo_name
                FROM users u LEFT JOIN cargos c ON u.cargo_id = c.id
                WHERE u.username = ?
            """,
                (username,),
            ).fetchone()
            conn.close()
            login_user(
                User(
                    row["id"], row["username"], row["cargo_id"], row["cargo_name"] or ""
                )
            )
            flash(f"Bem-vindo(a), {username}! Conta criada.", "success")
            return redirect(url_for("index"))

        else:  # login
            row = conn.execute(
                """
                SELECT u.*, c.name AS cargo_name
                FROM users u LEFT JOIN cargos c ON u.cargo_id = c.id
                WHERE u.username = ?
            """,
                (username,),
            ).fetchone()
            conn.close()
            if row and check_password_hash(row["password_hash"], password):
                login_user(
                    User(
                        row["id"],
                        row["username"],
                        row["cargo_id"],
                        row["cargo_name"] or "",
                    )
                )
                return redirect(url_for("index"))
            flash("Usuario ou senha incorretos.", "error")

    return render_template("login.html", cargos=cargos)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# ── Main routes ────────────────────────────────────────────────────────────
@app.route("/")
@login_required
def index():
    conn = get_db_connection()

    # Módulos do cargo do usuário  +  módulos compartilhados (cargo_id IS NULL)
    modules = conn.execute(
        """
        SELECT * FROM modules
        WHERE cargo_id = ? OR cargo_id IS NULL
        ORDER BY id
    """,
        (current_user.effective_cargo_id,),
    ).fetchall()

    today_str = datetime.now().strftime("%Y-%m-%d")
    today_classes_count = conn.execute(
        """
        SELECT COUNT(*) FROM user_progress
        WHERE user_id = ? AND scheduled_date = ? AND is_completed = 0
    """,
        (current_user.id, today_str),
    ).fetchone()[0]

    study_data = []
    total_minutes = 0
    completed_minutes = 0

    for mod in modules:
        classes = conn.execute(
            """
            SELECT c.*, COALESCE(up.is_completed, 0) AS is_completed
            FROM classes c
            LEFT JOIN user_progress up ON c.id = up.class_id AND up.user_id = ?
            WHERE c.module_id = ?
        """,
            (current_user.id, mod["id"]),
        ).fetchall()

        mod_classes = []
        for c in classes:
            mod_classes.append(dict(c))
            total_minutes += c["duration_minutes"]
            if c["is_completed"]:
                completed_minutes += c["duration_minutes"]

        study_data.append(
            {"id": mod["id"], "name": mod["name"], "classes": mod_classes}
        )

    conn.close()

    return render_template(
        "index.html",
        study_data=study_data,
        total_minutes=total_minutes,
        completed_minutes=completed_minutes,
        today_classes_count=today_classes_count,
        username=current_user.username,
        cargo_name=current_user.cargo_name,
    )


@app.route("/agenda")
@login_required
def agenda():
    date_str = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))

    conn = get_db_connection()
    classes = conn.execute(
        """
        SELECT c.*, m.name AS module_name, COALESCE(up.is_completed, 0) AS is_completed
        FROM classes c
        JOIN modules m        ON c.module_id  = m.id
        JOIN user_progress up ON c.id = up.class_id AND up.user_id = ?
        WHERE up.scheduled_date = ?
    """,
        (current_user.id, date_str),
    ).fetchall()

    day_total = sum(c["duration_minutes"] for c in classes)
    day_done = sum(c["duration_minutes"] for c in classes if c["is_completed"])

    preview_dates = []
    curr = datetime.strptime(date_str, "%Y-%m-%d")
    for i in range(1, 5):
        preview_dates.append((curr + timedelta(days=i)).strftime("%Y-%m-%d"))

    conn.close()

    return render_template(
        "agenda.html",
        classes=classes,
        current_date=date_str,
        day_total=day_total,
        day_done=day_done,
        preview_dates=preview_dates,
        username=current_user.username,
        cargo_name=current_user.cargo_name,
    )


# ── API routes ─────────────────────────────────────────────────────────────
@app.route("/api/toggle_class", methods=["POST"])
@login_required
def toggle_class():
    data = request.get_json()
    class_id = data.get("class_id")
    is_completed = data.get("is_completed")

    if class_id is None or is_completed is None:
        return jsonify({"error": "Invalid data"}), 400

    status_int = 1 if is_completed else 0

    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO user_progress (user_id, class_id, is_completed)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, class_id) DO UPDATE SET is_completed = ?
    """,
        (current_user.id, class_id, status_int, status_int),
    )
    conn.commit()

    # Totais específicos do cargo do usuário (módulos do cargo + compartilhados)
    cid = current_user.effective_cargo_id
    total_minutes = (
        conn.execute(
            """
        SELECT SUM(c.duration_minutes)
        FROM classes c
        JOIN modules m ON c.module_id = m.id
        WHERE m.cargo_id = ? OR m.cargo_id IS NULL
    """,
            (cid,),
        ).fetchone()[0]
        or 0
    )

    completed_minutes = (
        conn.execute(
            """
        SELECT SUM(c.duration_minutes)
        FROM classes c
        JOIN modules m        ON c.module_id = m.id
        JOIN user_progress up ON c.id = up.class_id
        WHERE up.user_id = ? AND up.is_completed = 1
          AND (m.cargo_id = ? OR m.cargo_id IS NULL)
    """,
            (current_user.id, cid),
        ).fetchone()[0]
        or 0
    )

    conn.close()

    return jsonify(
        {
            "success": True,
            "total_minutes": total_minutes,
            "completed_minutes": completed_minutes,
        }
    )


@app.route("/api/generate_schedule", methods=["POST"])
@login_required
def generate_schedule_route():
    """Gera/regenera o cronograma apenas para o usuario logado."""
    from generate_schedule import generate_schedule_for_user

    start_date = datetime.now().strftime("%Y-%m-%d")
    cargo_id = current_user.effective_cargo_id
    days = generate_schedule_for_user(current_user.id, start_date, cargo_id)
    return jsonify({"success": True, "message": f"Cronograma gerado ({days} dias)!"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
