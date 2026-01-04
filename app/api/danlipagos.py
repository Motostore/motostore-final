import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/danlipagos/balance")
async def get_danlipagos_balance():
    # URL y Datos
    url = "https://192.142.2.85/service/api"
    params = {"key": "6286HWW0081794", "action": "saldos"}

    print(f"--- INTENTANDO CONECTAR A DANLIPAGOS: {url} ---")

    try:
        # TIMEOUT: Si tarda mas de 10 segundos, cortamos para no colgar el server
        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            response = await client.get(url, params=params)
        
        # Imprimimos lo que respondieron para verlo en los logs si hace falta
        print(f"--- RESPUESTA RECIBIDA: {response.status_code} ---")

        if response.status_code == 200:
            data = response.json()
            # Verificamos si realmente llego el saldo
            balance = data.get("balance", "0.00")
            return JSONResponse(content={"balance": balance, "currency": "VES"})
        else:
            return JSONResponse(
                content={"error": f"Proveedor respondio status {response.status_code}", "balance": "0.00"}, 
                status_code=502
            )

    except httpx.ConnectTimeout:
        print("--- ERROR: TIEMPO DE ESPERA AGOTADO (TIMEOUT) ---")
        return JSONResponse(content={"error": "Timeout conectando al proveedor", "balance": "0.00"}, status_code=504)
        
    except Exception as e:
        # AQUI CAPTURAMOS EL ERROR 500 PARA QUE NO EXPLOTE
        print(f"--- ERROR GRAVE CONECTANDO: {str(e)} ---")
        return JSONResponse(content={"error": str(e), "balance": "0.00"}, status_code=500)