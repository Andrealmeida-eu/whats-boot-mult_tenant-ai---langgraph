from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fast_api.core.database.conection.conection_orm import get_db
from fast_api.core.database.model.restaurant.auth import Usuario
from fast_api.core.security.dependencies import get_admin_user, get_current_user
from fast_api.core.database.model.restaurant.financial import Caixa, StatusCaixa

router = APIRouter(prefix="/caixa", tags=["Financeiro"])

class CaixaOpen(BaseModel):
    valor_inicial: float
    Valor_esperado: float




@router.post("/abrir")
def abrir_caixa(
        payload: CaixaOpen,
        current_user = Depends(get_current_user),
        db: Session = Depends(get_db),

        admin: Usuario = Depends(get_admin_user)
):
    # Verifica se já existe um caixa aberto para este tenant
    caixa_aberto = db.query(Caixa).filter(
        Caixa.tenant_id == admin.tenant_id,
        Caixa.status == StatusCaixa.ABERTO
    ).first()

    if caixa_aberto:
        raise HTTPException(status_code=400, detail="Já existe um caixa aberto.")

    novo_caixa = Caixa(
        tenant_id=admin.tenant_id,
        valor_inicial=payload.valor_inicial,

        valor_esperado=payload.Valor_esperado,  # Vai somando conforme as vendas entram
        operador_id=current_user.id
    )

    db.add(novo_caixa)
    db.commit()
    db.refresh(novo_caixa)
    return novo_caixa

@router.post("/fechar")
def fechar_caixa(
        db: Session = Depends(get_db),
        admin: Usuario = Depends(get_admin_user)
):

    caixa_aberto = (
        db.query(Caixa)
          .filter(
            Caixa.tenant_id == admin.tenant_id,
            Caixa.status == StatusCaixa.ABERTO
          )
          .first()
    )

    if not caixa_aberto:
        raise HTTPException("Não há caixa a ser fechado")

    valor_total = caixa_aberto.valor_acumulado

    diferenca = caixa_aberto.valor_acumulado - caixa_aberto.valor_esperado

    caixa_aberto.status = StatusCaixa.FECHADO
    caixa_aberto.diferenca = diferenca
    caixa_aberto.valor_final = valor_total
    caixa_aberto.data_fechamento = datetime.now()

    db.commit()
    db.refresh(caixa_aberto)

    return caixa_aberto

@router.get("/buscar_aberto")
def buscar_caixa_aberto(
        db: Session = Depends(get_db),
        admin:Usuario = Depends(get_admin_user)
):

    caixa_aberto = (
        db.query(Caixa)
          .filter(
            Caixa.tenant_id == admin.tenant_id,
            Caixa.status == StatusCaixa.ABERTO
        )
        .first()

    )
    if not caixa_aberto:
        raise HTTPException(status_code=404, detail="Caixas Abertos não encontrados!")

    return caixa_aberto

@router.get("/")
def listar_todas_caixas(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        admin: Usuario = Depends(get_admin_user)
):

    caixas = (
        db.query(Caixa).filter(
            Caixa.tenant_id == admin.tenant_id
        ).order_by(Caixa.id.desc()).offset(skip).limit(limit).all()
    )

    return caixas