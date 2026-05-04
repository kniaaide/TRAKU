/* ===== STATE ===== */
let currentUser = null;
let evalState = { absences: 'Si', motivation: 'Poco', performance: 'Regular' };
let selectedIcon = '📋';
let calYear = new Date().getFullYear();
let calMonth = new Date().getMonth();
let allReminders = [];
let selectedLoginRole = null;

/* ===== ROLE SELECTION ===== */
function selectLoginRole(role) {
  selectedLoginRole = role;
  document.querySelectorAll('.role-card').forEach(c => c.classList.remove('selected'));
  document.getElementById('role-' + role).classList.add('selected');
  document.getElementById('login-role-error').classList.add('hidden');
}

function getRoleLabel(role) {
  return { estudiante: 'Estudiante', psicologo: 'Psicólogo / Orientador', admin: 'Administrador' }[role] || role;
}

/* ===== AUTH TABS ===== */
function switchTab(tab) {
  document.getElementById('tab-login').classList.add('hidden');
  document.getElementById('tab-register').classList.add('hidden');
  document.getElementById('tab-' + tab).classList.remove('hidden');
  document.getElementById('tab-btn-login').classList.toggle('active', tab === 'login');
  document.getElementById('tab-btn-register').classList.toggle('active', tab === 'register');
}

