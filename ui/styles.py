CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', system-ui, sans-serif;
    }

    /* Ocultar menú hamburguesa extra y footer streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {background: transparent;}

    /* ─── Sidebar ejecutivo ─── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0c1222 0%, #151d32 45%, #1a2744 100%) !important;
        border-right: 1px solid rgba(201, 162, 39, 0.15);
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.25rem;
    }
    [data-testid="stSidebar"] .stMarkdown, 
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span {
        color: #e2e8f0 !important;
    }
    [data-testid="stSidebar"] .stCaption {
        color: #94a3b8 !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.08);
    }
    [data-testid="stSidebar"] .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #c9a227 0%, #a67c00 100%) !important;
        border: none !important;
        color: #0c1222 !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="secondary"] {
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        color: #f1f5f9 !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.25);
    }

    /* Radio / nav en sidebar */
    [data-testid="stSidebar"] [role="radiogroup"] label {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 8px;
        padding: 0.5rem 0.75rem;
        margin-bottom: 4px;
    }

    /* ─── Área principal ─── */
    .block-container {
        padding-top: 1.5rem;
        max-width: 1400px;
    }

    .exec-brand {
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 1.5rem;
        font-weight: 700;
        color: #f8fafc;
        letter-spacing: 0.02em;
        margin: 0;
        line-height: 1.2;
    }
    .exec-brand-sub {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.18em;
        color: #c9a227;
        margin-top: 0.25rem;
    }
    .exec-user-card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .exec-user-name { color: #f8fafc; font-weight: 600; font-size: 0.95rem; }
    .exec-user-role {
        display: inline-block;
        background: rgba(201, 162, 39, 0.2);
        color: #e8c547;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        margin-top: 0.35rem;
    }

    .dash-hero {
        background: linear-gradient(135deg, #0c1222 0%, #1e3a5f 60%, #0f766e 100%);
        border-radius: 16px;
        padding: 2rem 2.5rem;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 12px 40px rgba(12, 18, 34, 0.35);
        border-bottom: 3px solid #c9a227;
    }
    .dash-hero h1 {
        font-family: 'Playfair Display', Georgia, serif;
        color: white !important;
        font-size: 2rem;
        margin: 0 0 0.5rem 0;
        font-weight: 700;
    }
    .dash-hero p { color: rgba(255,255,255,0.85); margin: 0; font-size: 1rem; }

    .kpi-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
        border-top: 3px solid #c9a227;
        height: 100%;
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: 700;
        color: #0c1222;
        line-height: 1.1;
    }
    .kpi-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #64748b;
        font-weight: 600;
        margin-top: 0.35rem;
    }
    .kpi-delta { font-size: 0.8rem; color: #0d9488; font-weight: 500; }

    .step-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #c9a227;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
    }
    .step-card h3 { color: #0c1222; margin-top: 0; font-size: 1.1rem; font-weight: 700; }

    .eval-header {
        background: linear-gradient(90deg, #0c1222, #1e3a5f);
        border-radius: 12px;
        padding: 1.25rem 1.75rem;
        color: white;
        margin-bottom: 1rem;
        border-left: 4px solid #c9a227;
    }
    .eval-header h2 { color: white !important; margin: 0; font-size: 1.35rem; }
    .eval-header p { color: rgba(255,255,255,0.8); margin: 0.35rem 0 0 0; font-size: 0.9rem; }

    .action-panel {
        background: #f8fafc;
        border: 1px dashed #cbd5e1;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
    }

    .hist-panel {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1.5rem 2rem;
        box-shadow: 0 4px 24px rgba(15, 23, 42, 0.06);
    }
    .hist-row {
        border-bottom: 1px solid #f1f5f9;
        padding: 1rem 0;
    }
    .hist-row:last-child { border-bottom: none; }

    .badge-borrador { background: #fef3c7; color: #92400e; padding: 0.2rem 0.6rem; border-radius: 6px; font-size: 0.75rem; font-weight: 600; }
    .badge-completada { background: #d1fae5; color: #065f46; padding: 0.2rem 0.6rem; border-radius: 6px; font-size: 0.75rem; font-weight: 600; }

    .rec-success { background: #ecfdf5; border: 1px solid #6ee7b7; border-radius: 12px; padding: 1.25rem; color: #065f46; }
    .rec-warning { background: #fffbeb; border: 1px solid #fcd34d; border-radius: 12px; padding: 1.25rem; color: #92400e; }
    .rec-error { background: #fff1f2; border: 1px solid #fda4af; border-radius: 12px; padding: 1.25rem; color: #9f1239; }

    .login-hero {
        background: linear-gradient(135deg, #0c1222 0%, #1e3a5f 50%, #0f766e 100%);
        border-radius: 20px;
        padding: 3rem 2rem;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
        border-bottom: 4px solid #c9a227;
    }
    .login-hero h1 {
        font-family: 'Playfair Display', Georgia, serif;
        color: white !important;
        font-size: 2.5rem;
        margin: 0;
    }
</style>
"""
