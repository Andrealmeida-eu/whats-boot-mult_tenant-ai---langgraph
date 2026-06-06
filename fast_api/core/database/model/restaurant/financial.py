from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Any
import enum
from fast_api.core.database.conection.conection_orm import Base
from fast_api.core.database.model.base_tenant.tentantMixin import TenantMixin


class StatusCaixa(enum.Enum):
    ABERTO = "aberto"
    FECHADO = "fechado"


class Caixa(Base, TenantMixin):
    """Controle de abertura e fechamento de turno/dia"""
    __tablename__ = 'caixas'

    id = Column(Integer, primary_key=True)
    data_abertura = Column(DateTime, default=datetime.now())
    data_fechamento = Column(DateTime, nullable=True)
    valor_acumulado = Column(Float, default=0.0)
    valor_inicial = Column(Float, default=0.0)  # "Troco" inicial
    valor_final = Column(Float, nullable=True)  # Valor total contado no fim
    valor_esperado = Column(Float, default=0.0)  # Soma automatica (inicial + vendas)

    status = Column(Enum(StatusCaixa), default=StatusCaixa.ABERTO)
    operador_id = Column(Integer, ForeignKey('usuarios.id'))

    operador = relationship("Usuario", back_populates="caixas_abertos")
    movimentacoes = relationship("MovimentacaoCaixa", back_populates="caixa")
    def __init__(self, **kwargs: Any):
        # Repassa todos os argumentos (incluindo tenant_id) para o SQLAlchemy
        super().__init__(**kwargs)

class MovimentacaoCaixa(Base, TenantMixin):
    """Registra entradas (vendas) e saídas (sangrias/pagamentos)"""
    __tablename__ = 'movimentacoes_caixa'

    id = Column(Integer, primary_key=True)
    caixa_id = Column(Integer, ForeignKey('caixas.id'))
    tipo = Column(String(20))  # 'ENTRADA', 'SAIDA'
    valor = Column(Float, nullable=False)
    descricao = Column(String(255))  # Ex: "Venda Pedido #102" ou "Compra de Gelo"
    data_movimentacao = Column(DateTime, default=datetime.now())

    caixa = relationship("Caixa", back_populates="movimentacoes")
    def __init__(self, **kwargs: Any):
        # Repassa todos os argumentos (incluindo tenant_id) para o SQLAlchemy
        super().__init__(**kwargs)