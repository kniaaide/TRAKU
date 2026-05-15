# Tu código local

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import json, datetime, os

app = Flask(__name__)
CORS(app)

DB_FILE = "students.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    default = {
        "users": {
            "admin@traku.edu": {
                "password": "admin123",
                "role": "admin",
                "name": "Administrador TraKU",
                "career": "Administración del Sistema",
                "semester": 0
            },
            "psicologa@traku.edu": {
                "password": "psico123",
                "role": "psicologo",
                "name": "Dra. Martínez",
                "career": "Orientación Universitaria",
                "semester": 0
            },
            "karime@universidad.edu": {
                "password": "1234",
                "role": "estudiante",
                "name": "Karime",
                "career": "Ing. en Gestión Empresarial",
                "semester": 6,
                "risk_level": "Medio",
                "progress": 75,
                "reminders": [
                    {"id": "r1", "icon": "📋", "task": "Entregar reporte de química", "date": "2026-04-25"},
                    {"id": "r2", "icon": "📐", "task": "Examen de matemáticas", "date": "2026-04-28"}
                ],
                "recommendations": [
                    {"icon": "📚", "text": "Estudia al menos 1 hora al día esta semana.", "color": "#2563eb"},
                    {"icon": "🧘", "text": "Practica ejercicios de respiración y relajación.", "color": "#16a34a"},
                    {"icon": "🗓️", "text": "Agenda una tutoría con un asesor.", "color": "#d97706"}
                ],
                "evaluations": []
            }
        }
    }
    save_db(default)
    return default

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

db = load_db()

chat_responses = {
    "estres": "Entiendo cómo te sientes. El estrés académico es muy común. ¿Quieres que te ayude a organizar tus tareas o prefieres hablar sobre cómo te sientes?",
    "tareas": "Puedo ayudarte a organizar tus tareas. ¿Cuántas materias tienes pendientes? Te ayudo a crear un plan de estudio.",
    "examen": "Los exámenes pueden ser estresantes. ¿De qué materia necesitas prepararte? Puedo orientarte con recursos y técnicas de estudio.",
    "ayuda": "Estoy aquí para apoyarte. Puedo ayudarte con organización académica, apoyo emocional, recordatorios o conectarte con un tutor.",
    "triste": "Lamento que te sientas así. Tu bienestar es muy importante. ¿Te gustaría hablar con un consejero?",
    "motivacion": "¡Tú puedes! Recuerda por qué empezaste esta carrera. Cada pequeño avance cuenta.",
    "faltas": "Las inasistencias pueden afectar tu rendimiento. Puedo ayudarte a ponerte al día.",
    "desmotivado": "Es normal sentirse así a veces. ¿Quieres hablar sobre lo que te está pasando?",
    "default": "Estoy aquí para apoyarte en tu camino académico. ¿Quieres que te ayude con tus tareas, hablemos sobre cómo te sientes, o prefieres contactar a un tutor?"
}

def get_ai_response(message):
    ml = message.lower()
    for k, v in chat_responses.items():
        if k in ml:
            return v
    return chat_responses["default"]

def get_students():
    return {e: u for e, u in db["users"].items() if u.get("role") == "estudiante"}

def check_tomorrow_reminders(user):
    """Return reminders due tomorrow"""
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    alerts = []
    for r in user.get("reminders", []):
        if r.get("date") == tomorrow:
            alerts.append(r)
    return alerts

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register():
    global db
    data = request.json
    name = data.get('name','').strip()
    email = data.get('email','').strip().lower()
    password = data.get('password','')
    career = data.get('career','').strip()
    semester = int(data.get('semester', 1))
    role = data.get('role', 'estudiante')

    if not name or not email or not password or not career:
        return jsonify({"success": False, "message": "Todos los campos son obligatorios"})
    if email in db["users"]:
        return jsonify({"success": False, "message": "Este correo ya está registrado"})
    if len(password) < 4:
        return jsonify({"success": False, "message": "La contraseña debe tener al menos 4 caracteres"})
    if role not in ["estudiante", "psicologo", "admin"]:
        role = "estudiante"

    new_user = {
        "password": password, "role": role, "name": name,
        "career": career, "semester": semester
    }
    if role == "estudiante":
        new_user.update({
            "risk_level": "Bajo", "progress": 0,
            "reminders": [], "recommendations": [
                {"icon": "🎉", "text": "¡Bienvenido/a a TraKU! Completa tu evaluación inicial.", "color": "#2563eb"},
                {"icon": "📚", "text": "Explora los recursos académicos disponibles.", "color": "#16a34a"},
            ],
            "evaluations": []
        })

    db["users"][email] = new_user
    save_db(db)
    user = db["users"][email].copy()
    user.pop('password')
    return jsonify({"success": True, "user": user})

@app.route('/api/login', methods=['POST'])
def login():
    global db
    db = load_db()
    data = request.json
    email = data.get('email','').strip().lower()
    password = data.get('password','')

    if email in db["users"] and db["users"][email]['password'] == password:
        user = db["users"][email].copy()
        user.pop('password')
        # Check tomorrow alerts for students
        if user.get("role") == "estudiante":
            user["tomorrow_alerts"] = check_tomorrow_reminders(db["users"][email])
        return jsonify({"success": True, "user": user})
    return jsonify({"success": False, "message": "Correo o contraseña incorrectos"})

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message','')
    return jsonify({"response": get_ai_response(message), "timestamp": datetime.datetime.now().strftime("%H:%M")})

