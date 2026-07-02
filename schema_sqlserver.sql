-- ============================================================
-- TraKU — Esquema SQL Server (Fase 1: reemplazo directo del JSON actual)
-- Corresponde EXACTAMENTE a los campos que hoy existen en students.json.
-- El esquema multi-campus/cifrado del documento de arquitectura v2
-- (Instituciones, Sesiones_Chat cifradas, Alertas_Crisis, etc.) es
-- un ROADMAP a futuro, no el estado actual — no se incluye aquí para
-- no confundir "lo que hay" con "lo que se propone".
-- ============================================================

CREATE TABLE Usuarios (
    UsuarioID       INT           IDENTITY(1,1) PRIMARY KEY,
    Email           NVARCHAR(200) NOT NULL UNIQUE,
    PasswordHash    NVARCHAR(200) NOT NULL,   -- bcrypt, nunca texto plano
    Rol             NVARCHAR(20)  NOT NULL CHECK (Rol IN ('admin','psicologo','estudiante')),
    Nombre          NVARCHAR(200) NOT NULL,
    Carrera         NVARCHAR(200),
    Semestre        INT           DEFAULT 0,
    NivelRiesgo     NVARCHAR(10)  DEFAULT 'Bajo',
    Progreso        INT           DEFAULT 0
);

CREATE TABLE Recordatorios (
    RecordatorioID  INT           IDENTITY(1,1) PRIMARY KEY,
    UsuarioID       INT           NOT NULL REFERENCES Usuarios(UsuarioID) ON DELETE CASCADE,
    Icono           NVARCHAR(10),
    Tarea           NVARCHAR(300) NOT NULL,
    Fecha           DATE          NOT NULL
);

CREATE TABLE Recomendaciones (
    RecomendacionID INT           IDENTITY(1,1) PRIMARY KEY,
    UsuarioID       INT           NOT NULL REFERENCES Usuarios(UsuarioID) ON DELETE CASCADE,
    Icono           NVARCHAR(10),
    Texto           NVARCHAR(500) NOT NULL,
    Color           NVARCHAR(10)
);

CREATE TABLE Evaluaciones (
    EvaluacionID    INT           IDENTITY(1,1) PRIMARY KEY,
    UsuarioID       INT           NOT NULL REFERENCES Usuarios(UsuarioID) ON DELETE CASCADE,
    Fecha           DATE,
    Ausencias       NVARCHAR(10),
    Motivacion      NVARCHAR(20),
    Desempeno       NVARCHAR(20),
    Riesgo          NVARCHAR(10)
);

CREATE TABLE ChatHistorial (
    MensajeID       INT           IDENTITY(1,1) PRIMARY KEY,
    UsuarioID       INT           NOT NULL REFERENCES Usuarios(UsuarioID) ON DELETE CASCADE,
    Contenido       NVARCHAR(MAX) NOT NULL,
    Timestamp       DATETIME2     DEFAULT SYSDATETIME()
);

CREATE INDEX IX_Recordatorios_UsuarioID ON Recordatorios(UsuarioID);
CREATE INDEX IX_Recomendaciones_UsuarioID ON Recomendaciones(UsuarioID);
CREATE INDEX IX_Evaluaciones_UsuarioID ON Evaluaciones(UsuarioID);
CREATE INDEX IX_ChatHistorial_UsuarioID ON ChatHistorial(UsuarioID);
