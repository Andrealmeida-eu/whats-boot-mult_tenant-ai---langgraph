from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel


from core.data.database.conection.conection_orm import get_db
from core.security.dependencies import get_current_tenant
from core.data.database.model.base_tenant.tenantBase import Tenant
from core.data.database.model.restaurant.client_modal import Cliente


router = APIRouter(prefix="/clientes", tags=["Clientes (Agente)"])

class CheckClientePayload(BaseModel):
    whatsapp_id: str
    nome_whatsapp: str

@router.post("/agente/check")
def check_ou_criar_cliente(
        payload: CheckClientePayload,
        db: Session = Depends(get_db),
        tenant: Tenant = Depends(get_current_tenant)
):

    cliente = db.query(Cliente).filter(
        Cliente.whatsapp_id == payload.whatsapp_id,
        Cliente.tenant_id == tenant.id
    ).first()


    if not cliente:
        cliente = Cliente(
            tenant_id=tenant.id,
            whatsapp_id=payload.whatsapp_id,
            nome=payload.nome_whatsapp
        )
        db.add(cliente)
        db.commit()
        db.refresh(cliente)


    return {
        "id": cliente.id,
        "nome": cliente.nome,
        "endereco_padrao": cliente.endereco_padrao,
        "novo_cliente": not bool(cliente.endereco_padrao)
    }

@router.get("/listar_clientes")
def buscar_cliente(
        db: Session = Depends(get_db),
        tenant: Tenant = Depends(get_current_tenant)
):
    cliente = db.query(Cliente).filter(Cliente.tenant_id == tenant.id).all()

    return cliente

# @router.post("/produto-name")
# def get_produto(
#         produto_nome,
#         qty,
#         tenant: Tenant = Depends(get_current_tenant)
#
# ):
#     cliente = add_item_to_cart_state(tenant.id , produto_nome, qty)
#
#     return cliente
