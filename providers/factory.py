# -> importa a implementação concreta do provedor Evolution
from providers.evolution import EvolutionProvider

# -> importa a implementação concreta do provedor Meta Cloud
from providers.meta import MetaCloudProvider


def get_provider(tenant):
    """
    Função fábrica que recebe o tenant do banco de dados
    e devolve a classe provedora de WhatsApp correta pronta para uso.
    """

    if not tenant.whatsapp_provider or not tenant.provider_config:
        raise ValueError(f"A lanchonete {tenant.id} não possui whatsapp configurado.")

    cfg = tenant.provider_config
    if tenant.whatsapp_provider == "evolution":
        return EvolutionProvider(
            api_url=cfg.get("api_url"),              # -> URL base da Evolution API
            instance_name=cfg.get("instance_name"),  # -> nome da instância
            api_key=cfg.get("api_key")               # -> chave de autenticação
        )

    if tenant.whatsapp_provider == "meta":
        return MetaCloudProvider(
            phone_number_id=cfg.get("phone_number_id"),  # -> ID do número no WhatsApp Cloud
            access_token=cfg.get("access_token"),        # -> token de acesso
            api_version=cfg.get("api_version"),          # -> versão da API
        )
        
    # -> se chegar aqui, o provider configurado é inválido
    # -> falha explícita para não mascarar erro de configuração
    raise ValueError(f"Provider '{tenant.whatsapp_provider}' não suportado")
