from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# ... (mantén tus importaciones de app.api tal cual las tienes)
from app.api import (
    example, users, auth, products, categories, customers, wallet,
    payment_methods, marketing, recharges, licenses, dashboard, streaming,
    payments, orders, guest, me, company, notifications, roles, addresses,
    phones, location, exchange, social, transactions, danlipagos, reports,
    withdrawals, announcements,
)
from app.core.database import init_db

app = FastAPI(title="Backend Motostore")

# --- CONFIGURACIÓN CORS FINAL (A PRUEBA DE FALLOS) ---
# Usamos allow_origins=["*"] para permitir a TODO el mundo.
# Ponemos allow_credentials=False para evitar conflictos de seguridad con el *.
# Como enviamos el token en el Header "Authorization", esto funcionará igual.

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # <--- PERMITE TODO (Localhost, Vercel, Tu Web)
    allow_credentials=False, # <--- DESACTIVADO para que el * funcione sin errores
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=600,
)

@app.on_event("startup")
def on_startup():
    try:
        init_db()
        print("--- DB INICIALIZADA ---")
    except Exception as e:
        print(f"--- ERROR DB: {e}")

# ... (El resto de tus rutas router siguen igual, no las toques)
app.include_router(products.router, prefix="/api/v1/products", tags=["products"])
app.include_router(streaming.router, prefix="/api/v1/streaming", tags=["products"])
# ... etc ...
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
# ...

@app.get("/")
def root():
    return {"status": "ok", "message": "Backend Funcionando 🚀"}