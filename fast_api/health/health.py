from __future__ import annotations

from fastapi import APIRouter
from core.config.tenants import TenantConfig


router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def health():
    # -> Endpoint simples de saúde/monitoramento.
    # -> Retorna status e configuração atual do tenant (id + provider).
    return {"status": "ok"}

