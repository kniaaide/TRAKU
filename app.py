from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
import json, datetime, os, bcrypt

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)
DB_FILE = "students.json"

# ── SEGURIDAD: HASH DE CONTRASEÑAS (bcrypt) ────────────────────────
# 🚨 FIX CRÍTICO: antes las contraseñas se guardaban en texto plano
# (ej. "password": "1234"). Ahora se guardan como hash bcrypt.
def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def is_bcrypt_hash(value: str) -> bool:
    return isinstance(value, str) and value.startswith(("$2a$", "$2b$", "$2y$"))

def check_password(plain_password: str, stored_password: str) -> bool:
    if is_bcrypt_hash(stored_password):
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), stored_password.encode("utf-8"))
        except ValueError:
            return False
    # Compatibilidad con contraseñas antiguas en texto plano
    return plain_password == stored_password

def migrate_plaintext_passwords(data: dict) -> bool:
    """Recorre todos los usuarios y convierte cualquier password en texto
    plano a hash bcrypt. Devuelve True si modificó algo (para guardar)."""
    changed = False
    for user in data.get("users", {}).values():
        pw = user.get("password", "")
        if pw and not is_bcrypt_hash(pw):
            user["password"] = hash_password(pw)
            changed = True
    return changed

# ── DATABASE ──────────────────────────────────────────────────────
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if migrate_plaintext_passwords(data):
            save_db(data)
            print("🔒 Contraseñas en texto plano migradas a bcrypt en", DB_FILE)
        return data
    default = {
        "users": {
            "admin@traku.edu": {
                "password": "admin123", "role": "admin",
                "name": "Administrador TraKU", "career": "Administración", "semester": 0
            },
            "psicologa@traku.edu": {
                "password": "psico123", "role": "psicologo",
                "name": "Dra. Martínez", "career": "Orientación Universitaria", "semester": 0
            },
            "karime@universidad.edu": {
                "password": "1234", "role": "estudiante",
                "name": "Karime", "career": "Ing. en Gestión Empresarial", "semester": 6,
                "risk_level": "Medio", "progress": 75,
                "reminders": [
                    {"id": "r1", "icon": "📋", "task": "Entregar reporte de química", "date": "2026-04-25"},
                    {"id": "r2", "icon": "📐", "task": "Examen de matemáticas", "date": "2026-04-28"}
                ],
                "recommendations": [
                    {"icon": "📚", "text": "Estudia al menos 1 hora al día esta semana.", "color": "#2563eb"},
                    {"icon": "🧘", "text": "Practica ejercicios de respiración y relajación.", "color": "#16a34a"},
                    {"icon": "🗓️", "text": "Agenda una tutoría con un asesor.", "color": "#d97706"}
                ],
                "evaluations": [],
                "chat_history": []
            }
        }
    }
    save_db(default)
    return default

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

db = load_db()

