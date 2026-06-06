from contextlib import contextmanager

from pydantic import BaseModel
from datetime import datetime
from fast_api.core.database.conection.conection_orm import get_db
from fast_api.core.database.model.restaurant.gestao_ia import GestaoIA


class GestaoCreate(BaseModel):
    tokens_entrada: int
    tokens_saida: int
    tokens_total: int
    custo_dolares: float
    data_hora: datetime

def salvar_dados_interacao(
        payload: GestaoCreate,
        tenant_pay_id: str,
):
    with contextmanager(get_db)() as db:
        gestao = GestaoIA(
            tokens_entrada=payload.tokens_entrada,
            tokens_saida=payload.tokens_saida,
            tokens_total=payload.tokens_total,
            custo_dolares=payload.custo_dolares,
            tenant_id= tenant_pay_id,
            data_hora=payload.data_hora
        )
        db.add(gestao)
        db.commit()
