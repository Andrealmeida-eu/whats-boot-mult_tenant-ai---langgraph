from enum import EnumCheck

from sqlalchemy import Column, String, Integer, ForeignKey, Time, Enum
from sqlalchemy.orm import relationship

from core.data.database.model.base_tenant.tenantBase import Base
import enum

class TurnoCardapio(str, enum.Enum):
    DIA = "dia"
    NOITE = "noite"
    TODOS = "todos"

class HorarioFuncionamento(Base):
    __tablename__ = "horarios_funcionamento"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(ForeignKey("tenants.id", ondelete="CASCADE"))

    dia_semana = Column(Integer) # 0 = Segunda, ..., 6 = Domingo
    hora_abertura = Column(Time)
    hora_fechamento = Column(Time)

    turno_cardapio = Column(Enum(TurnoCardapio), default=TurnoCardapio.TODOS)
    tenant = relationship("Tenant", back_populates="horarios")