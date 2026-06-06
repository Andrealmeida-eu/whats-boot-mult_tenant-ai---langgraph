from datetime import datetime, time
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from fast_api.core.database.conection.conection_orm import get_db
from fast_api.core.database.model.base_tenant.horarioFuncionamento import HorarioFuncionamento
from fast_api.core.database.model.base_tenant.tenantBase import Tenant
from fast_api.core.security.dependencies import get_current_tenant

router = APIRouter(prefix="/funcionamento", tags=["horario-funcionamento"])
fuso_sp = ZoneInfo("America/Sao_Paulo")
class HorarioCreate(BaseModel):
    dia_semana: int
    abertura: time
    fechamento: time
    turno: str


def verificar_status_e_turno(
        tenant_id: str,
        db: Session = Depends(get_db)) -> dict:
    """
    Verifica se a loja está aberta AGORA e qual o turno ativo.
    Trata inclusive turnos que ultrapassam a meia-noite.
    Retorna: {"aberto": True/False, "turno": "dia"/"noite"/"todos"/None}
    """
    agora = datetime.now(fuso_sp)
    dia_atual = agora.weekday()
    hora_atual = agora.time()
    print(F"AGORA ----> {agora}")
    print(F"DIA_ATUAL ----> {dia_atual}")
    print(F"HORA_ATUAL ----> {hora_atual}")

    horario_normal = db.query(HorarioFuncionamento).filter(
        HorarioFuncionamento.tenant_id == tenant_id,
        HorarioFuncionamento.dia_semana == dia_atual,
        HorarioFuncionamento.hora_abertura <= HorarioFuncionamento.hora_fechamento,  # Mesmo dia
        HorarioFuncionamento.hora_abertura <= hora_atual,
        HorarioFuncionamento.hora_fechamento >= hora_atual
    ).first()
    print(F"NORMAL ----> {horario_normal}")
    if horario_normal:
        return {"aberto": True, "turno": horario_normal.turno_cardapio}

    horario_virada_hoje = db.query(HorarioFuncionamento).filter(
        HorarioFuncionamento.tenant_id == tenant_id,
        HorarioFuncionamento.dia_semana == dia_atual,
        HorarioFuncionamento.hora_abertura > HorarioFuncionamento.hora_fechamento,
        hora_atual >= HorarioFuncionamento.hora_abertura
    ).first()
    print(F"VIRADA HOJE ----> {horario_virada_hoje}")
    if horario_virada_hoje:
        return {"aberto": True, "turno": horario_virada_hoje.turno_cardapio}

    dia_ontem = 6 if dia_atual == 0 else dia_atual - 1

    horario_virada_ontem = db.query(HorarioFuncionamento).filter(
        HorarioFuncionamento.tenant_id == tenant_id,
        HorarioFuncionamento.dia_semana == dia_ontem,
        HorarioFuncionamento.hora_abertura > HorarioFuncionamento.hora_fechamento,
        hora_atual <= HorarioFuncionamento.hora_fechamento
    ).first()
    print(F"VIRADA ONTEM ----> {horario_virada_ontem}")
    if horario_virada_ontem:
        return {"aberto": True, "turno": horario_virada_ontem.turno_cardapio}


    return {"aberto": False, "turno": None}

@router.post("/add_horario")
def adicionar_horario(
        payload: HorarioCreate,
        tenant: Tenant = Depends(get_current_tenant),
        db: Session = Depends(get_db)):
    """Cadastra um novo período de funcionamento validando superposições simples."""


    conflito = db.query(HorarioFuncionamento).filter(
        HorarioFuncionamento.tenant_id == tenant.id,
        HorarioFuncionamento.dia_semana == payload.dia_semana,
        or_(
            and_(
                HorarioFuncionamento.hora_abertura <= payload.abertura,
                HorarioFuncionamento.hora_fechamento >= payload.abertura
            ),
            and_(
                HorarioFuncionamento.hora_abertura <= payload.fechamento,
                HorarioFuncionamento.hora_fechamento >= payload.fechamento
            )
        )
    ).first()

    if conflito:
        raise ValueError("Este horário entra em conflito com um período já cadastrado.")

    novo_horario = HorarioFuncionamento(
        tenant_id=tenant.id,
        dia_semana=payload.dia_semana,
        hora_abertura=payload.abertura,
        hora_fechamento=payload.fechamento,
        turno_cardapio=payload.turno
    )
    db.add(novo_horario)
    db.commit()
    db.refresh(novo_horario)
    return novo_horario

@router.get("/get_horario")
def listar_horarios_loja(
        tenant: Tenant = Depends(get_current_tenant),
        db: Session = Depends(get_db)
):
    """Retorna todos os horários configurados ordenados por dia da semana e hora de abertura."""
    return db.query(HorarioFuncionamento).filter(
        HorarioFuncionamento.tenant_id == tenant.id
    ).order_by(
        HorarioFuncionamento.dia_semana,
        HorarioFuncionamento.hora_abertura
    ).all()

@router.delete("/del_horario")
def remover_horario(
        horario_id: int,
        tenant: Tenant = Depends(get_current_tenant),
        db: Session = Depends(get_db)
) -> bool:
    """Remove um horário específico, garantindo que pertença ao tenant requisitante."""
    horario = db.query(HorarioFuncionamento).filter(
        HorarioFuncionamento.id == horario_id,
        HorarioFuncionamento.tenant_id == tenant.id
    ).first()

    if not horario:
        return False

    db.delete(horario)
    db.commit()
    return True

@router.post("/clonar_horario")
def clonar_horarios_dia(
        dia_origem: int,
        dias_destino: list[int],
        tenant: Tenant = Depends(get_current_tenant),
        db: Session = Depends(get_db)):
    """Copia as configurações de horários de um dia para múltiplos outros dias."""
    horarios_origem = db.query(HorarioFuncionamento).filter(
        HorarioFuncionamento.tenant_id == tenant.id,
        HorarioFuncionamento.dia_semana == dia_origem
    ).all()

    if not horarios_origem:
        return False

    for dia in dias_destino:
        # 1. Limpa os horários antigos do dia de destino para não duplicar
        db.query(HorarioFuncionamento).filter(
            HorarioFuncionamento.tenant_id == tenant.id,
            HorarioFuncionamento.dia_semana == dia
        ).delete()

        # 2. Cria as novas cópias
        for h in horarios_origem:
            copia = HorarioFuncionamento(
                tenant_id=tenant.id,
                dia_semana=dia,
                hora_abertura=h.hora_abertura,
                hora_fechamento=h.hora_fechamento,
                turno_cardapio=h.turno_cardapio
            )
            db.add(copia)

    db.commit()
    return True