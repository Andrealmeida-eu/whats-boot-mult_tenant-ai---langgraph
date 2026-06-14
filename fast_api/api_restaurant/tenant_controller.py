from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.data.database.conection.conection_orm import get_db
from core.data.database.model.restaurant.auth import Usuario, Role
from core.data.database.model.base_tenant.tenantBase import Tenant

from core.security.auth import get_password_hash
from pydantic import BaseModel

from typing import Optional, Union, Literal

router = APIRouter(tags=["Sistema"])


class MetaConfig(BaseModel):
    verify_token: str
    app_secret: str
    phone_number_id: str
    access_token: str


class EvolutionConfig(BaseModel):
    instance_name: str
    instance_url: str
    global_apikey: str


class RegisterTenantSchema(BaseModel):
    tenant_id: str
    nome_fantasia: str
    admin_email: str
    admin_senha: str


    whatsapp_provider: Optional[Literal['meta', 'evolution']] = "evolution"
    provider_config: Optional[Union[MetaConfig, EvolutionConfig]] = None


@router.post("/registrar-lanchonete")
def registrar_lanchonete(
        payload: RegisterTenantSchema,
        db: Session = Depends(get_db)
):
    # 1. Verifica se o ID já existe
    if db.query(Tenant).filter(Tenant.id == payload.tenant_id).first():
        raise HTTPException(status_code=400, detail="Este ID de lanchonete já está em uso.")

    config_dit = None

    if payload.provider_config:
        config_dit = payload.provider_config.model_dump()
    # 2. Cria o Tenant
    novo_tenant = Tenant(
        id=payload.tenant_id,
        nome_fantasia=payload.nome_fantasia,
        whatsapp_provider=payload.whatsapp_provider,
        provider_config= config_dit,
        ativo=True
    )
    db.add(novo_tenant)

    # 3. Cria o Usuário Admin
    novo_admin = Usuario(
        tenant_id=payload.tenant_id,
        nome="Administrador",
        email=payload.admin_email,
        senha_hash=get_password_hash(payload.admin_senha),
        role=Role.ADMIN
    )
    db.add(novo_admin)

    db.commit()
    return {"message": "Lanchonete e Admin criados com sucesso!"}

@router.get("/lanchonete/{tenant_id}")
def buscar_lanchonete(
        tenant_id: str,
        db: Session = Depends(get_db)
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

    if not tenant:
        raise HTTPException(status_code=404, detail="Lanchonete não encontrada.")

    return {
        "id": tenant.id,
        "nome_fantasia": tenant.nome_fantasia,
        "aberto_para_pedidos": tenant.aberto_para_pedidos,
        "taxa_entrega_padrao": tenant.taxa_entrega_padrao,
        "slug": tenant.slug,
        "ativo": tenant.ativo,
        "provider_config": tenant.provider_config
    }
    
@router.delete("/lanchonete/{tenant_id}")
def deletar_lanchonete(
    tenant_id: str,
    db: Session = Depends(get_db)
):
    tenant = db.query(Tenant).filter(
        Tenant.id == tenant_id
    ).first()

    if not tenant:
        raise HTTPException(
            status_code=404, 
            detail="Lanchonete não encontrada."
        )
    
    db.delete(tenant)
    db.commit()
    
    return {
        "detail": "Categoria deletada com sucesso"
    }

# @router.get("/buscar-cardapio")
# def buscar_cardapio(
#         tenant_id: str,
#         turno_especifico: str
# ) -> Any:
#     cardapio = consultar_cardapio(tenant_id, turno_especifico)
#
#     return cardapio