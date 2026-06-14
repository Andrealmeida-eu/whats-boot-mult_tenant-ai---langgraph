from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Any
import enum
from core.data.database.conection.conection_orm import Base
from core.data.database.model.base_tenant.tentantMixin import TenantMixin


class StatusPedido(enum.Enum):
    PENDENTE = "pendente"
    EM_PREPARO = "em_preparo"
    EM_ROTA = "em_rota"
    ENTREGUE = "entregue"
    CANCELADO = "cancelado"

class FormaPagamento(enum.Enum):
    DINHEIRO = "dinheiro"
    PIX = "pix"
    CARTAO_CREDITO = "cartao_credito"
    CARTAO_DEBITO = "cartao_debito"




class ItemPedido(Base, TenantMixin):
    """Relacionamento Muitos-para-Muitos entre Pedido e Produto com quantidade"""
    __tablename__ = 'itens_pedido'

    id = Column(Integer, primary_key=True)
    pedido_id = Column(Integer, ForeignKey('pedidos.id'))
    produto_id = Column(Integer, ForeignKey('produtos.id'))
    quantidade = Column(Integer, nullable=False, default=1)
    preco_unitario = Column(Float, nullable=False) 

    pedido = relationship("Pedido", back_populates="itens")
    produto = relationship("Produto", back_populates="itens_pedido")

    def __init__(self, **kwargs: Any):
        # Repassa todos os argumentos (incluindo tenant_id) para o SQLAlchemy
        super().__init__(**kwargs)

class Pedido(Base, TenantMixin):
    """Cabeçalho do Pedido"""
    __tablename__ = 'pedidos'

    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey('clientes.id'))
    forma_pagamento = Column(Enum(FormaPagamento))
    caixa_id = Column(Integer, ForeignKey('caixas.id'), nullable=True)
    data_criacao = Column(DateTime, default=datetime.now())
    status = Column(Enum(StatusPedido), default=StatusPedido.PENDENTE)
    valor_total = Column(Float, default=0.0)
    observacao = Column(String(255))  # Ex: "Sem cebola"

    caixa = relationship("Caixa")
    cliente = relationship("Cliente", back_populates="pedidos")
    itens = relationship("ItemPedido", back_populates="pedido", cascade="all, delete-orphan")

    tipo_entrega = Column(String(50), default="DELIVERY")  
    endereco_entrega = Column(String(255), nullable=True)  
    troco_para = Column(Float, nullable=True)

    def __init__(self, **kwargs: Any):
        # Repassa todos os argumentos (incluindo tenant_id) para o SQLAlchemy
        super().__init__(**kwargs)