# ── CUESTIONARIO COMPLETO ─────────────────────────────────────────
QUESTIONS = [
    # Académicas
    {"id": 1,  "cat": "academico",   "text": "¿Te cuesta concentrarte en clases o tareas?"},
    {"id": 2,  "cat": "academico",   "text": "¿Sientes que tus calificaciones han bajado recientemente?"},
    {"id": 3,  "cat": "academico",   "text": "¿Entregas tareas tarde o incompletas?"},
    {"id": 4,  "cat": "academico",   "text": "¿Te sientes desmotivado para estudiar?"},
    {"id": 5,  "cat": "academico",   "text": "¿Te resulta difícil organizar tus actividades escolares?"},
    {"id": 6,  "cat": "academico",   "text": "¿Sientes presión excesiva por el rendimiento escolar?"},
    {"id": 7,  "cat": "academico",   "text": "¿Has faltado a clases por falta de ganas o motivación?"},
    # Emocional
    {"id": 8,  "cat": "emocional",   "text": "¿Sientes estrés constante relacionado con la escuela?"},
    {"id": 9,  "cat": "emocional",   "text": "¿Te sientes triste o sin ánimo frecuentemente?"},
    {"id": 10, "cat": "emocional",   "text": "¿Te enojas fácilmente últimamente?"},
    {"id": 11, "cat": "emocional",   "text": "¿Sientes ansiedad o nervios constantemente?"},
    {"id": 12, "cat": "emocional",   "text": "¿Te cuesta dormir por preocupaciones?"},
    {"id": 13, "cat": "emocional",   "text": "¿Sientes que nadie te entiende?"},
    {"id": 14, "cat": "emocional",   "text": "¿Has perdido interés en actividades que antes disfrutabas?"},
    {"id": 15, "cat": "emocional",   "text": "¿Te sientes emocionalmente agotado?"},
    {"id": 16, "cat": "emocional",   "text": "¿Te cuesta expresar cómo te sientes?"},
    # Social
    {"id": 17, "cat": "social",      "text": "¿Sientes apoyo por parte de tu familia?"},
    {"id": 18, "cat": "social",      "text": "¿Te llevas bien con tus compañeros?"},
    {"id": 19, "cat": "social",      "text": "¿Has sufrido burlas, rechazo o ciberacoso?"},
    {"id": 20, "cat": "social",      "text": "¿Tienes alguien de confianza con quien hablar?"},
    {"id": 21, "cat": "social",      "text": "¿Te sientes solo la mayor parte del tiempo?"},
    {"id": 22, "cat": "social",      "text": "¿Los problemas familiares afectan tu desempeño escolar?"},
    # Hábitos
    {"id": 23, "cat": "habitos",     "text": "¿Duermes menos de lo necesario?"},
    {"id": 24, "cat": "habitos",     "text": "¿Pasas demasiado tiempo en redes sociales o videojuegos?"},
    {"id": 25, "cat": "habitos",     "text": "¿Sientes cansancio físico o mental constantemente?"},
    {"id": 26, "cat": "habitos",     "text": "¿Consideras que tienes hábitos saludables?"},
    {"id": 27, "cat": "habitos",     "text": "¿Tienes tiempo suficiente para descansar o relajarte?"},
    {"id": 28, "cat": "habitos",     "text": "¿Realizas actividades físicas o recreativas?"},
    # Abierta
    {"id": 29, "cat": "abierta",     "text": "¿Qué es lo que más te preocupa actualmente?"},
    {"id": 30, "cat": "abierta",     "text": "¿Qué crees que podría ayudarte a mejorar emocional o académicamente?"},
]

