from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import os

app = Flask(__name__)
app.secret_key = 'llave_segura_traku'

# Función para cargar usuarios desde el JSON
def cargar_usuarios():
    if os.path.exists('students.json'):
        with open('students.json', 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

# Función para guardar usuarios en el JSON
def guardar_usuarios(usuarios):
    with open('students.json', 'w', encoding='utf-8') as f:
        json.dump(usuarios, f, indent=4)

@app.route('/')
def index():
    if 'username' in session:
        usuarios = cargar_usuarios()
        # Buscamos al usuario actual para obtener sus tareas guardadas
        user_data = next((u for u in usuarios if u['username'] == session['username']), None)
        
        # Si el usuario no tiene la lista de tareas, enviamos una lista vacía
        tareas = user_data.get('tasks', []) if user_data else []
        
        return render_template('index.html', 
                               role=session.get('role'), 
                               user=session.get('username'),
                               tareas=tareas)
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    usuarios = cargar_usuarios()
    
    user = next((u for u in usuarios if u['username'] == username and u['password'] == password), None)
    
    if user:
        session['username'] = user['username']
        session['role'] = user['role']
        return redirect(url_for('index'))
    return "Credenciales incorrectas. <a href='/'>Intentar de nuevo</a>"

@app.route('/add_task', methods=['POST'])
def add_task():
    if 'username' in session and session['role'] == 'estudiante':
        nueva_tarea = request.json # Recibe {title: "...", start: "..."}
        usuarios = cargar_usuarios()
        
        for u in usuarios:
            if u['username'] == session['username']:
                if 'tasks' not in u:
                    u['tasks'] = []
                u['tasks'].append(nueva_tarea)
                break
        
        guardar_usuarios(usuarios)
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "No autorizado"}), 403

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)