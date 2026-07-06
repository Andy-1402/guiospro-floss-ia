# GUIOSPRO_FLOSS — Guía técnica del sistema

Documento de referencia: por qué no se usa HTML estático, arquitectura por archivos y lógica de cada módulo.

---

## 1. Por qué no usamos HTML como interfaz principal

### 1.1 Qué había al inicio del proyecto

La primera versión del software utilizaba:

| Componente | Función |
|------------|---------|
| **Flexx** (`main.py`) | Framework de interfaz en Python que generaba UI en el navegador |
| **`guiosad.html`** | Archivo HTML muy grande (exportación / vista legada) |
| **CSV** (`factors.csv`, `guiosad_data.csv`) | Catálogo GUIOSAD sin base de datos |

Era una aplicación con **muchos formularios** (factores, subfactores, escalas 1–4, FODA, recomendaciones). Mantener eso en HTML estático + lógica separada complicaba correcciones y evolución.

### 1.2 Qué se usa ahora

| Antes | Ahora |
|-------|--------|
| HTML estático + Flexx | **Streamlit** (`app.py`) |
| Archivos `.html` en el repositorio | **Python** describe pantallas; el HTML lo genera Streamlit en tiempo de ejecución |
| Sin persistencia unificada | **SQLite** + capa `db/` y `services/` |

### 1.3 Razones técnicas de la decisión

1. **Muchos formularios y pasos** — Login, historial, pasos 1–6, borrador, informes. En Streamlit cada control (`st.form`, `st.selectbox`, `st.slider`) se define en pocas líneas de Python.

2. **Un solo lenguaje** — Pantalla, reglas GUIOSAD y base de datos en **Python**. Menos archivos que coordinar (HTML + JS + API + backend).

3. **Menos errores de integración** — La versión Flexx tenía bugs de etiquetas y referencias; al separar `engine.py` (lógica) de `app.py` (UI) el método GUIOSAD quedó más claro y testeable.

4. **Despliegue sencillo** — `streamlit run app.py` y Streamlit Community Cloud; no hace falta servidor de archivos estáticos ni plantillas HTML.

5. **Misma experiencia en navegador** — El usuario sigue viendo una **aplicación web**. La diferencia es **quién escribe el HTML**: el desarrollador (antes) vs. Streamlit (ahora).

### 1.4 ¿Significa que no hay HTML en absoluto?

**No.** El navegador siempre renderiza HTML. En este proyecto:

- **Streamlit** genera la estructura de la página automáticamente.
- **`ui/styles.py`** aporta **CSS** (apariencia).
- En algunos puntos (`app.py`, `ui/components.py`) hay **fragmentos HTML** pequeños (títulos del login, tarjetas) mediante `st.markdown(..., unsafe_allow_html=True)`. Son detalles visuales, no una aplicación entera en HTML.

### 1.5 Conclusión para documentación académica

> La interfaz de GUIOSPRO_FLOSS se implementó con el framework **Streamlit**, que construye dinámicamente la capa de presentación en el navegador a partir de código **Python**, en lugar de mantener plantillas **HTML** estáticas. Esta decisión responde a la complejidad del flujo de evaluación (múltiples formularios y pasos del método GUIOSAD), a la necesidad de integración directa con la base de datos y a la simplificación del despliegue y mantenimiento del sistema.

---

## 2. Arquitectura general (capas)