# Respuestas empáticas para cada pregunta según sí/no
Q_RESPONSES = {
    1:  {"si": "Entiendo, la concentración puede verse afectada por muchas cosas. Te recomiendo técnicas como Pomodoro: estudia 25 minutos y descansa 5. ¿Quieres que te explique cómo hacerlo?",
         "no": "¡Qué bien! Mantener la concentración es clave para el éxito académico. Sigue así. 💪"},
    2:  {"si": "Las calificaciones a veces bajan por estrés, falta de organización o problemas personales. Podemos trabajar juntos en un plan de estudio. ¿Te gustaría?",
         "no": "¡Excelente! Mantener buenas calificaciones requiere esfuerzo constante. ¡Sigue adelante! 🌟"},
    3:  {"si": "Entregar tarde puede acumularse y generar más estrés. Te ayudo a organizar tus entregas con un calendario. ¿Quieres empezar?",
         "no": "¡Muy bien! Ser puntual con las tareas es una gran habilidad. 👍"},
    4:  {"si": "La desmotivación es una señal importante. Puede ser temporal o indicar algo más profundo. Cuéntame, ¿hace cuánto tiempo te sientes así?",
         "no": "¡Eso es genial! La motivación es el motor del aprendizaje. ¿Qué es lo que más te motiva de tu carrera?"},
    5:  {"si": "Organizar el tiempo académico puede ser difícil. Te puedo ayudar a crear un horario semanal personalizado. ¿Quieres intentarlo?",
         "no": "¡Qué buena habilidad! La organización es fundamental para el éxito universitario."},
    6:  {"si": "La presión académica excesiva puede afectar tu salud mental. Es importante aprender a manejarla. Te recomiendo hablar con un orientador. ¿Te gustaría contactar uno?",
         "no": "¡Perfecto! Mantener un equilibrio sano con las exigencias académicas es muy importante."},
    7:  {"si": "Faltar por desmotivación es una señal de alerta. ¿Sabes qué está causando esa falta de ganas? Podemos buscar soluciones juntos.",
         "no": "¡Muy bien! La asistencia regular es clave para no perder el hilo de los temas."},
    8:  {"si": "El estrés crónico puede afectar tanto tu rendimiento como tu salud. Practica al menos 10 minutos de respiración profunda al día. ¿Quieres que te enseñe técnicas?",
         "no": "¡Qué alivio escuchar eso! Mantener el estrés bajo control te ayudará a rendir mejor."},
    9:  {"si": "Sentirse triste constantemente es algo que merece atención. No estás solo/a. ¿Has podido hablar con alguien de confianza sobre cómo te sientes?",
         "no": "¡Me alegra mucho! El bienestar emocional es la base de todo lo demás."},
    10: {"si": "El enojo frecuente puede ser señal de frustración acumulada o estrés. ¿Hay algo específico que lo esté provocando?",
         "no": "¡Excelente! Mantener la calma en situaciones difíciles es una fortaleza."},
    11: {"si": "La ansiedad constante es muy agotadora. Existen técnicas muy efectivas para manejarla. Te recomiendo buscar apoyo profesional. ¿Quieres que te ayude a agendar una cita?",
         "no": "¡Muy bien! Vivir sin ansiedad constante te permite aprovechar mejor cada día."},
    12: {"si": "Dormir mal por preocupaciones afecta directamente tu concentración y estado de ánimo. Intenta desconectarte de pantallas 1 hora antes de dormir. ¿Te ayudo con más tips?",
         "no": "¡Qué bueno! El sueño reparador es esencial para el aprendizaje y la memoria."},
    13: {"si": "Sentir que nadie te entiende puede ser muy doloroso. Pero aquí estoy yo para escucharte. ¿Quieres contarme qué está pasando?",
         "no": "¡Eso es muy valioso! Sentirse comprendido/a hace toda la diferencia en los momentos difíciles."},
    14: {"si": "Perder interés en lo que antes disfrutabas puede ser una señal de agotamiento emocional. Es importante no ignorar esta señal. ¿Quieres hablar más sobre esto?",
         "no": "¡Qué bien! Mantener intereses y hobbies es muy importante para el equilibrio emocional."},
    15: {"si": "El agotamiento emocional es real y válido. Necesitas espacios de descanso y recuperación. ¿Cuándo fue la última vez que hiciste algo solo para ti?",
         "no": "¡Excelente! Cuidar tu energía emocional es tan importante como tu salud física."},
    16: {"si": "Expresar emociones puede ser difícil. Está bien ir a tu ritmo. Escribir en un diario o hablar con alguien de confianza puede ayudar mucho.",
         "no": "¡Eso es una fortaleza! Poder expresar cómo te sientes te ayuda a procesar mejor las situaciones."},
    17: {"si": "¡Qué afortunado/a de tener ese apoyo! La familia puede ser un gran pilar en los momentos difíciles.",
         "no": "No sentir apoyo familiar puede ser muy difícil. Recuerda que también puedes encontrar apoyo en amigos, profesores o consejeros. No estás solo/a."},
    18: {"si": "¡Excelente! Las buenas relaciones con compañeros hacen la vida universitaria mucho más agradable y productiva.",
         "no": "Las relaciones sociales difíciles pueden afectar tu bienestar. ¿Quieres hablar sobre lo que está pasando con tus compañeros?"},
    19: {"si": "El acoso en cualquier forma es inaceptable y no debes enfrentarlo solo/a. Te recomiendo reportarlo a las autoridades de tu institución. ¿Necesitas orientación sobre cómo hacerlo?",
         "no": "¡Me alegra mucho! Vivir libre de acoso es un derecho de todos los estudiantes."},
    20: {"si": "¡Qué valioso es tener esa persona! Las redes de apoyo son fundamentales en momentos difíciles.",
         "no": "No tener a alguien de confianza puede sentirse muy solitario. Recuerda que yo estoy aquí, y también puedes acudir a los orientadores de tu institución."},
    21: {"si": "La soledad universitaria es más común de lo que crees. ¿Has intentado unirte a grupos o clubes en tu institución? Puedo ayudarte a encontrar opciones.",
         "no": "¡Qué bien! Las conexiones sociales son muy importantes para el bienestar."},
    22: {"si": "Los problemas familiares pueden ser muy pesados de cargar solos. ¿Has considerado hablar con un orientador para que te apoye en esta situación?",
         "no": "¡Me alegra que tu entorno familiar no afecte tu rendimiento! Eso es un gran punto a favor."},
    23: {"si": "Dormir menos de lo necesario afecta la memoria, la concentración y el ánimo. Intenta acostarte a la misma hora cada día. ¿Quieres consejos para mejorar tu sueño?",
         "no": "¡Perfecto! El sueño adecuado es uno de los pilares más importantes del rendimiento académico."},
    24: {"si": "El uso excesivo de pantallas puede afectar el sueño y la concentración. ¿Has intentado poner límites de tiempo en tus apps?",
         "no": "¡Muy bien! Tener un uso equilibrado de la tecnología es muy saludable."},
    25: {"si": "El cansancio constante puede ser señal de que necesitas un descanso real. ¿Cuándo fue la última vez que descansaste sin culpa?",
         "no": "¡Genial! Tener energía constante indica que estás cuidando bien tu cuerpo y mente."},
    26: {"si": "¡Excelente! Los hábitos saludables son la base del rendimiento académico y el bienestar personal.",
         "no": "No te preocupes, los hábitos se pueden cambiar paso a paso. ¿Por dónde te gustaría empezar: sueño, alimentación o ejercicio?"},
    27: {"si": "¡Qué bien! El descanso no es perder el tiempo, es recargar energías para rendir mejor.",
         "no": "Sin tiempo para descansar, el agotamiento llega rápido. ¿Podemos buscar juntos espacios en tu horario para el descanso?"},
    28: {"si": "¡Excelente! La actividad física libera endorfinas que mejoran el ánimo y reducen el estrés.",
         "no": "El movimiento físico, aunque sea una caminata de 15 minutos, puede hacer una gran diferencia en tu bienestar. ¿Te animas a intentarlo?"},
    29: {"open": "Gracias por compartir eso conmigo. Lo que sientes es completamente válido. ¿Hay algo específico en lo que pueda ayudarte con eso ahora mismo?"},
    30: {"open": "Qué reflexión tan importante. Tú conoces mejor que nadie lo que necesitas. TraKU está aquí para apoyarte en ese camino. ¿Quieres que trabajemos juntos en eso?"},
}

