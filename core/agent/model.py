from pydantic import BaseModel, Field
from typing import Literal, Optional, List

class ItemExtraido(BaseModel):
    nome_produto: str = Field(description="APENAS o nome do produto limpo, sem a quantidade. Ex: 'coca', 'pepsi 2l', 'x-tudo'")
    quantidade: int = Field(default=1, description="A quantidade numérica desejada. Ex: 1, 2")
    
    
class IntentRouter(BaseModel):
    """Classifica a intenção do usuário e extrai entidades relevantes."""
    
    intent: Literal[
        "saudacao",         
        "duvida_geral",
        "ver_cardapio", 
        "adicionar_item", 
        "checkout", 
        "confirmar_pedido", 
        "fallback"
    ] = Field(
        description="A intenção principal da mensagem do usuário."
    )
    
    itens_extraidos: Optional[List[ItemExtraido]] = Field(default=None)
    tipo_entrega: Optional[str] = Field(description="Ex: 'DELIVERY' ou 'BALCAO'")
    endereco: Optional[str] = Field(description="Endereço fornecido pelo cliente")
    forma_pagamento: Optional[str] = Field(description="Ex: 'PIX', 'CARTAO', 'DINHEIRO'")
    troco_para: Optional[str] = Field(description="Valor para troco, se houver")

    termo_busca_cardapio: Optional[str] = Field(
        default=None, 
        description="Extraia APENAS o nome da categoria se o cliente pedir para ver uma específica (ex: 'bebidas', 'lanches'). Se ele pedir o cardápio inteiro, deixe vazio."
    )