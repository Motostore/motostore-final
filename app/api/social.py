# app/api/social.py
#
# Redes sociales de la empresa.
#
#   GET /api/v1/social/links

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()


class SocialLink(BaseModel):
    name: str
    url: str
    icon: str


@router.get("/links", response_model=List[SocialLink])
def get_social_links():
    return [
        SocialLink(name="Instagram", url="https://instagram.com/motostore", icon="instagram"),
        SocialLink(name="WhatsApp", url="https://wa.me/584000000000", icon="whatsapp"),
        SocialLink(name="Facebook", url="https://facebook.com/motostore", icon="facebook"),
    ]