/* ===== LOGIN ===== */
async function handleLogin(e) {
  e.preventDefault();
  if (!selectedLoginRole) {
    document.getElementById('login-role-error').classList.remove('hidden');
    return;
  }
  const email = document.getElementById('email').value.trim();
  const password = document.getElementById('password').value;
  const errEl = document.getElementById('login-error');
  errEl.classList.add('hidden');
  try {
    const res = await fetch('/api/login', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (data.success) {
      if (data.user.role !== selectedLoginRole) {
        errEl.textContent = 'Este correo no corresponde a un ' + getRoleLabel(selectedLoginRole) + '. Verifica tu rol.';
        errEl.classList.remove('hidden');
        return;
      }
      currentUser = data.user;
      currentUser.email = email;
      routeByRole(data.user);
    } else {
      errEl.textContent = data.message || 'Correo o contraseña incorrectos';
      errEl.classList.remove('hidden');
    }
  } catch { loginAsGuest(); }
}

/* ===== REGISTER ROLE ===== */
let selectedRegRole = 'estudiante';
function selectRegRole(role) {
  selectedRegRole = role;
  document.querySelectorAll('[id^="reg-role-"]').forEach(c => c.classList.remove('selected'));
  document.getElementById('reg-role-' + role).classList.add('selected');
  document.getElementById('reg-role').value = role;

  const studentFields = document.getElementById('reg-student-fields');
  const staffFields   = document.getElementById('reg-staff-fields');
  const careerInput   = document.getElementById('reg-career');

  if (role === 'estudiante') {
    if (studentFields) studentFields.style.display = '';
    if (staffFields)   staffFields.style.display   = 'none';
    if (careerInput)   careerInput.required = true;
  } else {
    if (studentFields) studentFields.style.display = 'none';
    if (staffFields)   staffFields.style.display   = '';
    if (careerInput)   careerInput.required = false;
  }
}

/* ===== REGISTER ===== */
async function handleRegister(e) {
  e.preventDefault();
  const role = document.getElementById('reg-role').value;
  const isStaff = role === 'psicologo' || role === 'admin';
  const careerEl = document.getElementById('reg-career');
  const areaEl   = document.getElementById('reg-area');
  const body = {
    name:     document.getElementById('reg-name').value,
    email:    document.getElementById('reg-email').value,
    password: document.getElementById('reg-password').value,
    career:   isStaff ? (areaEl ? areaEl.value || 'Sin área' : 'Sin área') : (careerEl ? careerEl.value : ''),
    semester: isStaff ? 0 : parseInt(document.getElementById('reg-semester').value),
    role:     role
  };
  const errEl = document.getElementById('register-error');
  const sucEl = document.getElementById('register-success');
  errEl.classList.add('hidden'); sucEl.classList.add('hidden');
  try {
    const res = await fetch('/api/register', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const data = await res.json();
    if (data.success) {
      sucEl.textContent = '¡Cuenta creada! Iniciando sesión...';
      sucEl.classList.remove('hidden');
      currentUser = data.user;
      currentUser.email = body.email;
      setTimeout(() => routeByRole(data.user), 1200);
    } else {
      errEl.textContent = data.message;
      errEl.classList.remove('hidden');
    }
  } catch {
    errEl.textContent = 'Error de conexión.';
    errEl.classList.remove('hidden');
  }
}

function loginAsGuest() {
  currentUser = {
    name: 'Invitado', career: 'Estudiante', semester: 1,
    role: 'estudiante', risk_level: 'Bajo', progress: 0,
    reminders: [], recommendations: [
      { icon: '🎉', text: 'Bienvenido/a a TraKU! Completa tu evaluación.', color: '#2563eb' }
    ], email: 'guest@traku.edu'
  };
  routeByRole(currentUser);
}

/* ===== ROUTING ===== */
function routeByRole(user) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  if (user.role === 'admin') {
    document.getElementById('screen-admin').classList.add('active');
    loadAdminData();
  } else if (user.role === 'psicologo') {
    document.getElementById('screen-psicologo').classList.add('active');
    document.getElementById('p-name').textContent = user.name;
    loadPsicoAlerts();
    loadPsicoStudents();
  } else {
    document.getElementById('screen-estudiante').classList.add('active');
    initStudentDashboard(user);
  }
}

function logout() {
  currentUser = null;
  allReminders = [];
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById('screen-login').classList.add('active');
  document.getElementById('email').value = '';
  document.getElementById('password').value = '';
  document.getElementById('chat-messages').innerHTML = `
    <div class="msg bot-msg"><div class="msg-avatar">🤖</div>
    <div class="msg-bubble">¡Hola! Soy TraKU, tu asistente universitario. ¿Cómo te sientes hoy?</div></div>`;
}

/* ===== STUDENT INIT ===== */
function initStudentDashboard(user) {
  document.getElementById('s-name').textContent = user.name;
  document.getElementById('s-info').textContent = `${user.career} | Semestre ${user.semester}`;
  document.getElementById('s-avatar').textContent = user.name.charAt(0).toUpperCase();

  // Risk
  const badge = document.getElementById('s-risk-badge');
  document.getElementById('s-risk-text').textContent = user.risk_level || 'Bajo';
  badge.className = 'risk-badge';
  if (user.risk_level === 'Bajo') badge.classList.add('low');
  else if (user.risk_level === 'Alto') badge.classList.add('high');

  // Progress
  const p = user.progress || 0;
  document.getElementById('s-progress-num').textContent = p;
  document.getElementById('s-progress-bar').style.width = p + '%';

  // Tomorrow alerts banner
  if (user.tomorrow_alerts && user.tomorrow_alerts.length > 0) {
    const banner = document.getElementById('alert-banner');
    banner.classList.remove('hidden');
    banner.innerHTML = `⚠️ Tienes ${user.tomorrow_alerts.length} tarea(s) que vencen mañana: ${user.tomorrow_alerts.map(r => r.task).join(', ')}`;
  }

  loadStudentReminders();
  loadStudentRecommendations(user.recommendations || []);
  renderCalendar();
  showSection('s-dashboard');
}

/* ===== SECTION NAVIGATION ===== */
function showSection(name) {
  document.querySelectorAll('#screen-estudiante .content-section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('#screen-estudiante .nav-item').forEach(n => n.classList.remove('active'));
  const sec = document.getElementById(`section-${name}`);
  if (sec) sec.classList.add('active');
  document.querySelectorAll('#screen-estudiante .nav-item').forEach(item => {
    if (item.getAttribute('onclick') && item.getAttribute('onclick').includes(name))
      item.classList.add('active');
  });
  if (name === 's-calendar') { loadStudentReminders(); renderCalendar(); }
}

function showPsicoSection(name) {
  document.querySelectorAll('#screen-psicologo .content-section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('#screen-psicologo .nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById(`section-${name}`).classList.add('active');
  document.querySelectorAll('#screen-psicologo .nav-item').forEach(item => {
    if (item.getAttribute('onclick') && item.getAttribute('onclick').includes(name))
      item.classList.add('active');
  });
  if (name === 'p-students') loadPsicoStudents();
  if (name === 'p-reports') loadPsicoReports();
}

function showAdminSection(name) {
  document.querySelectorAll('#screen-admin .content-section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('#screen-admin .nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById(`section-${name}`).classList.add('active');
  document.querySelectorAll('#screen-admin .nav-item').forEach(item => {
    if (item.getAttribute('onclick') && item.getAttribute('onclick').includes(name))
      item.classList.add('active');
  });
  if (name === 'a-users') loadAdminUsers();
}

/* ===== STUDENT REMINDERS ===== */
async function loadStudentReminders() {
  if (!currentUser || !currentUser.email) return;
  try {
    const res = await fetch(`/api/reminders?email=${currentUser.email}`);
    const data = await res.json();
    allReminders = data.reminders || [];
    renderDashboardReminders();
    renderUpcoming();
    renderCalendar();
  } catch { allReminders = currentUser.reminders || []; renderDashboardReminders(); }
}

function renderDashboardReminders() {
  const list = document.getElementById('s-reminder-list');
  const today = new Date().toISOString().split('T')[0];
  const tomorrow = new Date(Date.now() + 86400000).toISOString().split('T')[0];
  const upcoming = allReminders
    .filter(r => r.date >= today)
    .sort((a,b) => a.date.localeCompare(b.date))
    .slice(0, 4);

  if (!upcoming.length) {
    list.innerHTML = '<li class="reminder-empty">Sin recordatorios próximos. ¡Ve al Calendario!</li>';
    return;
  }
  list.innerHTML = upcoming.map(r => {
    let cls = '', badge = '';
    if (r.date === today) { cls = 'today'; badge = '<span class="reminder-badge">¡Hoy!</span>'; }
    else if (r.date === tomorrow) { cls = 'tomorrow'; badge = '<span class="reminder-badge tomorrow">Mañana</span>'; }
    else if (r.date < today) cls = 'overdue';
    return `<li class="reminder-item ${cls}">
      <div class="reminder-icon">${r.icon}</div>
      <div style="flex:1"><div class="reminder-task">${r.task}</div>
      <div class="reminder-date">${formatDate(r.date)}</div></div>${badge}</li>`;
  }).join('');
}

function renderUpcoming() {
  const today = new Date().toISOString().split('T')[0];
  const sorted = allReminders.filter(r => r.date >= today).sort((a,b) => a.date.localeCompare(b.date));
  const el = document.getElementById('upcoming-list');
  if (!sorted.length) { el.innerHTML = '<p style="color:#94a3b8;font-size:13px;text-align:center;padding:16px">No hay fechas límite próximas</p>'; return; }
  el.innerHTML = sorted.map(r => {
    const days = Math.ceil((new Date(r.date) - new Date(today)) / 86400000);
    let cls = 'ok', daysLabel = `${days}d`, itemCls = '';
    if (days === 0) { cls = ''; daysLabel = '¡Hoy!'; itemCls = 'urgent'; }
    else if (days === 1) { cls = 'warn'; daysLabel = '¡Mañana!'; itemCls = 'warning'; }
    else if (days <= 3) { cls = 'warn'; itemCls = 'warning'; }
    return `<div class="upcoming-item ${itemCls}">
      <span class="upcoming-icon">${r.icon}</span>
      <div class="upcoming-text">
        <div class="upcoming-task">${r.task}</div>
        <div class="upcoming-date">${formatDate(r.date)}</div>
      </div>
      <span class="upcoming-days ${cls}">${daysLabel}</span>
      <button class="del-btn" onclick="deleteReminder('${r.id}')">🗑</button>
    </div>`;
  }).join('');
}

async function addReminder() {
  const task = document.getElementById('task-name').value.trim();
  const date = document.getElementById('task-date').value;
  if (!task || !date) { alert('Por favor ingresa la tarea y la fecha.'); return; }
  try {
    const res = await fetch('/api/reminders/add', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: currentUser.email, task, date, icon: selectedIcon })
    });
    const data = await res.json();
    if (data.success) {
      document.getElementById('task-name').value = '';
      document.getElementById('task-date').value = '';
      await loadStudentReminders();
      // Check if tomorrow alert needed
      const tomorrow = new Date(Date.now() + 86400000).toISOString().split('T')[0];
      if (date === tomorrow) {
        const banner = document.getElementById('alert-banner');
        banner.classList.remove('hidden');
        banner.innerHTML = `⚠️ Recuerda: "${task}" vence mañana.`;
      }
    }
  } catch { console.error('Error adding reminder'); }
}

async function deleteReminder(id) {
  try {
    await fetch('/api/reminders/delete', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: currentUser.email, id })
    });
    await loadStudentReminders();
  } catch { console.error('Error deleting'); }
}

