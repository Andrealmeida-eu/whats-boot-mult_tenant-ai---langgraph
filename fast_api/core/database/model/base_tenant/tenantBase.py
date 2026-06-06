from sqlalchemy import Column, String, Boolean, JSON, Float, Integer
from sqlalchemy.orm import relationship

from fast_api.core.database.conection.conection_orm import Base
import enum


class Tenant(Base):
    __tablename__ = 'tenants'

    id = Column(String, primary_key=True) # Ex: 'lanches-do-jorge'
    nome_fantasia = Column(String(100), nullable=False)
    cnpj = Column(String(14), unique=True, nullable=True)
    slug = Column(String(50), unique=True) # Para URLs personalizadas
    ativo = Column(Boolean, default=True)
    whatsapp_provider = Column(String(20)) # 'evolution' ou 'meta'
    taxa_entrega_padrao = Column(Float)
    aberto_para_pedidos = Column(Boolean, default=False)
    provider_config = Column(JSON, nullable=True)

    horarios = relationship("HorarioFuncionamento", back_populates="tenant", cascade="all, delete-orphan")
