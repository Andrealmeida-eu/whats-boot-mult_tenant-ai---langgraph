from __future__ import annotations
from dataclasses import dataclass
from typing import Dict
from core.config.configapi import settings




@dataclass(frozen=True)
class TenantConfig:
    """Configurações de runtime de um Tenant (Lanchonete)"""
    id: str
    name: str
    provider: str
    model_name: str
    model_temperature: float
    provider_config: Dict 


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
                "instance_url": extra_configs.get("instance_url"),
                "instance_name": extra_configs.get("instance_name"),
                "global_apikey": extra_configs.get("global_apikey"),
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
            model_name=settings.OPENAI_MODEL_NAME,  
            model_temperature=settings.OPENAI_MODEL_TEMPERATURE,
            provider_config=provider_config
        )


# Instância global para uso no sistema
tenant_service = TenantService()