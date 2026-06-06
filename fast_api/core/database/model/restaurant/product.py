from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from typing import Any
from fast_api.core.database.conection.conection_orm import Base
from fast_api.core.database.model.base_tenant.tentantMixin import TenantMixin

class Categoria(TenantMixin, Base):
    __tablename__ = 'categorias'
    id = Column(Integer, primary_key=True)
    nome = Column(String)
    produtos = relationship("Produto", back_populates="categoria")

    def __init__(self, **kwargs: Any):
        # Repassa todos os argumentos (incluindo tenant_id) para o SQLAlchemy
        super().__init__(**kwargs)




class Produto(TenantMixin, Base):
    """Itens do Cardápio"""
    __tablename__ = 'produtos'

    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(String(255))
    preco = Column(Float, nullable=False)
    categoria_id = Column(Integer, ForeignKey('categorias.id'))

    sub_tipo = Column(String(50), nullable=True)

    disponibilidade_turno = Column(String, default="todos")
    categoria = relationship("Categoria", back_populates="produtos")
    itens_pedido = relationship("ItemPedido", back_populates="produto")

    def __init__(self, **kwargs: Any):
        # Repassa todos os argumentos (incluindo tenant_id) para o SQLAlchemy
        super().__init__(**kwargs)