# Respuestas para palabras clave del chat libre
KEYWORD_RESPONSES = {
    "concentra":    "La falta de concentración puede tener muchas causas. Intenta la técnica Pomodoro: 25 min de estudio, 5 de descanso. También revisa si estás durmiendo bien. ¿Quieres que iniciemos el cuestionario completo para entender mejor tu situación?",
    "calificacion": "Las calificaciones bajas pueden deberse a estrés, falta de organización o problemas personales. ¿Quieres que hagamos juntos un plan de estudio personalizado?",
    "tarea":        "Organizarte con las tareas es clave. Te recomiendo el calendario de TraKU para registrar fechas límite. ¿Quieres que te muestre cómo usarlo?",
    "desmotiva":    "La desmotivación es una señal importante que no debes ignorar. Cuéntame, ¿desde cuándo te sientes así? Estoy aquí para escucharte.",
    "organiz":      "Organizar el tiempo académico puede ser un reto. ¿Quieres que creemos juntos un horario semanal personalizado?",
    "presion":      "La presión académica excesiva puede afectar tu salud mental. Recuerda que tu bienestar es más importante que cualquier calificación.",
    "faltas":       "Las inasistencias pueden afectar tu rendimiento. ¿Hay alguna razón específica por la que estás faltando? Podemos buscar soluciones juntos.",
    "estres":       "El estrés es una respuesta natural, pero cuando es constante necesita atención. Practica respiración profunda: inhala 4 seg, sostén 4, exhala 4. ¿Quieres más técnicas?",
    "triste":       "Sentirse triste es completamente válido. No tienes que cargarlo solo/a. ¿Quieres contarme qué está pasando? Estoy aquí para escucharte sin juzgarte.",
    "enojo":        "El enojo frecuente puede ser señal de frustración acumulada. ¿Hay algo específico que lo esté provocando? Hablar de ello puede ayudar.",
    "ansiedad":     "La ansiedad puede ser muy agotadora. Existen técnicas muy efectivas: respiración, mindfulness, ejercicio. ¿Te gustaría que te contactemos con un orientador?",
    "dormir":       "El sueño es fundamental para el aprendizaje. Intenta acostarte a la misma hora, evita pantallas 1 hora antes y haz algo relajante antes de dormir.",
    "solo":         "Sentirse solo/a en la universidad es más común de lo que parece. Pero no estás solo/a aquí. ¿Has pensado en unirte a algún grupo o club de tu institución?",
    "familia":      "Los problemas familiares pueden ser muy pesados. ¿Has considerado hablar con un orientador para que te apoye? No tienes que enfrentarlo solo/a.",
    "acoso":        "El acoso es inaceptable. Mereces estar en un ambiente seguro. Te recomiendo reportarlo a las autoridades de tu institución. ¿Quieres orientación sobre cómo hacerlo?",
    "cansado":      "El cansancio constante puede ser señal de agotamiento. ¿Cuándo fue la última vez que descansaste de verdad? Tu cuerpo y mente necesitan recuperarse.",
    "habitos":      "Los hábitos saludables son la base del éxito académico y personal. ¿Por cuál quieres empezar: sueño, alimentación, ejercicio u organización?",
    "ejercicio":    "¡Excelente idea! El ejercicio libera endorfinas que mejoran el ánimo y reducen el estrés. Aunque sea una caminata de 15 minutos al día, marca la diferencia.",
    "ayuda":        "Estoy aquí para apoyarte. Puedo ayudarte con organización académica, apoyo emocional, recordatorios o conectarte con un orientador. ¿Por dónde quieres empezar?",
    "tutor":        "Conectarte con un tutor es una excelente decisión. Puedo ayudarte a agendar una sesión. ¿De qué materia necesitas apoyo?",
    "psicologo":    "Hablar con un psicólogo o orientador puede ser muy beneficioso. No es señal de debilidad, al contrario, es valentía. ¿Quieres que te ayude a contactar uno?",
    "suicid":       "Lo que me dices es muy serio y me importa mucho tu bienestar. Por favor habla con alguien de confianza ahora mismo o llama a una línea de crisis. No estás solo/a. ¿Puedo ayudarte a contactar apoyo profesional de inmediato?",
    "morir":        "Escucho que estás pasando por algo muy difícil. Tu vida tiene un valor enorme. Por favor busca apoyo ahora: habla con alguien de confianza o contacta a un orientador. ¿Quieres que te ayude?",
    "cuestionario": "¡Claro! Voy a hacerte 30 preguntas para entender mejor cómo te sientes académica y emocionalmente. Responde con Sí o No, o cuéntame con tus palabras. ¿Empezamos?",
    "preguntas":    "Puedo hacerte un cuestionario de bienestar con 30 preguntas sobre tu situación académica, emocional, social y de hábitos. ¿Quieres empezar?",
    "default":      "Entiendo. Estoy aquí para apoyarte en tu camino universitario. Puedes contarme cómo te sientes, hacer el cuestionario de bienestar, o pedirme ayuda con tus tareas y organización. ¿Qué necesitas?"
}

