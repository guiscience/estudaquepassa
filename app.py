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
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
    return conn


# Auto-create database on first run
import sys

if USE_PG:
    import psycopg

    try:
        conn = psycopg.connect(DB_PATH)
        cur = conn.cursor()
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

        cur.execute(
            "INSERT INTO cargos (id, name) VALUES (1, 'Analista') ON CONFLICT DO NOTHING"
        )
        cur.execute(
            "INSERT INTO cargos (id, name) VALUES (2, 'Tecnico') ON CONFLICT DO NOTHING"
        )

        # Shared modules (cargo_id = NULL)
        cur.execute(
            "INSERT INTO modules (name, cargo_id) VALUES ('Informatica e LGPD - Leo Matos', NULL) ON CONFLICT DO NOTHING"
        )
        cur.execute(
            "INSERT INTO modules (name, cargo_id) VALUES ('Transparencia e Controle - LAI', NULL) ON CONFLICT DO NOTHING"
        )
        cur.execute(
            "INSERT INTO modules (name, cargo_id) VALUES ('Etica e Gestao no Servico Publico - Nathan Pilonetto', NULL) ON CONFLICT DO NOTHING"
        )

        # Analista modules
        cur.execute(
            "INSERT INTO modules (name, cargo_id) VALUES ('AFO - Administracao Financeira e Orcamentaria', 1) ON CONFLICT DO NOTHING"
        )
        cur.execute(
            "INSERT INTO modules (name, cargo_id) VALUES ('Portugues - Douglas Wisniewski', 1) ON CONFLICT DO NOTHING"
        )
        cur.execute(
            "INSERT INTO modules (name, cargo_id) VALUES ('Administracao Geral - Fabio de Assis', 1) ON CONFLICT DO NOTHING"
        )
        cur.execute(
            "INSERT INTO modules (name, cargo_id) VALUES ('Gestao de Pessoas - Fabio de Assis', 1) ON CONFLICT DO NOTHING"
        )
        cur.execute(
            "INSERT INTO modules (name, cargo_id) VALUES ('Adm de Materiais e Logistica - Fabio de Assis', 1) ON CONFLICT DO NOTHING"
        )
        cur.execute(
            "INSERT INTO modules (name, cargo_id) VALUES ('Administracao Publica - Fabio de Assis', 1) ON CONFLICT DO NOTHING"
        )

        # Tecnico modules
        cur.execute(
            "INSERT INTO modules (name, cargo_id) VALUES ('Lingua Portuguesa - Janaina Souto (Tecnico)', 2) ON CONFLICT DO NOTHING"
        )
        cur.execute(
            "INSERT INTO modules (name, cargo_id) VALUES ('Direito Civil - Yegor Moreira (Tecnico)', 2) ON CONFLICT DO NOTHING"
        )
        cur.execute(
            "INSERT INTO modules (name, cargo_id) VALUES ('Direito Constitucional (Tecnico)', 2) ON CONFLICT DO NOTHING"
        )
        cur.execute(
            "INSERT INTO modules (name, cargo_id) VALUES ('Direito Penal (Tecnico)', 2) ON CONFLICT DO NOTHING"
        )
        cur.execute(
            "INSERT INTO modules (name, cargo_id) VALUES ('Direito Processual Penal (Tecnico)', 2) ON CONFLICT DO NOTHING"
        )
        cur.execute(
            "INSERT INTO modules (name, cargo_id) VALUES ('Direito Administrativo (Tecnico)', 2) ON CONFLICT DO NOTHING"
        )
        cur.execute(
            "INSERT INTO modules (name, cargo_id) VALUES ('Direito Processual Civil (Tecnico)', 2) ON CONFLICT DO NOTHING"
        )
        cur.execute(
            "INSERT INTO modules (name, cargo_id) VALUES ('Informatica e Protecao de Dados (Tecnico)', 2) ON CONFLICT DO NOTHING"
        )

        conn.commit()
        conn.close()
        print("PostgreSQL database initialized!")
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

    conn = get_db_connection()
    cargos = conn.execute("SELECT * FROM cargos ORDER BY id").fetchall()
    conn.close()

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
