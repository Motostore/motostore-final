from fastapi import APIRouter, Depends, HTTPException
import requests
import os
from app.api.auth import get_current_active_user

router = APIRouter()

@router.get("/balances")
def get_providers_balances(
    current_user: dict = Depends(get_current_active_user)
):
    # Solo admins pueden ver saldo real del proveedor
    if current_user.get("role") not in ["SUPERUSER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    balances = {
        "legion": 0.0,
        "danlipagos": 0.0
    }

    # --- 1. CONSULTAR LEGION (MARKETING) ---
    try:
        legion_key = os.getenv("LEGION_API_KEY")
        if legion_key:
            # URL Estándar de servicios SMM (ajusta si usas otra)
            # Intentamos la consulta de balance estándar
            url = "https://marketing.legion-developer.net/api/v2"
            res = requests.post(url, json={"key": legion_key, "action": "balance"}, timeout=4)
            if res.status_code == 200:
                data = res.json()
                # Legion suele devolver {"balance": "12.50", "currency": "USD"}
                val = data.get("balance", 0)
                balances["legion"] = float(val)
    except Exception as e:
        print(f"Error check Legion: {e}")

    # --- 2. CONSULTAR DANLIPAGOS ---
    try:
        # Usamos variables de entorno para seguridad
        danli_user = os.getenv("DANLI_USER", "MOTORESTORE") 
        danli_pass = os.getenv("DANLI_PASSWORD") # Asegurate de poner esto en Render
        
        if danli_user and danli_pass:
            url = "http://192.142.2.85/api/index.php"
            payload = {
                "user": danli_user,
                "password": danli_pass,
                "action": "BALANCE"
            }
            res = requests.post(url, json=payload, timeout=4)
            if res.status_code == 200:
                data = res.json()
                # Ajustar según respuesta de Danli (suelen enviar "msg" o "balance")
                val = data.get("balance") or data.get("msg") or 0
                balances["danlipagos"] = float(val)
    except Exception as e:
        print(f"Error check Danlipagos: {e}")

    return balances