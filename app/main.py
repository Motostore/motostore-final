from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import init_db

# 1. IMPORTACIONES (Traemos todos los archivos de tu carpeta api)
from app.api import (
    example, users, auth, products, categories, customers, wallet,
    payment_methods, marketing, recharges, licenses, dashboard, streaming,
    payments, orders, guest, me, company, notifications, roles, addresses,
    phones, location, exchange, social, transactions, danlipagos, reports,
    withdrawals, announcements, admin_users, admin_products
)

app = FastAPI(title="Backend Motostore")

# 2. CONFIGURACIÓN DE SEGURIDAD (CORS)
# Permite que tu Frontend en Vercel se conecte sin bloqueos.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=600,
)

# 3. INICIO DE BASE DE DATOS
@app.on_event("startup")
def on_startup():
    try:
        init_db()
        print("--- DB INICIALIZADA CORRECTAMENTE ---")
    except Exception as e:
        print(f"--- ERROR AL INICIAR DB: {e}")

# ==================================================================
# 4. CONEXIÓN DE RUTAS (ROUTERS) - AQUÍ ESTABA EL PROBLEMA
# ==================================================================

# --- Usuarios y Autenticación ---
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])  # ✅ ESTA ERA LA QUE FALTABA
app.include_router(me.router, prefix="/api/v1/me", tags=["me"])
app.include_router(roles.router, prefix="/api/v1/roles", tags=["roles"])
app.include_router(admin_users.router, prefix="/api/v1/admin/users", tags=["admin_users"])

# --- Productos y Ventas ---
app.include_router(products.router, prefix="/api/v1/products", tags=["products"])
app.include_router(admin_products.router, prefix="/api/v1/admin/products", tags=["admin_products"])
app.include_router(categories.router, prefix="/api/v1/categories", tags=["categories"])
app.include_router(orders.router, prefix="/api/v1/orders", tags=["orders"])
app.include_router(customers.router, prefix="/api/v1/customers", tags=["customers"])

# --- Finanzas y Wallet ---
app.include_router(wallet.router, prefix="/api/v1/wallet", tags=["wallet"])
app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["transactions"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(withdrawals.router, prefix="/api/v1/withdrawals", tags=["withdrawals"])
app.include_router(payment_methods.router, prefix="/api/v1/payment-methods", tags=["payment_methods"])
app.include_router(exchange.router, prefix="/api/v1/exchange", tags=["exchange"])
app.include_router(danlipagos.router, prefix="/api/v1/danlipagos", tags=["danlipagos"])

# --- Servicios Digitales ---
app.include_router(streaming.router, prefix="/api/v1/streaming", tags=["streaming"])
app.include_router(licenses.router, prefix="/api/v1/licenses", tags=["licenses"])
app.include_router(recharges.router, prefix="/api/v1/recharges", tags=["recharges"])

# --- Sistema, Utilidades y Marketing ---
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
app.include_router(announcements.router, prefix="/api/v1/announcements", tags=["announcements"])
app.include_router(company.router, prefix="/api/v1/company", tags=["company"])
app.include_router(location.router, prefix="/api/v1/location", tags=["location"])
app.include_router(addresses.router, prefix="/api/v1/addresses", tags=["addresses"])
app.include_router(phones.router, prefix="/api/v1/phones", tags=["phones"])
app.include_router(social.router, prefix="/api/v1/social", tags=["social"])
app.include_router(marketing.router, prefix="/api/v1/marketing", tags=["marketing"])
app.include_router(guest.router, prefix="/api/v1/guest", tags=["guest"])
app.include_router(example.router, prefix="/api/v1/example", tags=["example"])

# Ruta de prueba para verificar que el servidor está vivo
@app.get("/")
def root():
    return {"status": "ok", "message": "Backend Motostore Activo y Conectado 🚀"}