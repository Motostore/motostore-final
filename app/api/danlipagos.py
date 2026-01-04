import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/danlipagos/balance")
async def get_danlipagos_balance():
    # URL directa a la IP del proveedor
    url = "https://192.142.2.85/service/api"
    # Tus credenciales reales
    params = {"key": "6286HWW0081794", "action": "saldos"}

    async with httpx.AsyncClient() as client:
        # verify=False es vital aquí porque estamos usando una IP directa
        response = await client.get(url, params=params, verify=False)

    if response.status_code == 200:
        data = response.json()
        # Retornamos lo que el frontend necesita
        return JSONResponse(content={"balance": data.get("balance", "0.00"), "currency": "VES"})
    else:
        print(f"Error Danlipagos: {response.status_code}")
        return JSONResponse(content={"error": "Error al obtener el saldo"}, status_code=502)