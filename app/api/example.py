from fastapi import APIRouter

router = APIRouter()

@router.get("/hola")
def hola():
    return {"mensaje": "Backend Python funcionando correctamente 🙌"}
