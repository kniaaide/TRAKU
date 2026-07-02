# TraKU — Informe de estado real y correcciones aplicadas

## 1. Estado real del proyecto (inventario exacto)

| Archivo | Líneas | Tamaño |
|---|---|---|
| `app.py` | 515 | 32 475 bytes |
| `static/js/app.js` | 694 | 28 300 bytes |
| `templates/index.html` | 588 | 25 494 bytes |
| `static/css/style.css` | 389 | 27 157 bytes |
| `students.json` | 263 | 6 830 bytes |
| `requirements.txt` | 3 | 26 bytes |
| `static/img/logo.jpeg` | — | 103 311 bytes |

**Nota:** el documento de arquitectura original hablaba de "15 usuarios reales". El conteo exacto sobre tu `students.json` da **17 usuarios**, no 15. Aquí está la tabla real:

| Email | Rol | Nombre | Semestre | Riesgo |
|---|---|---|---|---|
| admin@traku.edu | admin | Administrador TraKU | 0 | — |
| psicologa@traku.edu | psicologo | Dra. Martínez | 0 | — |
| karime@universidad.edu | estudiante | Karime | 6 | Medio |
| hermin@gmil.com | estudiante | herminia | 3 | Bajo |
| herminpol@gmil.com | estudiante | herminia | 3 | Bajo |
| nina@gmail.com | psicologo | nina | 0 | — |
| onichan@gimail | admin | koko | 0 | — |
| pip@gmali.com | psicologo | pip | 0 | — |
| kikki@gmail.com | estudiante | kenia | 2 | Bajo |
| kicsc@gmail.com | psicologo | kenia | 0 | — |
| abyade@gmil.com | estudiante | LIlian Abyade Resendiz | 6 | Bajo |
| sofia@gmil.com | psicologo | Ana Sofia Castro | 0 | — |
| aide@gmil.com | admin | Kenia Aide Martinez | 0 | — |
| alejandra@gmail.com | psicologo | ALEJANDRA | 0 | — |
| aleandra@gmail.com | estudiante | ALEJANDRA | 6 | Bajo |
| aleana@gmail.com | estudiante | ALEJANDR | 6 | Bajo |
| ale@gmail.com | psicologo | ALEJ | 0 | — |

Total: 7 estudiantes, 7 psicólogos, 3 admins.

### Estado real de módulos

| Módulo | Estado | Nota |
|---|---|---|
| Login / registro | ✅ | funciona, contraseñas ahora con bcrypt |
| Chat con cuestionario de 30 preguntas | ✅ | basado en reglas/keywords, no IA generativa real |
| Recordatorios (CRUD) | ✅ | completo |
| Evaluación rápida (`/api/evaluate`) | ✅ | completo |
| Panel admin (estudiantes/stats) | ✅ | completo |
| Alertas para psicólogo | ⚠️ | existe pero sin filtro por campus (single-tenant) |
| Seguridad de contraseñas | ⚠️→✅ | estaban en texto plano, corregido en esta entrega |
| Base de datos relacional | ❌→✅ | antes solo JSON; se entrega SQLite real + DDL SQL Server |
| Multi-campus / Instituciones | ❌ | no implementado (fuera de alcance de esta entrega) |
| Cifrado de chat en reposo (TDE) | ❌ | no implementado |
| Habilitación de psicólogos (test 70/100) | ❌ | no implementado |
| Notificaciones cron (APScheduler) | ❌ | no implementado |
| Informes semanales de psicología | ❌ | no implementado |
| Auditoría | ❌ | no implementado |

## 2. Arquitectura actual (flujo real)

Ver el diagrama de arriba: `app.py` sirve `/` con `render_template`, pero `/style.css` y `/app.js` **no** usan la carpeta `static` de Flask directamente — son rutas manuales con `send_file()`. Esto es distinto de lo típico (`url_for('static', filename=...)`) y significa que si mueves esos archivos, hay que actualizar esas dos rutas a mano.

**Bug encontrado (no reportado antes):** `templates/index.html` tenía `<link rel="stylesheet" href="/style.css">` duplicado, y **faltaba el `<link>` al CDN de Tabler Icons** aunque el HTML usa clases `ti ti-*` en más de 15 lugares — los íconos no se estaban renderizando. Ambos se corrigieron.

## 3. 🚨 Alerta de seguridad — contraseñas en texto plano (CRÍTICO, corregido)

`students.json` guardaba contraseñas así:
```json
"karime@universidad.edu": { "password": "1234", ... }
```

Cualquiera con acceso al archivo (o a un backup, un `git log`, un log de errores) ve todas las contraseñas de golpe. Se corrigió en `app.py`:

- `hash_password()` usa `bcrypt.hashpw()` para nuevos registros.
- `check_password()` verifica hash bcrypt, y sigue aceptando temporalmente contraseñas viejas en texto plano para no romper logins existentes.
- `migrate_plaintext_passwords()` corre automáticamente al iniciar la app: convierte cualquier contraseña en texto plano a hash bcrypt y guarda el archivo. Se probó contra tus 17 usuarios reales y funcionó sin romper ningún login.

## 4. Migración de JSON a base de datos (ejecutada)

`migrate_json_to_db.py` lee `students.json` campo por campo tal cual existen hoy (`password`, `role`, `name`, `career`, `semester`, `risk_level`, `progress`, `reminders[]`, `recommendations[]`, `evaluations[]`, `chat_history[]`) y los inserta en `traku.db` (SQLite). Se ejecutó de verdad sobre tus datos:

```
📄 students.json: 17 usuarios encontrados
✅ Migración completa → traku.db
   Usuarios:        17
   Recordatorios:   3
   Recomendaciones: 15
   Evaluaciones:    0
```

`schema_sqlserver.sql` trae el mismo esquema en T-SQL para cuando quieras pasar de SQLite a SQL Server real — usa solo los campos que existen hoy, no el esquema multi-campus/cifrado del documento original (ese queda como Fase 2, ver roadmap).

## 5. Stack real: qué tienes vs qué falta

| Componente | Estado |
|---|---|
| Flask | ✅ instalado (`requirements.txt`) |
| Flask-CORS | ✅ instalado |
| Gunicorn | ✅ instalado |
| Google Fonts (Nunito, Poppins) | ✅ ya estaba en `index.html` |
| Tabler Icons | ❌ usado en el HTML pero el `<link>` del CDN faltaba — **agregado ahora** |
| bcrypt | ❌ no estaba — **agregado ahora** |
| SQL Server / motor relacional | ❌ no había — se entrega SQLite funcional + DDL SQL Server |
| APScheduler (notificaciones) | ❌ no instalado, no implementado |
| Cifrado en reposo (TDE) | ❌ no implementado |

## 6. Roadmap actualizado

1. **Fase 1 (urgente, ya entregada):** eliminar contraseñas en texto plano → hecho con bcrypt + migración automática.
2. **Fase 2:** mover de SQLite a SQL Server real usando `schema_sqlserver.sql`, o mantener SQLite si el volumen de usuarios sigue siendo bajo (17 usuarios no necesitan SQL Server todavía).
3. **Fase 3:** notificaciones automáticas (APScheduler) para recordatorios próximos a vencer.
4. **Fase 4:** multi-campus (tabla `Instituciones`), habilitación de psicólogos, informes semanales, auditoría — todo esto sigue siendo diseño a futuro, no código existente.
