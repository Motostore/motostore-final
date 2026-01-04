from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importamos todos los routers
from app.api import (
    example,
    users,
    auth,
    products,
    categories,
    customers,
    wallet,
    payment_methods,
    marketing,
    recharges,
    licenses,
    dashboard,
    streaming,
    payments,
    orders,
    guest,
    me,
    # profile,      <-- COMENTADO PARA EVITAR ERROR 503
    company,
    notifications,
    roles,
    addresses,
    phones,
    location,
    exchange,
    # admin_users,  <-- COMENTADO PARA EVITAR ERROR 503
    social,
    transactions,
    danlipagos,
    reports,
    withdrawals,
    announcements,
)
from app.core.database import init_db

# ----------- 1. CREAR LA APP FASTAPI -----------

app = FastAPI(title="Backend Motostore en Python")

# ----------- 2. MIDDLEWARE (CORS) CORRECTO PARA PRODUCCIÓN -----------

origins = [
    "https://motostorellc.com",
    "https://www.motostorellc.com",
    "https://motostore-final.vercel.app",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=600,
)

# ----------- 3. EVENTO DE ARRANQUE -----------

@app.on_event("startup")
def on_startup():
    try:
        init_db()
        print("--- BASE DE DATOS INICIALIZADA CORRECTAMENTE ---")
    except Exception as e:
        print(f"--- ALERTA: Error inicializando DB: {e}")

# ----------- 4. INCLUSIÓN DE RUTAS -----------

app.include_router(products.router, prefix="/api/v1/products", tags=["products"])
app.include_router(categories.router, prefix="/api/v1/categories", tags=["products"])
app.include_router(marketing.router, prefix="/api/v1/marketing", tags=["products"])
app.include_router(recharges.router, prefix="/api/v1/recharges", tags=["products"])
app.include_router(licenses.router, prefix="/api/v1/licenses", tags=["products"])
app.include_router(streaming.router, prefix="/api/v1/streaming", tags=["products"])
app.include_router(exchange.router, prefix="/api/v1/exchange", tags=["products"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["products"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(orders.router, prefix="/api/v1/orders", tags=["orders"])

app.include_router(wallet.router, prefix="/api/v1/wallet", tags=["wallet"])
app.include_router(payment_methods.router, prefix="/api/v1/payment-methods", tags=["wallet"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(withdrawals.router, prefix="/api/v1/withdrawals", tags=["admin"])

# app.include_router(admin_users.router, prefix="/api/v1/admin/users", tags=["admin"])  <-- DESACTIVADO
app.include_router(social.router, prefix="/api/v1/social", tags=["social"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["user"])
app.include_router(roles.router, prefix="/api/v1/roles", tags=["admin"])
app.include_router(addresses.router, prefix="/api/v1/addresses", tags=["user"])
app.include_router(phones.router, prefix="/api/v1/phones", tags=["user"])
app.include_router(location.router, prefix="/api/v1/locations", tags=["utils"])
app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["user"])
app.include_router(me.router, prefix="/api/v1/me", tags=["user"])
# app.include_router(profile.router, prefix="/api/v1/profile", tags=["user"])  <-- DESACTIVADO
app.include_router(company.router, prefix="/api/v1/company", tags=["admin"])
app.include_router(customers.router, prefix="/api/v1/customers", tags=["admin"])

app.include_router(announcements.router, prefix="/api/v1", tags=["announcements"])

app.include_router(example.router, prefix="/api", tags=["example"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(guest.router, prefix="/api/v1/guest", tags=["guest"])
app.include_router(danlipagos.router, prefix="/api/v1", tags=["danlipagos"])

@app.get("/")
def root():
    return {"status": "ok", "message": "Backend COMPLETO en Python listo 🚀"}
