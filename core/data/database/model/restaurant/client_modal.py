from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from typing import Any
from core.data.database.conection.conection_orm import Base
from core.data.database.model.base_tenant.tentantMixin import TenantMixin


class Cliente(Base, TenantMixin):
    """Cadastro de Clientes (útil para histórico de pedidos via WhatsApp)"""
    __tablename__ = 'clientes'

    id = Column(Integer, primary_key=True)
    whatsapp_id = Column(String(50), unique=True, nullable=False)
    nome = Column(String(100))
    endereco_padrao = Column(String(255))

    pedidos = relationship("Pedido", back_populates="cliente")

    def __init__(self, **kwargs: Any):
        # Repassa todos os argumentos (incluindo tenant_id) para o SQLAlchemy
        super().__init__(**kwargs)