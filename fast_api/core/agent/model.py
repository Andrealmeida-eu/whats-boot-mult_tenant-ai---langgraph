from pydantic import BaseModel, Field
from typing import Literal, Optional, List

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
    
    itens_extraidos: Optional[List[str]] = Field(
        default=None,
        description="Se a intenção for 'adicionar_item', extraia os itens e quantidades. Ex: ['2x X-Bacon', '1x Coca']"
    )

    
    termo_busca_cardapio: Optional[str] = Field(
        default=None, 
        description="Extraia APENAS o nome da categoria se o cliente pedir para ver uma específica (ex: 'bebidas', 'lanches'). Se ele pedir o cardápio inteiro, deixe vazio."
    )