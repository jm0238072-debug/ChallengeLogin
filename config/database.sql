-- Crear base de datos
CREATE DATABASE sistema_usuarios;

\c sistema_usuarios;

CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    email VARCHAR(254) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    intentos_fallidos INT DEFAULT 0,
    bloqueado_hasta TIMESTAMP DEFAULT NULL,
    ultima_actividad TIMESTAMP DEFAULT NULL,
    session_id VARCHAR(128) DEFAULT NULL
);

CREATE INDEX idx_email ON usuarios(email);