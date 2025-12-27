# app/api/licenses.py
#
# Versión con datos de ejemplo.
# Paths usados:
#   /api/v1/license [...]
#   /api/v1/licenses
#   /api/v1/licenses/providers
#   /api/v1/license-providers

from fastapi import APIRouter, Query
from typing import Any, Dict, List

router = APIRouter()

_fake_licenses: List[Dict[str, Any]] = [
    {
        "id": 1,
        "name": "Licencia IPTV Básica",
        "client": "Cliente A",
        "active": True,
    },
    {
        "id": 2,
        "name": "Licencia IPTV Premium",
        "client": "Cliente B",
        "active": True,
    },
]

_fake_license_providers: List[Dict[str, Any]] = [
    {"id": 1, "name": "Proveedor Licencias A"},
    {"id": 2, "name": "Proveedor Licencias B"},
]


def page_from_list(items: List[Dict[str, Any]], page: int, elements: int) -> Dict[str, Any]:
    total = len(items)
    return {
        "content": items,
        "number": page,
        "size": elements,
        "totalElements": total,
        "totalPages": 1,
    }


# ---------- LICENSES (base /license) ----------

@router.get("/license")
def get_all_licenses(
    query: str = Query("", description="texto de búsqueda"),
    page: int = Query(0, ge=0),
    elements: int = Query(10, ge=1),
):
    """
    GET /api/v1/license
    """
    return page_from_list(_fake_licenses, page, elements)


@router.get("/license/client")
def get_all_licenses_by_client(
    query: str = Query("", description="texto de búsqueda"),
    page: int = Query(0, ge=0),
    elements: int = Query(10, ge=1),
):
    """
    GET /api/v1/license/client
    """
    return page_from_list(_fake_licenses, page, elements)


@router.get("/license/{id}")
def get_license_by_id(id: int):
    """
    GET /api/v1/license/{id}
    """
    for item in _fake_licenses:
        if item["id"] == id:
            return item
    return {"detail": f"License {id} no encontrada (datos de ejemplo)"}


@router.post("/license")
def create_license(body: Dict[str, Any]):
    new_id = max((l["id"] for l in _fake_licenses), default=0) + 1
    obj = {"id": new_id, **body}
    _fake_licenses.append(obj)
    return obj


@router.put("/license/{id}")
def update_license(id: int, body: Dict[str, Any]):
    for idx, item in enumerate(_fake_licenses):
        if item["id"] == id:
            updated = {**item, **body, "id": id}
            _fake_licenses[idx] = updated
            return updated
    return {"detail": f"License {id} no encontrada (datos de ejemplo)"}


@router.delete("/license/{id}")
def delete_license(id: int):
    for idx, item in enumerate(_fake_licenses):
        if item["id"] == id:
            _fake_licenses.pop(idx)
            return {"detail": f"License {id} eliminada (ejemplo en memoria)"}
    return {"detail": f"License {id} no encontrada (datos de ejemplo)"}


# ---------- ALIAS /licenses para el frontend ----------

@router.get("/licenses")
def get_all_licenses_alias(
    query: str = Query("", description="texto de búsqueda"),
    page: int = Query(0, ge=0),
    elements: int = Query(10, ge=1),
):
    """
    GET /api/v1/licenses
    Alias de /license
    """
    return page_from_list(_fake_licenses, page, elements)


# ---------- PROVIDERS ----------

@router.get("/license/provider")
def get_all_license_providers(
    query: str = Query("", description="texto de búsqueda"),
    page: int = Query(0, ge=0),
    elements: int = Query(10, ge=1),
):
    """
    GET /api/v1/license/provider
    """
    return page_from_list(_fake_license_providers, page, elements)


@router.get("/license/provider/available")
def get_all_license_providers_for_transactions():
    """
    GET /api/v1/license/provider/available
    """
    return _fake_license_providers


@router.get("/license/provider/{id}")
def get_license_provider_by_id(id: int):
    for item in _fake_license_providers:
        if item["id"] == id:
            return item
    return {"detail": f"LicenseProvider {id} no encontrado (datos de ejemplo)"}


@router.post("/license/provider")
def create_license_provider(body: Dict[str, Any]):
    new_id = max((p["id"] for p in _fake_license_providers), default=0) + 1
    obj = {"id": new_id, **body}
    _fake_license_providers.append(obj)
    return obj


@router.put("/license/provider/{id}")
def update_license_provider(id: int, body: Dict[str, Any]):
    for idx, item in enumerate(_fake_license_providers):
        if item["id"] == id:
            updated = {**item, **body, "id": id}
            _fake_license_providers[idx] = updated
            return updated
    return {"detail": f"LicenseProvider {id} no encontrado (datos de ejemplo)"}


@router.delete("/license/provider/{id}")
def delete_license_provider(id: int):
    for idx, item in enumerate(_fake_license_providers):
        if item["id"] == id:
            _fake_license_providers.pop(idx)
            return {"detail": f"LicenseProvider {id} eliminado (ejemplo en memoria)"}
    return {"detail": f"LicenseProvider {id} no encontrado (datos de ejemplo)"}


# ---------- Aliases extras para lo que pide el frontend ----------

@router.get("/licenses/providers")
def get_all_license_providers_alias():
    """
    GET /api/v1/licenses/providers
    Alias
    """
    return _fake_license_providers


@router.get("/license-providers")
def get_all_license_providers_alias2():
    """
    GET /api/v1/license-providers
    Otro alias
    """
    return _fake_license_providers


