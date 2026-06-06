from __future__ import annotations
from dataclasses import dataclass
from typing import Dict
from fast_api.core.config.configapi import settings


# Importe seu Model de Tenant que criamos anteriormente

@dataclass(frozen=True)
class TenantConfig:
    """Configurações de runtime de um Tenant (Lanchonete)"""
    id: str
    name: str
    provider: str  # "evolution" | "meta"
    model_name: str
    model_temperature: float
    provider_config: Dict  # Detalhes da API (Key, Instance, etc)


class TenantService:
    """Gerenciador para carregar configurações dos tenants"""

    @staticmethod
    def build_config(
            tenant_id: str,
            name: str,
            provider: str,
            extra_configs: Dict
    ) -> TenantConfig:
        """Monta o objeto de configuração baseado no provedor"""

        provider = provider.lower().strip()
        provider_config = {}

        if provider == "evolution":
            provider_config = {
                "api_url": extra_configs.get("api_url"),
                "instance_name": extra_configs.get("instance_name"),
                "api_key": extra_configs.get("api_key"),
            }
        elif provider == "meta":
            provider_config = {
                "phone_number_id": extra_configs.get("phone_number_id"),
                "access_token": extra_configs.get("access_token"),
                "api_version": extra_configs.get("api_version", "v17.0"),
            }

        return TenantConfig(
            id=tenant_id,
            name=name,
            provider=provider,
            model_name=settings.OPENAI_MODEL_NAME,  # Pode vir do banco também
            model_temperature=settings.OPENAI_MODEL_TEMPERATURE,
            provider_config=provider_config
        )


# Instância global para uso no sistema
tenant_service = TenantService()