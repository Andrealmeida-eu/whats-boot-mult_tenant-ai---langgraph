from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from core.data.database.conection.conection_orm import get_db
from core.data.database.model.restaurant.financial import MovimentacaoCaixa, Caixa, StatusCaixa
from core.security.dependencies import get_current_tenant
from core.data.database.model.base_tenant.tenantBase import Tenant
from core.data.database.model.restaurant.orders import Pedido, ItemPedido, StatusPedido,Base
from core.data.database.model.restaurant.client_modal import Cliente
from core.providers.factory import get_provider
from pydantic import BaseModel
from typing import List, Optional


router = APIRouter(prefix="/pedidos", tags=["Pedidos"])

class ItemPedidoCreate(BaseModel):
    produto_id: int
    quantidade: int


class PedidoCreate(BaseModel):
    cliente_id: int | None = None  
    observacao: str | None = None

    itens: List[ItemPedidoCreate]

    tipo_entrega: str 
    endereco_entrega: Optional[str] = None  
    forma_pagamento: Optional[str] = None  
    troco_para: Optional[float] = None


class ItemPedidoResponse(BaseModel):
    id: int
    produto_id: int
    quantidade: int
    preco_unitario: float

    class Config:
        from_attributes = True  



class PedidoResponse(BaseModel):
    id: int
    cliente_id: int
    status: str
    valor_total: float
    tipo_entrega: str
    forma_pagamento: str


    itens: List[ItemPedidoResponse] = []

    class Config:
        from_attributes = True 

@router.post("/")
def criar_pedido(
        payload: PedidoCreate,
        db: Session = Depends(get_db),
        tenant: Tenant = Depends(get_current_tenant)
):
    from core.data.database.model.restaurant.product import Produto


    novo_pedido = Pedido(
        tenant_id=tenant.id,
        cliente_id=payload.cliente_id,
        observacao=payload.observacao,
        status=StatusPedido.PENDENTE,
        valor_total=0.0,

        tipo_entrega = payload.tipo_entrega,
        endereco_entrega = payload.endereco_entrega,
        forma_pagamento = payload.forma_pagamento,
        troco_para = payload.troco_para
    )
    db.add(novo_pedido)
    db.flush()

    valor_total = 0.0

    for item in payload.itens:

        produto = db.query(Produto).filter(
            Produto.id == item.produto_id, Produto.tenant_id == tenant.id
        ).first()

        if not produto:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Produto {item.produto_id} inválido.")

        novo_item = ItemPedido(
            tenant_id=tenant.id,
            pedido_id=novo_pedido.id,
            produto_id=produto.id,
            quantidade=item.quantidade,
            preco_unitario=produto.preco
        )
        db.add(novo_item)
        valor_total += (produto.preco * item.quantidade)

    novo_pedido.valor_total = valor_total
    db.commit()
    db.refresh(novo_pedido)
    return novo_pedido

@router.get("/{pedido_id}")
def obter_pedido(
        pedido_id: int,
        db: Session = Depends(get_db),
        tenant: Tenant = Depends(get_current_tenant)
):

    pedido = db.query(Pedido).filter(
        Pedido.id == pedido_id,
        Pedido.tenant_id == tenant.id
    ).options(
        joinedload(Pedido.itens)
    ).first()


    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")


    return pedido

@router.delete("/{pedido_id}")
def cancelar_pedido(
        pedido_id: int,
        db: Session = Depends(get_db),
        tenant: Tenant = Depends(get_current_tenant)
):
    pedido = db.query(Pedido).filter(
        Pedido.id == pedido_id,
        Pedido.tenant_id == tenant.id
    ).first()

    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")


    if pedido.status == StatusPedido.ENTREGUE:
        raise HTTPException(status_code=400, detail="Não é possível cancelar um pedido que já foi entregue.")

    pedido.status = StatusPedido.CANCELADO
    db.commit()

    return {"message": "Pedido cancelado com sucesso"}

@router.get("/")
def listar_pedidos(
        status: Optional[StatusPedido] = None,
        limit: int = 50,
        db: Session = Depends(get_db),
        tenant: Tenant = Depends(get_current_tenant)
):
    query = db.query(Pedido).filter(Pedido.tenant_id == tenant.id)

    if status:
        query = query.filter(Pedido.status == status)


    pedidos = query.order_by(Pedido.id.desc()).limit(limit).all()
    return pedidos

@router.patch("/{pedido_id}/status")
def atualizar_status(
        pedido_id: int,
        novo_status: StatusPedido,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db),
        tenant: Tenant = Depends(get_current_tenant)
):
    print(f"status ---> {novo_status}")
    pedido = db.query(Pedido).filter(
        Pedido.id == pedido_id,
        Pedido.tenant_id == tenant.id
    ).first()

    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    status_anterior = pedido.status
    pedido.status = novo_status

    if novo_status == StatusPedido.ENTREGUE and status_anterior != StatusPedido.ENTREGUE:

        caixa_aberto = db.query(Caixa).filter(
            Caixa.tenant_id == tenant.id,
            Caixa.status == StatusCaixa.ABERTO
        ).first()

        if not caixa_aberto:
            raise HTTPException(
                status_code=400,
                detail="Não ha caixa aberto"
            )

        nova_movimentacao = MovimentacaoCaixa(
            tenant_id = tenant.id,
            caixa_id = caixa_aberto.id,
            valor = pedido.valor_total,
            tipo = "ENTRADA",
            descricao = f"Recebimento referente ao pedido #{pedido.id}"
        )

        db.add(nova_movimentacao)
        if caixa_aberto.valor_acumulado is None:
            caixa_aberto.valor_acumulado = 0.0

        caixa_aberto.valor_acumulado += pedido.valor_total

    db.commit()
    providers = get_provider(tenant)

    if pedido.cliente_id:
        cliente = db.query(Cliente).filter(Cliente.id == pedido.cliente_id).first()

        if cliente and cliente.whatsapp_id:
            mensagem = ""
            if novo_status == StatusPedido.EM_PREPARO:
                mensagem = f"👨‍🍳 Olá {cliente.nome}, seu pedido #{pedido.id} está na chapa!"
            elif novo_status == StatusPedido.EM_ROTA:
                mensagem = f"🏍️ Oba! Seu pedido #{pedido.id} saiu para entrega."

            if mensagem:
                background_tasks.add_task(
                    providers.send_text,
                    cliente.whatsapp_id,
                    mensagem
                )



    return {"message": f"Status atualizado para {novo_status.value}"}