def get_ai_response(message, chat_state=None):
    ml = message.lower().strip()

    # Check if we're in questionnaire mode
    if chat_state and chat_state.get("mode") == "questionnaire":
        return handle_questionnaire(message, chat_state)

    # Trigger questionnaire
    if any(w in ml for w in ["cuestionario", "preguntas", "evalua", "test", "empezar cuestionario"]):
        return {
            "text": "¡Perfecto! Voy a hacerte **30 preguntas** sobre tu bienestar académico, emocional, social y de hábitos. Solo responde **Sí** o **No** (o cuéntame con tus palabras en las últimas preguntas).\n\n¿Listo/a para empezar? 😊",
            "action": "start_questionnaire"
        }

    # Keyword matching
    for keyword, response in KEYWORD_RESPONSES.items():
        if keyword != "default" and keyword in ml:
            return {"text": response}

    return {"text": KEYWORD_RESPONSES["default"]}

def handle_questionnaire(message, chat_state):
    current_q = chat_state.get("current_question", 1)
    answers   = chat_state.get("answers", {})
    ml        = message.lower().strip()

    # Save answer for current question
    if current_q <= 30:
        q_data = QUESTIONS[current_q - 1]
        if q_data["cat"] == "abierta":
            answers[str(current_q)] = message
            response_text = Q_RESPONSES[current_q]["open"]
        else:
            is_yes = any(w in ml for w in ["si", "sí", "yes", "a veces", "seguido", "mucho", "bastante"])
            answers[str(current_q)] = "si" if is_yes else "no"
            response_text = Q_RESPONSES[current_q]["si" if is_yes else "no"]

    next_q = current_q + 1

    if next_q > 30:
        # Finished — generate summary
        summary = generate_summary(answers)
        return {
            "text": response_text + "\n\n" + summary,
            "action": "questionnaire_done",
            "answers": answers,
            "new_state": {"mode": None, "current_question": 1, "answers": {}}
        }

    # Get category header if category changes
    current_cat = QUESTIONS[current_q - 1]["cat"]
    next_cat    = QUESTIONS[next_q - 1]["cat"]
    cat_names   = {"academico": "📚 Área Académica", "emocional": "💙 Área Emocional",
                   "social": "👥 Área Social", "habitos": "🌿 Hábitos y Bienestar", "abierta": "💬 Reflexión Personal"}
    cat_header  = f"\n\n**{cat_names[next_cat]}**\n" if next_cat != current_cat else "\n\n"

    next_question = QUESTIONS[next_q - 1]["text"]
    progress = f"*Pregunta {next_q} de 30*"

    return {
        "text": response_text + cat_header + f"{progress}\n**{next_question}**",
        "action": "next_question",
        "new_state": {"mode": "questionnaire", "current_question": next_q, "answers": answers}
    }