@app.route('/api/evaluate', methods=['POST'])
def evaluate():
    global db
    db = load_db()
    data = request.json
    email = data.get('email','')
    absences = data.get('absences','No')
    motivation = data.get('motivation','Mucho')
    performance = data.get('performance','Alto')

    risk = "Bajo"
    recs = []
    if absences == 'Si':
        risk = "Medio"
        recs.append({"icon": "📅", "text": "Retoma la asistencia a clases esta semana.", "color": "#d97706"})
    if motivation == 'Poco':
        if risk == "Bajo": risk = "Medio"
        recs.append({"icon": "🎯", "text": "Establece metas pequeñas y alcanzables diariamente.", "color": "#2563eb"})
    if motivation == 'Nada':
        risk = "Alto"
        recs.append({"icon": "💙", "text": "Agenda una sesión con el consejero estudiantil.", "color": "#dc2626"})
    if performance == 'Bajo':
        risk = "Alto"
        recs.append({"icon": "📚", "text": "Solicita una tutoría de emergencia esta semana.", "color": "#dc2626"})
    if not recs:
        recs = [
            {"icon": "✅", "text": "¡Vas muy bien! Mantén tu ritmo de estudio actual.", "color": "#16a34a"},
            {"icon": "🌟", "text": "Considera participar en grupos de estudio.", "color": "#2563eb"},
        ]

    # Save evaluation to student record
    if email and email in db["users"]:
        eval_record = {
            "date": datetime.date.today().isoformat(),
            "absences": absences, "motivation": motivation,
            "performance": performance, "risk": risk
        }
        db["users"][email].setdefault("evaluations", []).append(eval_record)
        db["users"][email]["risk_level"] = risk
        db["users"][email]["recommendations"] = recs
        save_db(db)

    return jsonify({"risk": risk, "recommendations": recs})

# ── CALENDAR / REMINDERS ──────────────────────────────────────────
@app.route('/api/reminders', methods=['GET'])
def get_reminders():
    db2 = load_db()
    email = request.args.get('email','')
    if email not in db2["users"]:
        return jsonify({"reminders": []})
    reminders = db2["users"][email].get("reminders", [])
    today = datetime.date.today().isoformat()
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    for r in reminders:
        r["is_today"] = r.get("date") == today
        r["is_tomorrow"] = r.get("date") == tomorrow
        r["is_overdue"] = r.get("date","") < today
    return jsonify({"reminders": reminders})

@app.route('/api/reminders/add', methods=['POST'])
def add_reminder():
    global db
    db = load_db()
    data = request.json
    email = data.get('email','')
    task = data.get('task','').strip()
    date = data.get('date','')
    icon = data.get('icon','📋')

    if not task or not date or email not in db["users"]:
        return jsonify({"success": False, "message": "Datos inválidos"})

    rid = f"r{datetime.datetime.now().timestamp()}"
    reminder = {"id": rid, "icon": icon, "task": task, "date": date}
    db["users"][email].setdefault("reminders", []).append(reminder)
    save_db(db)
    return jsonify({"success": True, "reminder": reminder})

@app.route('/api/reminders/delete', methods=['POST'])
def delete_reminder():
    global db
    db = load_db()
    data = request.json
    email = data.get('email','')
    rid = data.get('id','')
    if email in db["users"]:
        db["users"][email]["reminders"] = [
            r for r in db["users"][email].get("reminders",[]) if r["id"] != rid
        ]
        save_db(db)
    return jsonify({"success": True})

# ── ADMIN / PSICOLOGO ROUTES ──────────────────────────────────────
@app.route('/api/admin/students', methods=['GET'])
def admin_students():
    students = get_students()
    result = []
    for email, s in students.items():
        result.append({
            "email": email, "name": s["name"], "career": s["career"],
            "semester": s["semester"], "risk_level": s.get("risk_level","Bajo"),
            "progress": s.get("progress", 0),
            "evaluations_count": len(s.get("evaluations",[])),
            "reminders_count": len(s.get("reminders",[]))
        })
    return jsonify({"students": result})

@app.route('/api/admin/stats', methods=['GET'])
def admin_stats():
    students = get_students()
    total = len(students)
    risk_counts = {"Bajo": 0, "Medio": 0, "Alto": 0}
    for s in students.values():
        r = s.get("risk_level","Bajo")
        risk_counts[r] = risk_counts.get(r, 0) + 1

    all_users = db["users"]
    psicologos = sum(1 for u in all_users.values() if u.get("role") == "psicologo")

    return jsonify({
        "total_students": total,
        "risk_counts": risk_counts,
        "total_psicologos": psicologos,
        "total_users": len(all_users)
    })

@app.route('/api/admin/delete_user', methods=['POST'])
def delete_user():
    global db
    db = load_db()
    data = request.json
    email = data.get('email','')
    if email in db["users"] and db["users"][email].get("role") != "admin":
        del db["users"][email]
        save_db(db)
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "No se puede eliminar"})

@app.route('/api/psico/alerts', methods=['GET'])
def psico_alerts():
    students = get_students()
    alerts = []
    today = datetime.date.today().isoformat()
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

    for email, s in students.items():
        # Risk alerts
        if s.get("risk_level") in ["Medio","Alto"]:
            alerts.append({
                "type": "risk", "student": s["name"], "email": email,
                "career": s["career"], "semester": s["semester"],
                "risk": s.get("risk_level"), "message": f"Nivel de riesgo {s.get('risk_level')}"
            })
        # Tomorrow reminder alerts
        for r in s.get("reminders",[]):
            if r.get("date") == tomorrow:
                alerts.append({
                    "type": "reminder", "student": s["name"], "email": email,
                    "message": f"Tarea vence mañana: {r['task']}"
                })

    return jsonify({"alerts": alerts})

if __name__ == '__main__':
    app.run(debug=True, port=5000)