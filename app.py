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
    generate_schedule_for_user(current_user.id, start_date)
    return jsonify({"success": True, "message": "Cronograma gerado com sucesso!"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