def generate_summary(answers):
    yes_count   = sum(1 for v in answers.values() if v == "si")
    no_count    = sum(1 for v in answers.values() if v == "no")
    open_count  = sum(1 for k, v in answers.items() if v not in ["si","no"])

    # Category scores
    academic_yes  = sum(1 for i in range(1,8)   if answers.get(str(i)) == "si")
    emotional_yes = sum(1 for i in range(8,17)  if answers.get(str(i)) == "si")
    social_yes    = sum(1 for i in range(17,23) if answers.get(str(i)) == "si")
    habits_yes    = sum(1 for i in range(23,29) if answers.get(str(i)) == "si")

    # Risk level
    if yes_count >= 18:      risk = "Alto"
    elif yes_count >= 10:    risk = "Medio"
    else:                    risk = "Bajo"

    recs = []
    if academic_yes >= 4:   recs.append("📚 Busca apoyo académico: tutoría o asesoría de materias.")
    if emotional_yes >= 5:  recs.append("💙 Te recomiendo hablar con un psicólogo o orientador.")
    if social_yes >= 3:     recs.append("👥 Considera fortalecer tu red de apoyo social.")
    if habits_yes >= 3:     recs.append("🌿 Trabaja en mejorar tus hábitos de sueño y descanso.")
    if not recs:            recs.append("✅ ¡Vas muy bien! Sigue cuidando tu bienestar.")

    recs_text = "\n".join(f"• {r}" for r in recs)

    return f"""---
✅ **¡Cuestionario completado!**

📊 **Resumen de tus respuestas:**
• Respuestas afirmativas: {yes_count}/28
• Nivel de atención sugerido: **{risk}**
• Área académica: {academic_yes}/7 señales
• Área emocional: {emotional_yes}/9 señales
• Área social: {social_yes}/6 señales
• Área de hábitos: {habits_yes}/6 señales

🎯 **Recomendaciones personalizadas:**
{recs_text}

Gracias por completar el cuestionario. Tus respuestas me ayudan a acompañarte mejor. 💙 ¿Quieres hablar sobre alguno de estos temas?"""

# ── ROUTES ───────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html') 

@app.route('/style.css')
def serve_css():
   return send_file('static/css/style.css', mimetype='text/css')

