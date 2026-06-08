
from typing import List, Optional, Any, Literal
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from fast_api.redis.cart import add_item_to_cart_state, get_cart_state, clear_cart_state, atualizar_dados_checkout

from fast_api.utils.service_tool import lancar_pedido_sistema_state, consultar_status_pedido_state, \
    consultar_cardapio_state, consultar_preco_produto_state, enviar_resumo_pedido_state


# ==========================================
# 1. SCHEMAS (PYDANTIC) DAS FERRAMENTAS
# ==========================================
class ClienteTenantInput(BaseModel):
    tenant_id: str = Field(description="Tenant ID")
    whatsapp_cliente: str = Field(description="Customer WhatsApp")

class ItemPedidoIA(BaseModel):
    nome_produto: str = Field(description="Product name")
    quantidade: int = Field(description="Quantity")

class LancarPedidoInput(BaseModel):
    tenant_id: str = Field(description="Tenant ID")
    chat_id: str = Field(description="Chat ID")

class CardapioInput(BaseModel):
    tenant_id: str = Field(..., description="Tenant ID")
    turno_especifico: Optional[str] = Field(None, description="Optional: 'dia' or 'noite'.")
    termo_busca: Optional[str] = Field(default=None, description="Category name, or empty to list main categories.")

class CartInput(BaseModel):
    tenant_id: str = Field(description="Tenant ID")
    chat_id: str = Field(description="Chat ID")
    produto_nome: Optional[str] = Field(None, description="Product name")
    produto_preco: Optional[float] = Field(None, description="Product price")
    qty: Optional[int] = Field(None, description="Quantity")

class AcaoCarrinhoInput(BaseModel):
    tenant_id: str
    chat_id: str
    acao: str = Field(description="'adicionar', 'remover', 'alterar', 'consultar', 'checkout' or 'limpar'")
    produto_nome: Optional[str] = Field(None, description="Product name")
    itens: Optional[List[ItemPedidoIA]] = Field(None, description="List of items")
    qty: Optional[int] = Field(None, description="Quantity")
    tipo_entrega: str = Field(description="'DELIVERY' or 'BALCAO'")
    forma_pagamento: str = Field(description="'PIX', 'DINHEIRO', or 'CARTAO'")
    endereco: Optional[str] = Field(None, description="Delivery address. Empty if BALCAO.")
    troco_para: Optional[str] = Field("0.0", description="Change for cash payment. E.g., '50.0'")
# ==========================================
# 2. FERRAMENTAS (TOOLS) PARA O AGENTE
# ==========================================

@tool(args_schema=CartInput)
def consultar_preco_produto(
        tenant_id: str,
        produto_nome: str,
        **kwargs
) -> Any:

    """Gets item price if missing."""
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
    """Gets menu. Leave termo_busca empty for categories, or pass category name for items."""
    consulta_cardapio = consultar_cardapio_state(
            tenant_id,
            turno_especifico,
            termo_busca
    )

    return consulta_cardapio



@tool(args_schema=ClienteTenantInput)
def consultar_status_pedido(tenant_id: str, whatsapp_cliente: str) -> str:
    """Gets order status for the customer."""

    consultar_status = consultar_status_pedido_state(
                                        tenant_id,
                                        whatsapp_cliente
    )

    return consultar_status



@tool(args_schema=LancarPedidoInput)
async def lancar_pedido_sistema(
        tenant_id: str,chat_id: str
) -> str:
    """Saves official order after customer confirmation."""



    lancar_pedido_call = await lancar_pedido_sistema_state(
                    tenant_id,
                    chat_id
    )

    return lancar_pedido_call

@tool()
async def enviar_resumo_pedido(
        tenant_id: str,
        chat_id: str
) -> str:
    """Generates order summary before final confirmation."""
    resumo = await enviar_resumo_pedido_state(
        tenant_id,
        chat_id
    )

    return resumo






@tool(args_schema=AcaoCarrinhoInput)
async def gerenciar_carrinho(
        tenant_id: str,
        chat_id: str,
        acao: str,
        produto_nome: str,
        qty: int,
        tipo_entrega: str,
        endereco: str,
        troco_para: str,
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
            troco_para,
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
            return res

        else:
            return "❌ ALERTA: Você tentou adicionar um item, mas não enviou nem a lista 'itens' nem o 'produto_nome'. Tente novamente."


    return None