
from typing import List, Optional, Any, Literal
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from fast_api.redis.cart import add_item_to_cart_state, get_cart_state, clear_cart_state, atualizar_dados_checkout

from fast_api.utils.service_tool import lancar_pedido_sistema_state, consultar_status_pedido_state, \
    consultar_cardapio_state, consultar_preco_produto_state, enviar_resumo_pedido_state


# ==========================================
# 1. SCHEMAS (PYDANTIC) DAS FERRAMENTAS
# ==========================================
class TenantInput(BaseModel):
    tenant_id: str = Field(description="The ID of the diner (tenant). E.g., 'burger-do-japa'")


class ClienteTenantInput(BaseModel):
    tenant_id: str = Field(description="The ID of the diner")
    whatsapp_cliente: str = Field(description="The customer's WhatsApp number")


class ItemPedidoIA(BaseModel):
    nome_produto: str = Field(description="Name of the product as per the menu")
    quantidade: int = Field(description="Requested quantity")


class LancarPedidoInput(BaseModel):
    tenant_id: str = Field(description="The ID of the diner")
    chat_id: str = Field(description="The ID of the conversation")
    tipo_entrega: str = Field(description="'DELIVERY' or 'BALCAO' (pickup)")
    forma_pagamento: str = Field(description="PIX, DINHEIRO (cash), or CARTAO (card)")
    endereco_entrega: Optional[str] = Field(None, description="Full delivery address. Empty if BALCAO.")
    troco_para: Optional[float] = Field(None,
                                        description="If paying in cash, specify the amount for change. E.g., 50.0")

    itens: List[ItemPedidoIA] = Field(description="MANDATORY list containing the items the customer chose.")

class CardapioInput(BaseModel):
    tenant_id: str = Field(..., description="The ID of the store")
    turno_especifico: Optional[str] = Field(
        None,
        description="OPTIONAL. Use 'dia' (day) or 'noite' (night) ONLY if the customer asks about items from a different shift."
    )
    termo_busca: Optional[str] = Field(
        default=None,
        description="Name of the category the customer chose. Leave empty if you want to list the category names"
    )

class CarrinhoInput(BaseModel):
    tenant_id: str = Field(description="The ID of the store")
    categoria_escolhida: str = Field(description="Category of the chosen product")
    itens: ItemPedidoIA = Field(description="Chosen snack(s) and drink(s)")

class CartInput(BaseModel):
    tenant_id: str = Field (description="The ID of the diner")
    chat_id: str = Field(description="The ID of the conversation")
    produto_nome: Optional[str] = Field(None, description="Name of the product")
    produto_preco: Optional[float] = Field(None, description="Price of the product")
    qty: Optional[int] = Field(None, description="Quantity of items")


class AcaoCarrinhoInput(BaseModel):
    tenant_id: str
    chat_id: str
    acao: str = Field(description="'adicionar', 'remover', 'alterar', 'consultar', 'checkout' or 'limpar'")
    produto_nome: Optional[str] = Field(None, description="Name of the product")
    itens: Optional[List[ItemPedidoIA]] = Field(None, description="List of items, if applicable")
    qty: Optional[int] = Field(None, description="Quantity of items")
    tipo_entrega: str = Field(description="'DELIVERY' or 'BALCAO' (pickup)")
    forma_pagamento: str = Field(description="PIX, DINHEIRO (cash), or CARTAO (card)")
    endereco_entrega: Optional[str] = Field(None, description="Full delivery address. Empty if BALCAO.")
    troco_para: Optional[float] = Field(None,
                                        description="If paying in cash, specify the amount for change. E.g., 50.0")
# ==========================================
# 2. FERRAMENTAS (TOOLS) PARA O AGENTE
# ==========================================

