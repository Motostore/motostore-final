from fastapi import APIRouter
import httpx
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/danlipagos/balance")
async def get_danlipagos_balance():
    url = "https://192.142.2.85/service/api"
    params = {"key": "6286HWW0081794", "action": "saldos"}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, verify=False)

    if response.status_code == 200:
        data = response.json()
        return JSONResponse(content={"balance": data["balance"], "currency": "VES"})
    else:
        return JSONResponse(content={"error": "Error al obtener el saldo"}, status_code=502)
