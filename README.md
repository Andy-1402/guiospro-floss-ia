# GUIOSPRO_FLOSS

Sistema de evaluación de adopción de software FLOSS (método GUIOSAD).

## Ejecutar en local

```bash
pip install -r requirements.txt
streamlit run app.py
```

Abrir `http://localhost:8501`

## Usuarios demo

| Usuario | Contraseña |
|---------|------------|
| decisor | Decisor2025! |
| consultor | Consultor2025! |
| admin | Admin2025! |

Base de datos: SQLite en `data/guiospro.db` (se crea automáticamente).

## Configurar acceso en producción

Para Streamlit Community Cloud o un servidor, define estas variables de entorno antes de iniciar la app:

```bash
GUIOSPRO_DEMO_USERNAME=operador
GUIOSPRO_DEMO_PASSWORD=una_clave_segura
GUIOSPRO_DEMO_ROLE=decisor
GUIOSPRO_DEMO_NAME=Operador Produccion
GUIOSPRO_DEMO_EMAIL=operador@tu-dominio.com
```

En Streamlit Cloud puedes cargarlas como secrets con el mismo nombre. Si esas variables existen, la app crea o actualiza ese usuario al iniciar.
