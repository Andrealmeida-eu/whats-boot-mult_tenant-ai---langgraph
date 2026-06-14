# models/base_tenant.py
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import declared_attr

class TenantMixin:
    @declared_attr
    def tenant_id(cls):
        return Column(String, nullable=False, index=True)