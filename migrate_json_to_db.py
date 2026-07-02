"""
migrate_json_to_db.py
======================
Migra TraKU de students.json (almacenamiento plano) a una base de datos
relacional (traku.db, SQLite) usando EXACTAMENTE los campos que existen
hoy en el JSON real del proyecto:

    users{email}: password, role, name, career, semester,
                  risk_level, progress, reminders[], recommendations[],
                  evaluations[], chat_history[]

No se inventan campos que no existen en el JSON actual (ver schema_sqlserver.sql
para el modelo ampliado multi-campus propuesto a futuro).

USO:
    python migrate_json_to_db.py                # lee students.json, crea traku.db
    python migrate_json_to_db.py --dry-run       # solo muestra qué haría
"""
import json
import sqlite3
import sys
import bcrypt
from pathlib import Path

JSON_FILE = "students.json"
DB_FILE = "traku.db"


def is_bcrypt_hash(value: str) -> bool:
    return isinstance(value, str) and value.startswith(("$2a$", "$2b$", "$2y$"))


def hash_if_needed(password: str) -> str:
    if is_bcrypt_hash(password):
        return password
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


SCHEMA = """
CREATE TABLE IF NOT EXISTS Usuarios (
    UsuarioID       INTEGER PRIMARY KEY AUTOINCREMENT,
    Email           TEXT NOT NULL UNIQUE,
    PasswordHash    TEXT NOT NULL,
    Rol             TEXT NOT NULL CHECK (Rol IN ('admin','psicologo','estudiante')),
    Nombre          TEXT NOT NULL,
    Carrera         TEXT,
    Semestre        INTEGER DEFAULT 0,
    NivelRiesgo     TEXT DEFAULT 'Bajo',
    Progreso        INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS Recordatorios (
    RecordatorioID  INTEGER PRIMARY KEY AUTOINCREMENT,
    UsuarioID       INTEGER NOT NULL REFERENCES Usuarios(UsuarioID) ON DELETE CASCADE,
    RecordatorioOrigenID TEXT,
    Icono           TEXT,
    Tarea           TEXT NOT NULL,
    Fecha           TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS Recomendaciones (
    RecomendacionID INTEGER PRIMARY KEY AUTOINCREMENT,
    UsuarioID       INTEGER NOT NULL REFERENCES Usuarios(UsuarioID) ON DELETE CASCADE,
    Icono           TEXT,
    Texto           TEXT NOT NULL,
    Color           TEXT
);

CREATE TABLE IF NOT EXISTS Evaluaciones (
    EvaluacionID    INTEGER PRIMARY KEY AUTOINCREMENT,
    UsuarioID       INTEGER NOT NULL REFERENCES Usuarios(UsuarioID) ON DELETE CASCADE,
    Fecha           TEXT,
    Ausencias       TEXT,
    Motivacion      TEXT,
    Desempeno       TEXT,
    Riesgo          TEXT
);

CREATE TABLE IF NOT EXISTS ChatHistorial (
    MensajeID       INTEGER PRIMARY KEY AUTOINCREMENT,
    UsuarioID       INTEGER NOT NULL REFERENCES Usuarios(UsuarioID) ON DELETE CASCADE,
    Contenido       TEXT NOT NULL,
    Timestamp       TEXT
);
"""


def migrate(dry_run: bool = False):
    if not Path(JSON_FILE).exists():
        print(f"❌ No se encontró {JSON_FILE}")
        sys.exit(1)

    data = json.loads(Path(JSON_FILE).read_text(encoding="utf-8"))
    users = data.get("users", {})
    print(f"📄 {JSON_FILE}: {len(users)} usuarios encontrados")

    if dry_run:
        for email, u in users.items():
            print(f"  - {email} | {u.get('role')} | {u.get('name')}")
        print("Dry-run: no se escribió ninguna base de datos.")
        return

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.executescript(SCHEMA)

    inserted = 0
    for email, u in users.items():
        pw_hash = hash_if_needed(u.get("password", ""))
        cur.execute(
            """INSERT OR REPLACE INTO Usuarios
               (Email, PasswordHash, Rol, Nombre, Carrera, Semestre, NivelRiesgo, Progreso)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                email,
                pw_hash,
                u.get("role", "estudiante"),
                u.get("name", ""),
                u.get("career", ""),
                u.get("semester", 0),
                u.get("risk_level", "Bajo"),
                u.get("progress", 0),
            ),
        )
        usuario_id = cur.lastrowid
        inserted += 1

        for r in u.get("reminders", []):
            cur.execute(
                """INSERT INTO Recordatorios (UsuarioID, RecordatorioOrigenID, Icono, Tarea, Fecha)
                   VALUES (?,?,?,?,?)""",
                (usuario_id, r.get("id"), r.get("icon"), r.get("task"), r.get("date")),
            )

        for rec in u.get("recommendations", []):
            cur.execute(
                """INSERT INTO Recomendaciones (UsuarioID, Icono, Texto, Color)
                   VALUES (?,?,?,?)""",
                (usuario_id, rec.get("icon"), rec.get("text"), rec.get("color")),
            )

        for ev in u.get("evaluations", []):
            cur.execute(
                """INSERT INTO Evaluaciones (UsuarioID, Fecha, Ausencias, Motivacion, Desempeno, Riesgo)
                   VALUES (?,?,?,?,?,?)""",
                (
                    usuario_id,
                    ev.get("date"),
                    ev.get("absences"),
                    ev.get("motivation"),
                    ev.get("performance"),
                    ev.get("risk"),
                ),
            )

        for msg in u.get("chat_history", []):
            # chat_history puede venir como string u objeto {text, timestamp}
            if isinstance(msg, dict):
                contenido = msg.get("text") or msg.get("message") or json.dumps(msg, ensure_ascii=False)
                ts = msg.get("timestamp")
            else:
                contenido, ts = str(msg), None
            cur.execute(
                """INSERT INTO ChatHistorial (UsuarioID, Contenido, Timestamp) VALUES (?,?,?)""",
                (usuario_id, contenido, ts),
            )

    conn.commit()

    cur.execute("SELECT COUNT(*) FROM Usuarios")
    total_usuarios = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM Recordatorios")
    total_recordatorios = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM Recomendaciones")
    total_recs = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM Evaluaciones")
    total_evals = cur.fetchone()[0]
    conn.close()

    print(f"✅ Migración completa → {DB_FILE}")
    print(f"   Usuarios:        {total_usuarios}")
    print(f"   Recordatorios:   {total_recordatorios}")
    print(f"   Recomendaciones: {total_recs}")
    print(f"   Evaluaciones:    {total_evals}")
    print(f"   (todas las contraseñas quedaron en bcrypt, ninguna en texto plano)")


if __name__ == "__main__":
    migrate(dry_run="--dry-run" in sys.argv)
