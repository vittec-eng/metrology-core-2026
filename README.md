# Metrology Core 2026

Sistema integral de gestión de activos de metrología para calibración interna de instrumentos y patrones de medición.

## 🎯 Características Principales

- **Gestión de Instrumentos**: Control completo de instrumentos de medición con historial de calibraciones
- **Gestión de Patrones**: Administración de patrones de referencia con trazabilidad
- **Sistema de Calibración**: Protocolos de calibración con análisis estadístico
- **Generación de Informes**: Informes PDF profesionales (ICI - Informe de Calibración Interna)
- **Análisis Gráfico**: Visualización de tendencias y dispersiones con matplotlib
- **Sistema de Usuarios**: Roles de acceso (Administrador, Operario, Visor)
- **Auditoría y Seguridad**: Registro completo de eventos con integridad verificada
- **Control de Integridad**: Sistema de hashes para detectar modificaciones no autorizadas

## 👤 Usuarios y Roles

| Usuario | Contraseña | Rol | Permisos |
|---------|------------|-----|----------|
| **admin** | `123` | **Administrador** | Gestión de seguridad, usuarios y regeneración de bóveda de hashes. |
| **Gemini** | `111` | **Técnico** | Registro de calibraciones y edición de datos de instrumentos. |
| **Claude** | `222` | **Visor** | Solo lectura, consulta de históricos y visualización de gráficas de error. |

## ⚠️ **AVISO IMPORTANTE - SOFTWARE EN DESARROLLO**

**ESTA ES UNA APLICACIÓN EN FASE DE DESARROLLO Y PRUEBA**

- **Base de Datos Genérica**: El sistema utiliza una base de datos JSON genérica que puede contener fallos lógicos o inconsistencias.
- **Errores de Hash**: Es posible que aparezcan errores de verificación de hashes al iniciar la aplicación por primera vez. Esto es normal y se puede resolver seleccionando "Continuar" o "Restaurar" según corresponda.
- **Sin Compromiso**: Este software se proporciona "tal cual" sin ningún tipo de garantía o compromiso de funcionamiento.
- **Responsabilidad del Usuario**: El uso de esta aplicación es bajo la responsabilidad exclusiva del usuario. El desarrollador no se hace responsable de los datos, cálculos o decisiones tomadas basadas en este software.
- **Uso Experimental**: No utilizar para fines críticos o producción sin realizar pruebas exhaustivas.

**AL UTILIZAR ESTE SOFTWARE, ACEPTA ESTOS TÉRMINOS Y CONDICIONES**

## 📋 Requisitos del Sistema

- Python 3.8 o superior
- Sistema operativo: Windows, Linux o macOS

## 🚀 Instalación

1. **Clonar el repositorio:**
```bash
git clone <repository-url>
cd metrologia-v02-github
```

2. **Crear entorno virtual (recomendado):**
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

## 🏃‍♂️ Ejecución

```bash
python main.py
```

## 👤 Usuarios y Roles

### Administrador (admin)
- Acceso completo a todas las funcionalidades
- Gestión de usuarios
- Auditoría del sistema
- Restauración de integridad

### Operario
- Calibración de instrumentos
- Gestión de datos de calibración
- Generación de informes

### Visor
- Solo consulta de datos
- Sin capacidad de modificación

## 📁 Estructura del Proyecto

```
metrologia-v02-github/
├── main.py                 # Aplicación principal
├── requirements.txt        # Dependencias Python
├── README.md              # Este archivo
├── config/                # Configuración del sistema
├── core/                  # Módulos centrales
│   ├── logger.py          # Sistema de logging y auditoría
│   ├── seguridad.py       # Funciones de seguridad e integridad
│   ├── pdf_generator.py   # Generación de informes PDF
│   ├── grafica_generator.py # Gráficos de análisis
│   ├── session_manager.py  # Gestión de sesiones
│   └── indices.py         # Generación de índices
├── gui/                   # Interfaz gráfica
│   ├── styles.py          # Estilos CSS de la aplicación
│   ├── login_dialog.py    # Diálogo de inicio de sesión
│   ├── element_window.py  # Ventana de elementos
│   ├── calibration_window.py # Ventana de calibración
│   ├── gestion_usuarios.py # Gestión de usuarios
│   └── auditoria.py       # Ventana de auditoría
├── data/                  # Datos de la aplicación
│   ├── instrumentos/      # Datos de instrumentos por familia
│   ├── patrones/          # Datos de patrones
│   └── usuarios.json      # Base de datos de usuarios
├── hashes_vault.json      # Vault de integridad de datos
├── metrologia_log.json    # Log de auditoría del sistema
└── metrologia_log.hash    # Hash de verificación del log
```

## 🔐 Seguridad

El sistema implementa múltiples capas de seguridad:

- **Hash Vault**: Verificación de integridad de todos los archivos JSON
- **Log de Auditoría**: Registro completo de todas las acciones
- **Sistema de Sesiones**: Control de acceso y seguimiento de usuarios
- **Verificación de Integridad**: Detección de modificaciones no autorizadas

## 📊 Funcionalidades Técnicas

### Sistema de Calibración
- Registro de puntos de calibración con múltiples lecturas
- Cálculo automático de medias, errores e incertidumbres
- Evaluación de conformidad según criterios establecidos
- Trazabilidad completa con patrones certificados

### Análisis de Datos
- Gráficos de dispersión (velas) para análisis de tendencias
- Cálculos estadísticos automáticos
- Visualización del comportamiento en rango completo

### Generación de Informes
- Informes PDF profesionales con formato estándar
- Inclusión de gráficos de análisis
- Datos completos de trazabilidad
- Numeración automática de informes (ICI-ID-YYYYMMDD)

## 🛠️ Mantenimiento

### Respaldo de Datos
- Copiar regularmente la carpeta `data/`
- Incluir `hashes_vault.json` y `metrologia_log.json`
- Verificar integridad periódicamente

### Actualización del Sistema
- Mantener actualizadas las dependencias con `pip install -r requirements.txt --upgrade`
- Verificar compatibilidad de versiones de PyQt6

## 📝 Registro de Cambios

### Versión 2026
- Implementación completa del sistema de gestión
- Interfaz moderna con tema oscuro estilo VS Code
- Sistema de auditoría y seguridad avanzado
- Generación de informes PDF con gráficos integrados
- Gestión multiusuario con roles definidos

## 🐛 Reporte de Problemas

Para reportar problemas o solicitar mejoras:
1. Verificar el log de auditoría para identificar el problema
2. Documentar los pasos para reproducir el error
3. Incluir capturas de pantalla si es posible

## 📄 Licencia

Este proyecto está bajo la licencia GNU GPL v3.
​Libertad de uso: Puedes clonar, estudiar y modificar el código libremente.
​Derivación responsable: Si modificas este software y lo distribues, debes mantener la misma licencia y compartir el código fuente de tus cambios.

## 👥 Desarrollo

- **Arquitectura**: PyQt6 para interfaz, Python vanilla para lógica de negocio
- **Base de Datos**: Sistema de archivos JSON con integridad verificada
- **Gráficos**: matplotlib para análisis visual
- **Informes**: fpdf2 para generación de PDFs

---

**Metrology Core 2026** - Sistema de Gestión de Activos de Metrología
