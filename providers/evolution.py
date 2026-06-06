# -> biblioteca HTTP síncrona
# -> usada para fazer chamadas REST simples
from locale import normalize

import requests
from requests import RequestException, HTTPError, JSONDecodeError

# -> importa o contrato (classe abstrata)
# -> garante que EvolutionProvider implemente send_text
from providers.base import WhatsAppProvider

from requests.exceptions import (
    RequestException, ConnectionError, Timeout, HTTPError, JSONDecodeError
)


class EvolutionProvider(WhatsAppProvider):
    # -> implementação concreta do provedor Evolution
    # -> essa classe SABE como enviar mensagens usando a Evolution API

    def __init__(self, api_url, instance_name, api_key):
        # -> api_url: URL base da Evolution API (ex: http://evolution-api:8080)
        self.api_url = api_url

        # -> instance_name: nome da instância configurada na Evolution
        self.instance_name = instance_name

        # -> api_key: chave de autenticação da Evolution
        self.api_key = api_key


    def _normalize_number(self, to: str) -> str:
        # aceita: "5519...@s.whatsapp.net" ou "5519..." e devolve só dígitos
        to = (to or "").strip()
        if "@" in to:
            to = to.split("@", 1)[0]
        # mantém apenas dígitos
        to = "".join(ch for ch in to if ch.isdigit())
        return to


    def send_text(self, to: str, text: str):
        # -> monta a URL do endpoint da Evolution para envio de texto
        # -> exemplo final:
        # -> http://evolution-api:8080/message/sendText/minha-instancia
        url = f"{self.api_url}/message/sendText/{self.instance_name}"
        
        # -> headers obrigatórios para autenticação e tipo de conteúdo
        headers = {
            "apikey": "YOUR_AUTH_API_KEY",                # -> autenticação na Evolution
            "Content-Type": "application/json"     # -> corpo em JSON
        }
        print(f"url: {url}, text: {text}, instancia: {self.instance_name}, para: {to}, apikey= {self.api_key}")
        # -> payload enviado para a Evolution

        number = self._normalize_number(to)
        payload = {
            "number": number,   # -> chat_id / número do destinatário
            "text": text   # -> mensagem a ser enviada
        }
        
        # -> faz a requisição POST para enviar a mensagem
        # -> requests é síncrono (bloqueante)
        # -> por isso essa função é chamada dentro de asyncio.to_thread(...)
        try:
            resposta = requests.post(url, json=payload, headers=headers)
            print(f"resposta: {resposta}, apikey= {headers.items}")

        except ConnectionError:
            return {"error": "Servidor inacessível"}

        except Timeout:
            return {"error": "Timeout - tente novamente"}
        except HTTPError as e:
            return {
                "error": f"HTTP {e.response.status_code}",
                "message": e.response.text[:200]
            }
        except Exception as e:
            return {"error": f"Erro inesperado: {str(e)}"}