function selectIcon(btn) {
  document.querySelectorAll('.icon-btn').forEach(b => b.classList.remove('selected'));
  btn.classList.add('selected');
  selectedIcon = btn.getAttribute('data-icon');
}

/* ===== CALENDAR ===== */
function renderCalendar() {
  const title = document.getElementById('cal-title');
  const grid = document.getElementById('cal-grid');
  if (!title || !grid) return;

  const monthNames = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];
  title.textContent = `${monthNames[calMonth]} ${calYear}`;

  const today = new Date().toISOString().split('T')[0];
  const tomorrow = new Date(Date.now() + 86400000).toISOString().split('T')[0];

  // Build reminder map by date
  const reminderMap = {};
  allReminders.forEach(r => {
    if (!reminderMap[r.date]) reminderMap[r.date] = [];
    reminderMap[r.date].push(r);
  });

  const firstDay = new Date(calYear, calMonth, 1).getDay();
  const daysInMonth = new Date(calYear, calMonth + 1, 0).getDate();
  const daysInPrev = new Date(calYear, calMonth, 0).getDate();

  let html = '';
  // Prev month filler
  for (let i = firstDay - 1; i >= 0; i--) {
    html += `<div class="cal-day other-month"><span class="cal-day-num">${daysInPrev - i}</span></div>`;
  }
  // Current month
  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = `${calYear}-${String(calMonth+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
    const isToday = dateStr === today;
    const isTomorrow = dateStr === tomorrow;
    const tasks = reminderMap[dateStr] || [];
    let cls = '';
    if (isToday) cls = 'today';
    else if (tasks.length > 0 && isTomorrow) cls = 'has-task-tomorrow';
    else if (tasks.length > 0) cls = 'has-task';

    const dots = tasks.slice(0, 3).map(t => `<div class="cal-task-dot"></div>`).join('');
    const label = tasks.length === 1 ? `<div class="cal-task-label">${tasks[0].task}</div>` :
                  tasks.length > 1  ? `<div class="cal-task-label">${tasks.length} tareas</div>` : '';

    html += `<div class="cal-day ${cls}" title="${tasks.map(t=>t.task).join(', ')}">
      <span class="cal-day-num">${d}</span>
      <div class="cal-task-dots">${dots}</div>
      ${label}
    </div>`;
  }
  // Next month filler
  const total = firstDay + daysInMonth;
  const remaining = total % 7 === 0 ? 0 : 7 - (total % 7);
  for (let i = 1; i <= remaining; i++) {
    html += `<div class="cal-day other-month"><span class="cal-day-num">${i}</span></div>`;
  }
  grid.innerHTML = html;
}

function changeMonth(dir) {
  calMonth += dir;
  if (calMonth > 11) { calMonth = 0; calYear++; }
  if (calMonth < 0) { calMonth = 11; calYear--; }
  renderCalendar();
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  const [y,m,d] = dateStr.split('-');
  const months = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'];
  return `${parseInt(d)} ${months[parseInt(m)-1]} ${y}`;
}

/* ===== CHAT ===== */
async function sendMessage() {
  const input = document.getElementById('chat-input');
  const msg = input.value.trim();
  if (!msg) return;
  input.value = '';
  addMessage(msg, 'user');
  showTyping();
  try {
    const res = await fetch('/api/chat', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg })
    });
    const data = await res.json();
    removeTyping(); addMessage(data.response, 'bot');
  } catch { removeTyping(); addMessage('Lo siento, ocurrió un error. Intenta de nuevo.', 'bot'); }
}
function sendQuick(msg) { document.getElementById('chat-input').value = msg; sendMessage(); }
function addMessage(text, type) {
  const c = document.getElementById('chat-messages');
  const d = document.createElement('div');
  d.className = `msg ${type === 'bot' ? 'bot-msg' : 'user-msg'}`;
  d.innerHTML = type === 'bot'
    ? `<div class="msg-avatar">🤖</div><div class="msg-bubble">${text}</div>`
    : `<div class="msg-bubble">${text}</div><div class="msg-avatar" style="background:linear-gradient(135deg,#7c3aed,#ec4899)">👤</div>`;
  c.appendChild(d); c.scrollTop = c.scrollHeight;
}
function showTyping() {
  const c = document.getElementById('chat-messages');
  const d = document.createElement('div');
  d.className = 'msg bot-msg typing-indicator'; d.id = 'typing';
  d.innerHTML = `<div class="msg-avatar">🤖</div><div class="msg-bubble" style="display:flex;gap:4px"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></div>`;
  c.appendChild(d); c.scrollTop = c.scrollHeight;
}
function removeTyping() { const t = document.getElementById('typing'); if(t) t.remove(); }

/* ===== EVALUATION ===== */
function selectOpt(field, value, btn) {
  evalState[field] = value;
  btn.parentElement.querySelectorAll('.eval-btn').forEach(b => b.classList.remove('selected'));
  btn.classList.add('selected');
}
async function submitEvaluation() {
  try {
    const res = await fetch('/api/evaluate', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...evalState, email: currentUser?.email || '' })
    });
    const data = await res.json();
    if (currentUser) {
      currentUser.risk_level = data.risk;
      const badge = document.getElementById('s-risk-badge');
      document.getElementById('s-risk-text').textContent = data.risk;
      badge.className = 'risk-badge';
      if (data.risk === 'Bajo') badge.classList.add('low');
      else if (data.risk === 'Alto') badge.classList.add('high');
    }
    loadStudentRecommendations(data.recommendations);
    showSection('s-recommendations');
  } catch {
    loadStudentRecommendations([{ icon:'📚', text:'Continúa con tu plan de estudios.', color:'#2563eb' }]);
    showSection('s-recommendations');
  }
}
function loadStudentRecommendations(recs) {
  document.getElementById('rec-list').innerHTML = (recs||[]).map((r,i) => `
    <div class="rec-item" style="animation-delay:${i*.1}s;border-left-color:${r.color}">
      <div class="rec-icon" style="background:${r.color}20">${r.icon}</div>
      <div class="rec-text">${r.text}</div></div>`).join('');
}

/* ===== PSICÓLOGO ===== */
async function loadPsicoAlerts() {
  try {
    const res = await fetch('/api/psico/alerts');
    const data = await res.json();
    const el = document.getElementById('psico-alerts-list');
    if (!data.alerts.length) {
      el.innerHTML = '<div class="alert-empty">✅ No hay alertas activas en este momento.</div>'; return;
    }
    el.innerHTML = data.alerts.map(a => {
      const isRisk = a.type === 'risk';
      const color = isRisk ? (a.risk === 'Alto' ? '' : 'yellow') : 'yellow';
      return `<div class="alert-item ${isRisk ? '' : 'reminder'}">
        <div class="alert-icon">${isRisk ? (a.risk === 'Alto' ? '🚨' : '⚠️') : '⏰'}</div>
        <div class="alert-info">
          <h4>${a.student} — ${a.career} Sem. ${a.semester}</h4>
          <p>${a.message} · ${a.email}</p>
        </div>
        <span class="alert-badge ${color}">${isRisk ? a.risk : 'Recordatorio'}</span>
      </div>`;
    }).join('');
  } catch { document.getElementById('psico-alerts-list').innerHTML = '<div class="alert-empty">Error al cargar alertas.</div>'; }
}

async function loadPsicoStudents() {
  try {
    const res = await fetch('/api/admin/students');
    const data = await res.json();
    renderStudentsTable('psico-students-table', data.students, false);
  } catch {}
}

async function loadPsicoReports() {
  try {
    const res = await fetch('/api/admin/students');
    const data = await res.json();
    const high = data.students.filter(s => s.risk_level === 'Alto');
    const med  = data.students.filter(s => s.risk_level === 'Medio');
    const low  = data.students.filter(s => s.risk_level === 'Bajo');
    const wrap = document.getElementById('psico-reports');
    wrap.innerHTML = `
      <div class="report-card">
        <h4>🚨 Estudiantes en Riesgo Alto (${high.length})</h4>
        ${renderMiniTable(high)}
      </div>
      <div class="report-card">
        <h4>⚠️ Estudiantes en Riesgo Medio (${med.length})</h4>
        ${renderMiniTable(med)}
      </div>
      <div class="report-card">
        <h4>✅ Estudiantes en Riesgo Bajo (${low.length})</h4>
        ${renderMiniTable(low)}
      </div>`;
  } catch {}
}

function renderMiniTable(students) {
  if (!students.length) return '<p style="color:#94a3b8;padding:8px;font-size:13px">Sin estudiantes en esta categoría.</p>';
  return `<table class="report-table">
    <tr><th>Nombre</th><th>Carrera</th><th>Semestre</th><th>Evaluaciones</th></tr>
    ${students.map(s => `<tr>
      <td>${s.name}</td><td>${s.career}</td><td>${s.semester}</td><td>${s.evaluations_count}</td>
    </tr>`).join('')}
  </table>`;
}

/* ===== ADMIN ===== */
async function loadAdminData() {
  try {
    const res = await fetch('/api/admin/stats');
    const data = await res.json();
    const grid = document.getElementById('admin-stats-grid');
    grid.innerHTML = `
      <div class="stat-card"><div class="stat-icon">🎓</div><div class="stat-num">${data.total_students}</div><div class="stat-label">Estudiantes</div></div>
      <div class="stat-card"><div class="stat-icon">🧠</div><div class="stat-num">${data.total_psicologos}</div><div class="stat-label">Psicólogos</div></div>
      <div class="stat-card"><div class="stat-icon">👥</div><div class="stat-num">${data.total_users}</div><div class="stat-label">Usuarios Total</div></div>
      <div class="stat-card"><div class="stat-icon">🚨</div><div class="stat-num" style="color:#dc2626">${data.risk_counts.Alto}</div><div class="stat-label">Riesgo Alto</div></div>`;
    // Risk chart
    const total = data.total_students || 1;
    const chart = document.getElementById('risk-chart');
    ['Bajo','Medio','Alto'].forEach(r => {
      const cnt = data.risk_counts[r] || 0;
      const pct = Math.round((cnt / total) * 100);
      chart.innerHTML += `<div class="risk-bar-wrap">
        <div class="risk-bar-outer">
          <div class="risk-bar-inner ${r}" style="height:${Math.max(pct,4)}%"></div>
        </div>
        <div class="risk-bar-count">${cnt}</div>
        <div class="risk-bar-label">${r}</div>
      </div>`;
    });
  } catch {}
}

async function loadAdminUsers() {
  try {
    const res = await fetch('/api/admin/students');
    const data = await res.json();
    renderStudentsTable('admin-users-table', data.students, true);
  } catch {}
}

function renderStudentsTable(containerId, students, showDelete) {
  const wrap = document.getElementById(containerId);
  if (!students.length) { wrap.innerHTML = '<p style="padding:24px;color:#94a3b8">Sin estudiantes registrados.</p>'; return; }
  wrap.innerHTML = `<table class="students-table">
    <thead><tr><th>Nombre</th><th>Carrera</th><th>Semestre</th><th>Riesgo</th><th>Evaluaciones</th>${showDelete ? '<th></th>' : ''}</tr></thead>
    <tbody>${students.map(s => `<tr>
      <td><strong>${s.name}</strong><br><span style="color:#94a3b8;font-size:11px">${s.email}</span></td>
      <td>${s.career}</td><td>S${s.semester}</td>
      <td><span class="risk-pill ${s.risk_level}">${s.risk_level}</span></td>
      <td>${s.evaluations_count}</td>
      ${showDelete ? `<td><button class="del-user-btn" onclick="deleteUser('${s.email}')">🗑</button></td>` : ''}
    </tr>`).join('')}</tbody>
  </table>`;
}

async function deleteUser(email) {
  if (!confirm(`¿Eliminar al usuario ${email}?`)) return;
  try {
    await fetch('/api/admin/delete_user', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });
    loadAdminUsers();
    loadAdminData();
  } catch {}
}

async function adminRegister(e) {
  e.preventDefault();
  const body = {
    name: document.getElementById('a-name').value,
    email: document.getElementById('a-email').value,
    password: document.getElementById('a-password').value,
    career: document.getElementById('a-career').value,
    semester: document.getElementById('a-semester').value,
    role: document.getElementById('a-role').value
  };
  const errEl = document.getElementById('admin-reg-error');
  const sucEl = document.getElementById('admin-reg-success');
  errEl.classList.add('hidden'); sucEl.classList.add('hidden');
  try {
    const res = await fetch('/api/register', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const data = await res.json();
    if (data.success) {
      sucEl.textContent = `✅ Usuario "${body.name}" registrado exitosamente como ${body.role}.`;
      sucEl.classList.remove('hidden');
      document.getElementById('a-name').value = '';
      document.getElementById('a-email').value = '';
      document.getElementById('a-password').value = '';
      document.getElementById('a-career').value = '';
      loadAdminData();
    } else {
      errEl.textContent = data.message;
      errEl.classList.remove('hidden');
    }
  } catch {
    errEl.textContent = 'Error de conexión.';
    errEl.classList.remove('hidden');
  }
}