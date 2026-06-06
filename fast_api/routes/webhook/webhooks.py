from __future__ import annotations

import hashlib
import hmac

from sqlalchemy.orm import Session

from fastapi import APIRouter ,Request, Header, HTTPException, Query,  Depends
from fastapi.responses import PlainTextResponse
from fast_api.core.config.configapi import settings
from fast_api.redis.message_buffer import buffer_message
from fast_api.redis.message_dedupe import dedupe_check_and_mark
from fast_api.utils.message import extract_message_evolution, is_group, extract_message_meta
from fast_api.core.config.tenants import tenant_service
from fast_api.core.database.conection.conection_orm import get_db

from fast_api.core.database.model.base_tenant.tenantBase import Tenant as TenantModel

router = APIRouter(prefix="/webhook", tags=["webhook"])



def _verify_meta_signature(raw_body: bytes, signature_header: str | None, app_secret: str | None) -> None:
    """Validate X-Hub-Signature-256 header for Meta Cloud webhook."""
    if not app_secret:
        raise HTTPException(
            status_code=500,
            detail="Configuração de segurança (Secret) ausente para este tenant."
        )

    if not signature_header:
        raise HTTPException(
            status_code=401,
            detail="Missing signature"
        )

    # Expected format: sha256=<hex>
    try:
        algo, sent = signature_header.split("=", 1)
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid signature"
        )

    if algo.lower() != "sha256" or not sent:
        raise HTTPException(
            status_code=401,
            detail="Invalid signature"
        )

    mac = hmac.new(
        app_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(mac, sent):
        raise HTTPException(status_code=401, detail="Invalid signature")


@router.post("/evolution")
async def webhook_evolution(
        request: Request,
        db: Session = Depends(get_db)
):
    # -> Lê o JSON da requisição (payload enviado pela Evolution).
    payload = await request.json()

    tenant_id = payload.get("instance")
    tenant_db = (
        db.query(TenantModel)
          .filter(
            TenantModel.id == tenant_id,
                      TenantModel.ativo == True
          )
          .first()
    )

    if not tenant_db:
        raise HTTPException(status_code=404, detail="Tenant não encontrado ou inativo")

    conf = tenant_service.build_config(
        tenant_id=tenant_db.id,
        name=tenant_db.nome_fantasia,
        provider=tenant_db.whatsapp_provider,
        extra_configs=tenant_db.provider_config
    )

    if conf.provider != "evolution":
        raise HTTPException(status_code=400, detail="Este tenant não utiliza Evolution API.")


    chat_id, text, message_id = extract_message_evolution(payload)

    if not chat_id or not text or is_group(chat_id):
        return {"status": "ignored"}

    if message_id:
        ok = await dedupe_check_and_mark(conf.id, message_id)
        if not ok:
            return {"status": "duplicate_ignored"}


    await buffer_message(tenant_id=conf.id, chat_id=chat_id, message=text)


    return {"status": "ok"}


@router.get("/{tenant_id}/meta")
async def webhook_meta_verify(
    tenant_id: str,
    db: Session = Depends(get_db),

    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
):
    print(f"verify token 1{settings.META_VERIFY_TOKEN}")
    # Aqui o Verify Token pode ser global ou específico por Tenant
    # Se for específico, buscamos no banco:
    tenant_db = db.query(TenantModel).filter(TenantModel.id == tenant_id).first()

    # Supondo que você salve o verify_token de cada lanchonete no banco:
    expected_token = tenant_db.meta_verify_token if tenant_db else settings.META_VERIFY_TOKEN

    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        return PlainTextResponse(hub_challenge)
    print(f"verify token {settings.META_VERIFY_TOKEN}")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/{tenant_id}/meta")
async def webhook_meta(
        tenant_id: str,
        request: Request,
        db: Session = Depends(get_db),
        x_hub_signature_256: str | None = Header(default=None, alias="X-Hub-Signature-256")
):
    tenant_db = db.query(TenantModel).filter(TenantModel.id == tenant_id).first()
    if not tenant_db or tenant_db.whatsapp_provider != "meta":
        raise HTTPException(status_code=400, detail="Configuração inválida.")

    raw = await request.body()
    _verify_meta_signature(raw, x_hub_signature_256, tenant_db.meta_app_secret)
    payload = await request.json()

    chat_id, text, message_id = extract_message_meta(payload)
    if not chat_id or not text:
        return {"status": "ignored"}

    if message_id:
        ok = await dedupe_check_and_mark(tenant_db.id, message_id)
        if not ok:
            return {"status": "duplicate_ignored"}

    await buffer_message(tenant_id=tenant_db.id, chat_id=chat_id, message=text)
    return {"status": "ok"}
