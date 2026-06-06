from sqlalchemy import Column, Integer, Float,  DateTime
from typing import Any
from fast_api.core.database.conection.conection_orm import Base
from fast_api.core.database.model.base_tenant.tentantMixin import TenantMixin



class GestaoIA(Base, TenantMixin):
    """Controle de abertura e fechamento de turno/dia"""
    __tablename__ = 'gestao_ia'

    id = Column(Integer, primary_key=True)
    tokens_entrada =  Column(Integer, default=0)
    tokens_saida =  Column(Integer, default=0)
    tokens_total =  Column(Integer, default=0)
    data_hora = Column(DateTime)
    custo_dolares = Column(Float, default=0.0)

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)