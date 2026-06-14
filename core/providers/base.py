# -> ABC = Abstract Base Class
# -> permite definir "contratos" que outras classes devem obrigatoriamente cumprir
from abc import ABC, abstractmethod


class WhatsAppProvider(ABC):
    # -> Classe base abstrata para provedores de WhatsApp
    # -> Ela NÃO pode ser instanciada diretamente
    # -> Serve apenas como um "molde" / contrato

    @abstractmethod
    def send_text(self, to: str, text: str):
        # -> Método abstrato
        # -> Toda classe que herdar WhatsAppProvider
        # -> É OBRIGADA a implementar esse método

        # -> to: identificador do destinatário (ex: chat_id / phone_number)
        # -> text: mensagem que será enviada

        # -> aqui não tem implementação
        # -> quem define COMO enviar é o provedor concreto (Evolution, Meta, etc.)
        pass
