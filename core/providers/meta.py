# -> biblioteca HTTP síncrona
# -> usada para fazer chamadas REST simples
import requests

# -> importa o contrato base
# -> garante que MetaCloudProvider implemente send_text
from core.providers.base import WhatsAppProvider


class MetaCloudProvider(WhatsAppProvider):
    # -> implementação concreta do provedor WhatsApp Cloud (Meta oficial)

    def __init__(self, phone_number_id, access_token, api_version):
        # -> phone_number_id: ID do número de WhatsApp configurado na Meta Cloud
        self.phone_number_id = phone_number_id

        # -> access_token: token Bearer da Meta (autenticação)
        self.access_token = access_token

        # -> api_version: versão da API Graph (ex: v20.0)
        self.api_version = api_version

    def send_text(self, to: str, text: str):
        # -> monta a URL oficial da Meta Graph API para envio de mensagens
        # -> exemplo:
        # -> https://graph.facebook.com/v20.0/123456789/messages
        url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"

        # -> headers exigidos pela Meta
        headers = {
            # -> autenticação Bearer obrigatória
            "Authorization": f"Bearer {self.access_token}",

            # -> payload será JSON
            "Content-Type": "application/json",
        }

        # -> payload no formato EXIGIDO pela Meta Cloud
        payload = {
            "messaging_product": "whatsapp",  # -> obrigatório, sempre "whatsapp"
            "to": to,                          # -> número do destinatário (E.164)
            "type": "text",                    # -> tipo da mensagem
            "text": {
                "body": text                  # -> texto da mensagem
            },
        }

        # -> envia a requisição POST para a Meta Cloud
        # -> requests é síncrono (bloqueante)
        # -> por isso essa função é chamada via asyncio.to_thread(...)
        requests.post(url, json=payload, headers=headers)
