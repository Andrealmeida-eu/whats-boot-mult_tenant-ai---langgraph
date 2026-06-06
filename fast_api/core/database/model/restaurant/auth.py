from typing import Any

from sqlalchemy import Column, Integer, String, Enum, Boolean
from sqlalchemy.orm import relationship
import enum
from fast_api.core.database.conection.conection_orm import Base
from fast_api.core.database.model.base_tenant.tentantMixin import TenantMixin


class Role(TenantMixin, enum.Enum):
    ADMIN = "admin"
    FUNCIONARIO = "funcionario"
    COZINHA = "cozinha"

class Usuario(Base, TenantMixin):
    """Funcionários e Administradores que acessam o painel"""
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    senha_hash = Column(String(255), nullable=False)
    role = Column(Enum(Role), default=Role.FUNCIONARIO)
    ativo = Column(Boolean, default=True)

    # Relacionamento com fechamentos de caixa
    caixas_abertos = relationship("Caixa", back_populates="operador")

    def __init__(self, **kwargs: Any):
        # Repassa todos os argumentos (incluindo tenant_id) para o SQLAlchemy
        super().__init__(**kwargs)