```
┌─────────────────────────────────────────────────────────────┐
│  NAVEGADOR (HTML/CSS/JS generado por Streamlit)             │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│  PRESENTACIÓN — app.py, ui/components.py, ui/styles.py       │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│  AUTENTICACIÓN — auth/service.py                            │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│  LÓGICA GUIOSAD — engine.py + guiosad.py (catálogo)         │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│  SERVICIOS — evaluation_repo, catalog, export_report, audit │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│  PERSISTENCIA — db/models, session, config, bootstrap       │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│  ALMACENAMIENTO — SQLite (data/guiospro.db)                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Flujo principal de la aplicación

1. El usuario ejecuta `streamlit run app.py`.
2. `main()` llama a `ensure_database_ready()` → crea tablas, importa CSV si hace falta, crea usuarios demo.
3. Si no hay sesión → **pantalla de login** → `authenticate()`.
4. Tras login → **Dashboard** o **Historial** según menú lateral.
5. Al **crear o abrir** una evaluación → se carga `EvaluationEngine` desde BD (`engine_from_evaluation`).
6. **Pasos 1–2** — factores (importancia, alcance) → guardar borrador → `save_engine_to_db`.
7. **Pasos 3–4** — subfactores por factor relevante → ponderación y FODA preliminar.
8. **Pasos 5–6** — revisión FODA, completar → recomendación A/B/C → `export_pdf` / `export_excel`.

---

## 4. Descripción y lógica de cada archivo

### 4.1 Raíz del proyecto

| Archivo | Qué hace | Lógica principal |
|---------|----------|------------------|
| **`app.py`** | **Punto de entrada** de la aplicación Streamlit. Orquesta pantallas, sesión y navegación. | `main()` inicializa BD y `session_state`. Según `st.session_state.page` muestra login, dashboard, historial, factores, subfactores o FODA. Llama a servicios para guardar y exportar. Mantiene caché del motor de evaluación (`get_engine`). |
| **`engine.py`** | **Cerebro del método GUIOSAD** sin depender de la UI. | Clase `EvaluationEngine`: importancia relativa, relevancia de factores, media de subfactores, clasificación FODA (Fortaleza/Oportunidad/Debilidad/Amenaza), recomendaciones A, B y C. No accede a Streamlit ni a SQL directamente. |
| **`guiosad.py`** | **Modelo del catálogo** desde CSV (dimensiones, 18 factores, 61 subfactores). | Clase `Guiosad` lee `guiosad_data.csv` y `factors.csv`, arma objetos `Dimension`, `Factor`, `Subfactor` en memoria. Usado al inicio o como referencia de etiquetas (`levels_lbls`, `sub_levels_lbls`). En evaluaciones guardadas el catálogo viene de la BD vía `DbGuiosadModel`. |
| **`factors.csv`** | Datos: importancia sugerida y alcance por factor. | Entrada para `catalog.py` / `Guiosad`. |
| **`guiosad_data.csv`** | Datos: dimensión, factor y texto de cada subfactor. | Entrada para poblar catálogo en BD. |
| **`requirements.txt`** | Dependencias pip del proyecto. | streamlit, sqlalchemy, pandas, bcrypt, openpyxl, reportlab, python-dotenv. |
| **`.env`** | Variables de entorno (no subir a GitHub). | `GUIOSPRO_DB_MODE=local` → SQLite en `data/guiospro.db`. |
| **`.env.example`** | Plantilla de configuración. | Documenta variables disponibles. |
| **`.streamlit/config.toml`** | Configuración del servidor Streamlit (tema, puerto, etc.). | Ajustes de la app al ejecutar `streamlit run`. |

---

### 4.2 Carpeta `auth/`

| Archivo | Qué hace | Lógica principal |
|---------|----------|------------------|
| **`auth/service.py`** | **Login y seguridad de contraseñas.** | `authenticate(username, password)` busca usuario activo en BD, verifica hash con **bcrypt**. Devuelve `AuthUser` con rol y permisos (`puede_editar`, `solo_lectura`). `hash_password` se usa al crear usuarios en bootstrap. |

---

### 4.3 Carpeta `db/`

| Archivo | Qué hace | Lógica principal |
|---------|----------|------------------|
| **`db/config.py`** | **Define cómo conectar a la base de datos.** | Lee `.env`. Si `GUIOSPRO_DB_MODE=local` → URL SQLite en `data/guiospro.db`. Si postgres → URL PostgreSQL. Funciones `is_sqlite()`, `storage_label()`. |
| **`db/models.py`** | **Modelo relacional (ORM SQLAlchemy).** | 9 tablas: `organizaciones`, `usuarios`, `dimensiones`, `factores`, `subfactores`, `evaluaciones`, `evaluacion_factores`, `evaluacion_subfactores`, `auditoria`. Define columnas, FK y relaciones. |
| **`db/session.py`** | **Motor y sesiones de base de datos.** | `create_engine`, `get_session()`, `init_tables()` → `Base.metadata.create_all()`. En SQLite activa `PRAGMA foreign_keys=ON`. |
| **`db/bootstrap.py`** | **Arranque automático al abrir la app.** | `ensure_database_ready()`: crea tablas, importa catálogo si está vacío (`seed_catalog_if_empty`), crea/actualiza usuarios demo (`seed_users`). Solo corre una vez por proceso (caché interna). |

---

### 4.4 Carpeta `services/`

| Archivo | Qué hace | Lógica principal |
|---------|----------|------------------|
| **`services/catalog.py`** | **Poblar catálogo GUIOSAD en BD desde CSV.** | Si no hay factores en BD, lee los CSV y inserta dimensiones, factores y subfactores. Se ejecuta desde bootstrap. |
| **`services/evaluation_repo.py`** | **CRUD de evaluaciones** — puente entre BD y `EvaluationEngine`. | `create_evaluation`, `list_evaluations`, `engine_from_evaluation` (carga respuestas a memoria), `save_engine_to_db` (persiste factores/subfactores, calcula FODA), `get_evaluation_detail`. `DbGuiosadModel` adapta filas de BD al formato que espera `EvaluationEngine`. |
| **`services/export_report.py`** | **Informes PDF y Excel** para el cliente. | Lee evaluación + motor, arma tablas con factores, FODA y recomendación. `export_pdf` (reportlab), `export_excel` (openpyxl). |
| **`services/audit.py`** | **Trazabilidad.** | `log_action()` inserta fila en `auditoria` (quién, qué acción, evaluación, detalle JSON). |

---

### 4.5 Carpeta `ui/`

| Archivo | Qué hace | Lógica principal |
|---------|----------|------------------|
| **`ui/styles.py`** | **Hoja de estilos CSS** inyectada en todas las páginas. | Constante `CUSTOM_CSS`: colores corporativos, tarjetas KPI, sidebar, formularios. Se aplica con `st.markdown(CUSTOM_CSS, unsafe_allow_html=True)` en `app.py`. |
| **`ui/components.py`** | **Bloques reutilizables de interfaz.** | Marca en sidebar, tarjeta de usuario, KPIs del dashboard, lista de evaluaciones recientes. Usa `list_evaluations` para estadísticas. |

---

### 4.6 Generado en ejecución (no va en Git)

| Ruta | Qué es |
|------|--------|
| **`data/guiospro.db`** | Base SQLite con organizaciones, usuarios, catálogo, evaluaciones y auditoría. |
| **`__pycache__/`** | Bytecode Python (temporal). |

---

## 5. Lógica del método GUIOSAD (resumen en `engine.py`)

| Paso | Lógica |
|------|--------|
| Importancia del decisor | Escala 1–4 por factor. |
| Importancia relativa | Media entre importancia sugerida (catálogo) e importancia del decisor → Irrelevante / Opcional / Importante / Fundamental. |
| Factor relevante | Si importancia relativa no es “Irrelevante”, se evalúan subfactores. |
| Subfactores | Escala 1–4; **ponderación global** = media de valores. |
| FODA | Si alcance **Interno** y ponderación ≥ 3 → Fortaleza; &lt; 3 → Debilidad. Si **Externo** → Oportunidad / Amenaza. |
| Recomendación | Reglas A, B, C según combinación de FODA en factores relevantes. |

---

## 6. Pantallas de `app.py` (mapa UI)

| Función | Pantalla |
|---------|----------|
| `page_login` | Acceso usuario/contraseña |
| `page_dashboard` | KPIs y resumen ejecutivo |
| `page_historial` | Lista, nueva evaluación, re-evaluación |
| `page_factores` | Pasos 1–2 |
| `page_subfactores` | Pasos 3–4 |
| `page_foda` | Pasos 5–6, completar, descargar informes |
| `render_sidebar` | Menú lateral y cierre de sesión |
| `main` | Enrutador según sesión y página activa |

---

## 7. Tabla resumen: archivo → responsabilidad

| Archivo | Una línea |
|---------|-----------|
| `app.py` | Muestra pantallas y conecta usuario con servicios |
| `engine.py` | Calcula GUIOSAD, FODA y recomendación |
| `guiosad.py` | Catálogo desde CSV (estructura GUIOSAD) |
| `auth/service.py` | Login y roles |
| `db/config.py` | Ruta a SQLite o PostgreSQL |
| `db/models.py` | Definición de tablas |
| `db/session.py` | Conexión y creación de tablas |
| `db/bootstrap.py` | Inicialización al arrancar |
| `services/catalog.py` | CSV → BD (catálogo) |
| `services/evaluation_repo.py` | Guardar/cargar evaluaciones |
| `services/export_report.py` | PDF y Excel |
| `services/audit.py` | Registro de acciones |
| `ui/styles.py` | Diseño visual (CSS) |
| `ui/components.py` | Piezas de UI reutilizables |

---

*GUIOSPRO_FLOSS — Método GUIOSAD v0.1.2 — Documento técnico interno*
