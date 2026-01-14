from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
import httpx
from app.api.auth import get_current_active_user

router = APIRouter()

# Nota: En main.py el prefijo ya es "/api/v1/danlipagos", 
# por eso aquí ponemos solo "/balance"
@router.get("/balance")
async def get_danlipagos_balance(current_user: dict = Depends(get_current_active_user)):
    
    # 1. SEGURIDAD: Solo Superuser o Admin pueden ver esto
    if current_user.get("role") not in ["SUPERUSER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="No tienes permiso para ver el saldo")

    # 2. TU LÓGICA DE CONEXIÓN (IP Directa + verify=False)
    url = "https://192.142.2.85/service/api"
    # Nota: Idealmente esta KEY debería ir en una variable de entorno, 
    # pero la dejamos aquí para que te funcione ya mismo.
    params = {"key": "6286HWW0081794", "action": "saldos"}

    print(f"--- [Back] Conectando a Danlipagos: {url} ---")

    try:
        # Usamos httpx.AsyncClient para no bloquear el servidor
        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            response = await client.get(url, params=params)
        
        print(f"--- [Back] Respuesta Danli: {response.status_code} ---")

        if response.status_code == 200:
            data = response.json()
            
            # Buscamos el saldo (a veces llega como 'balance', a veces como 'saldo')
            # Tu código original buscaba "balance", agregamos "saldo" por si acaso cambia.
            raw_balance = data.get("balance") or data.get("saldo") or "0.00"
            
            # Aseguramos que sea un número para que el frontend no falle
            try:
                final_balance = float(raw_balance)
            except:
                final_balance = 0.00

            return JSONResponse(content={"balance": final_balance, "currency": "VES"})
        else:
            print(f"--- [Back] Error Status: {response.text} ---")
            return JSONResponse(
                content={"error": f"Status {response.status_code}", "balance": 0.00}, 
                status_code=502
            )

    except httpx.ConnectTimeout:
        print("--- [Back] TIMEOUT Danlipagos ---")
        return JSONResponse(content={"error": "Timeout", "balance": 0.00}, status_code=504)
        
    except Exception as e:
        print(f"--- [Back] ERROR GRAVE: {str(e)} ---")
        return JSONResponse(content={"error": "Error interno", "balance": 0.00}, status_code=500)