@app.route('/app.js')
def serve_js():
    return send_file('static/js/app.js', mimetype='application/javascript')

@app.route('/api/register', methods=['POST'])
def register():
    global db
    data     = request.json
    name     = data.get('name','').strip()
    email    = data.get('email','').strip().lower()
    password = data.get('password','')
    career   = data.get('career','').strip()
    semester = int(data.get('semester', 1))
    role     = data.get('role','estudiante')

    if not name or not email or not password:
        return jsonify({"success": False, "message": "Todos los campos son obligatorios"})
    if email in db["users"]:
        return jsonify({"success": False, "message": "Este correo ya está registrado"})
    if len(password) < 4:
        return jsonify({"success": False, "message": "La contraseña debe tener al menos 4 caracteres"})

    new_user = {"password": hash_password(password), "role": role, "name": name, "career": career or "Sin especificar", "semester": semester}
    if role == "estudiante":
        new_user.update({
            "risk_level": "Bajo", "progress": 0, "reminders": [],
            "recommendations": [
                {"icon": "🎉", "text": "¡Bienvenido/a! Completa el cuestionario de bienestar en el Chat.", "color": "#2563eb"},
                {"icon": "📚", "text": "Explora los recursos académicos disponibles.", "color": "#16a34a"},
            ],
            "evaluations": [], "chat_history": []
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
    data     = request.json
    email    = data.get('email','').strip().lower()
    password = data.get('password','')

    if email in db["users"] and check_password(password, db["users"][email]['password']):
        user = db["users"][email].copy()
        user.pop('password')
        if user.get("role") == "estudiante":
            tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
            user["tomorrow_alerts"] = [r for r in user.get("reminders",[]) if r.get("date") == tomorrow]
        return jsonify({"success": True, "user": user})
    return jsonify({"success": False, "message": "Correo o contraseña incorrectos"})

@app.route('/api/chat', methods=['POST'])
def chat():
    global db
    data       = request.json
    message    = data.get('message','')
    email      = data.get('email','')
    chat_state = data.get('chat_state', {})

    result = get_ai_response(message, chat_state)

    # Update chat state if questionnaire
    new_state = result.get("new_state", chat_state)

    # If questionnaire finished, update risk level
    if result.get("action") == "questionnaire_done" and email and email in db["users"]:
        answers  = result.get("answers", {})
        yes_count = sum(1 for v in answers.values() if v == "si")
        risk = "Alto" if yes_count >= 18 else "Medio" if yes_count >= 10 else "Bajo"
        db["users"][email]["risk_level"] = risk
        save_db(db)

    return jsonify({
        "response":   result["text"],
        "action":     result.get("action",""),
        "chat_state": new_state,
        "timestamp":  datetime.datetime.now().strftime("%H:%M")
    })

@app.route('/api/evaluate', methods=['POST'])
def evaluate():
    global db
    db = load_db()
    data        = request.json
    email       = data.get('email','')
    absences    = data.get('absences','No')
    motivation  = data.get('motivation','Mucho')
    performance = data.get('performance','Alto')

    risk = "Bajo"; recs = []
    if absences == 'Si':
        risk = "Medio"
        recs.append({"icon":"📅","text":"Retoma la asistencia a clases esta semana.","color":"#d97706"})
    if motivation == 'Poco':
        if risk == "Bajo": risk = "Medio"
        recs.append({"icon":"🎯","text":"Establece metas pequeñas y alcanzables diariamente.","color":"#2563eb"})
    if motivation == 'Nada':
        risk = "Alto"
        recs.append({"icon":"💙","text":"Agenda una sesión con el consejero estudiantil.","color":"#dc2626"})
    if performance == 'Bajo':
        risk = "Alto"
        recs.append({"icon":"📚","text":"Solicita una tutoría de emergencia esta semana.","color":"#dc2626"})
    if not recs:
        recs = [
            {"icon":"✅","text":"¡Vas muy bien! Mantén tu ritmo de estudio actual.","color":"#16a34a"},
            {"icon":"🌟","text":"Considera participar en grupos de estudio.","color":"#2563eb"},
        ]

    if email and email in db["users"]:
        db["users"][email].setdefault("evaluations",[]).append({
            "date": datetime.date.today().isoformat(),
            "absences": absences, "motivation": motivation,
            "performance": performance, "risk": risk
        })
        db["users"][email]["risk_level"] = risk
        db["users"][email]["recommendations"] = recs
        save_db(db)

    return jsonify({"risk": risk, "recommendations": recs})

@app.route('/api/reminders', methods=['GET'])
def get_reminders():
    db2   = load_db()
    email = request.args.get('email','')
    if email not in db2["users"]:
        return jsonify({"reminders": []})
    reminders = db2["users"][email].get("reminders",[])
    today    = datetime.date.today().isoformat()
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    for r in reminders:
        r["is_today"]    = r.get("date") == today
        r["is_tomorrow"] = r.get("date") == tomorrow
        r["is_overdue"]  = r.get("date","") < today
    return jsonify({"reminders": reminders})

@app.route('/api/reminders/add', methods=['POST'])
def add_reminder():
    global db
    db    = load_db()
    data  = request.json
    email = data.get('email','')
    task  = data.get('task','').strip()
    date  = data.get('date','')
    icon  = data.get('icon','📋')
    if not task or not date or email not in db["users"]:
        return jsonify({"success": False, "message": "Datos inválidos"})
    rid = f"r{datetime.datetime.now().timestamp()}"
    db["users"][email].setdefault("reminders",[]).append({"id":rid,"icon":icon,"task":task,"date":date})
    save_db(db)
    return jsonify({"success": True, "reminder": {"id":rid,"icon":icon,"task":task,"date":date}})

@app.route('/api/reminders/delete', methods=['POST'])
def delete_reminder():
    global db
    db    = load_db()
    data  = request.json
    email = data.get('email','')
    rid   = data.get('id','')
    if email in db["users"]:
        db["users"][email]["reminders"] = [r for r in db["users"][email].get("reminders",[]) if r["id"] != rid]
        save_db(db)
    return jsonify({"success": True})

@app.route('/api/admin/students', methods=['GET'])
def admin_students():
    db = load_db()
    students = {e:u for e,u in db["users"].items() if u.get("role") == "estudiante"}
    return jsonify({"students": [{"email":e,"name":s["name"],"career":s["career"],
        "semester":s["semester"],"risk_level":s.get("risk_level","Bajo"),
        "progress":s.get("progress",0),"evaluations_count":len(s.get("evaluations",[])),
        "reminders_count":len(s.get("reminders",[]))} for e,s in students.items()]})

@app.route('/api/admin/stats', methods=['GET'])
def admin_stats():
    db = load_db()
    students   = {e:u for e,u in db["users"].items() if u.get("role") == "estudiante"}
    risk_counts = {"Bajo":0,"Medio":0,"Alto":0}
    for s in students.values():
        r = s.get("risk_level","Bajo")
        risk_counts[r] = risk_counts.get(r,0) + 1
    psicologos = sum(1 for u in db["users"].values() if u.get("role") == "psicologo")
    return jsonify({"total_students":len(students),"risk_counts":risk_counts,
                    "total_psicologos":psicologos,"total_users":len(db["users"])})

@app.route('/api/admin/delete_user', methods=['POST'])
def delete_user():
    global db
    db    = load_db()
    data  = request.json
    email = data.get('email','')
    if email in db["users"] and db["users"][email].get("role") != "admin":
        del db["users"][email]; save_db(db)
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "No se puede eliminar"})

@app.route('/api/psico/alerts', methods=['GET'])
def psico_alerts():
    db = load_db()
    students = {e:u for e,u in db["users"].items() if u.get("role") == "estudiante"}
    alerts   = []
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    for email, s in students.items():
        if s.get("risk_level") in ["Medio","Alto"]:
            alerts.append({"type":"risk","student":s["name"],"email":email,
                "career":s["career"],"semester":s["semester"],"risk":s.get("risk_level"),
                "message":f"Nivel de riesgo {s.get('risk_level')}"})
        for r in s.get("reminders",[]):
            if r.get("date") == tomorrow:
                alerts.append({"type":"reminder","student":s["name"],"email":email,
                    "message":f"Tarea vence mañana: {r['task']}"})
    return jsonify({"alerts": alerts})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