@tool(args_schema=CartInput)
def consultar_preco_produto(
        tenant_id: str,
        produto_nome: str,
        **kwargs
) -> Any:

    """
       ALWAYS use after the customer asks to add an item and this item does not have a price.
    """
    preco_produto = consultar_preco_produto_state(
        tenant_id,
        produto_nome
    )

    return preco_produto

@tool(args_schema=CardapioInput)
def consultar_cardapio(
        tenant_id: str,
        turno_especifico: str,
        termo_busca: str
) -> Any:
    """
        ALWAYS use whenever the customer asks to see the menu.
        If no search term is passed, it lists the Main Categories.
        If the search term is a category (e.g., "Bebidas"), it returns the products separated by sub-types.
   """
    consulta_cardapio = consultar_cardapio_state(
            tenant_id,
            turno_especifico,
            termo_busca
    )

    return consulta_cardapio



@tool(args_schema=ClienteTenantInput)
def consultar_status_pedido(tenant_id: str, whatsapp_cliente: str) -> str:
    """
   Use when the customer asks "Cadê meu lanche?", "Já saiu para entrega?", or "Qual o status do meu pedido?".
    """

    consultar_status = consultar_status_pedido_state(
                                        tenant_id,
                                        whatsapp_cliente
    )

    return consultar_status



@tool(args_schema=LancarPedidoInput)
async def lancar_pedido_sistema(
        tenant_id: str,chat_id: str,
        tipo_entrega: str, forma_pagamento: str, endereco_entrega: str = None, troco_para: float = None
) -> str:
    """
    Use ONLY at the end of the service, after sending the summary and the customer says "Sim, pode confirmar".
    Saves the official order in the diner's system.
    """



    lancar_pedido_call = await lancar_pedido_sistema_state(
                    tenant_id,
                    chat_id,
                    tipo_entrega,
                    forma_pagamento,
                    endereco_entrega,
                    troco_para
    )

    return lancar_pedido_call

@tool()
async def enviar_resumo_pedido(
        tenant_id: str,
        chat_id: str
) -> str:
    """
    Used when the customer has finished ordering, to generate the order summary.
    """
    await enviar_resumo_pedido_state(
        tenant_id,
        chat_id
    )

    return (
        "SYSTEM: The receipt has been successfully sent via API.\n"
    )






@tool(args_schema=AcaoCarrinhoInput)
async def gerenciar_carrinho(
        tenant_id: str,
        chat_id: str,
        acao: str,
        produto_nome: str,
        qty: int,
        tipo_entrega: str,
        endereco: str,
        forma_pagamento: str,
        itens: list = None) -> str:
    """A single tool to manage the customer's shopping cart."""

    if acao == "consultar":
        cart = await get_cart_state(tenant_id, chat_id)
        return f"Carrinho atual: {cart}"

    elif acao == "limpar":
        await clear_cart_state(tenant_id, chat_id)
        return "Carrinho limpo."

    elif acao == "checkout":
        checkout = await atualizar_dados_checkout(
            tenant_id,
            chat_id,
            tipo_entrega,
            endereco,
            forma_pagamento
        )

        return checkout

    elif acao == "adicionar":
        resultados = []
        # 1. Se a IA mandou como Lista/Lote (itens)
        if itens:
            for item in itens:
                nome = None
                quantidade = 1

                if isinstance(item, dict):
                    nome = item.get('nome_produto')
                    quantidade = item.get('quantidade', 1)
                else:
                    nome = getattr(item, 'nome_produto', None)
                    quantidade = getattr(item, 'quantidade', 1)

                if not nome:
                    continue

                res = await add_item_to_cart_state(tenant_id, chat_id, nome, quantidade)
                resultados.append(res)

                return res

        elif produto_nome:
            quantidade = qty if qty is not None else 1
            res = await add_item_to_cart_state(tenant_id, chat_id, produto_nome, quantidade)
            resultados.append(res)

        else:
            return "❌ ALERTA: Você tentou adicionar um item, mas não enviou nem a lista 'itens' nem o 'produto_nome'. Tente novamente."


    return None