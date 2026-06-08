from langchain_core.messages import AIMessage
from fast_api.core.agent.state import AgentState
from fast_api.core.agent.tools import (
    consultar_cardapio, 
    gerenciar_carrinho, 
    enviar_resumo_pedido, 
    lancar_pedido_sistema
)
from fast_api.redis.cart import buscar_resumo_carrinho_redis
from fast_api.utils.service_tool import verificar_status_e_turno

async def router_node(state: AgentState) -> AgentState:
    """Detecta intenção e define o próximo passo"""
    last_msg = state["messages"][-1].content.lower().strip()
    
    if any(x in last_msg for x in ["cardapio", "menu", "bebidas", "lanches", "ver"]):
        state["last_intent"] = "ver_cardapio"
        state["current_step"] = "MENU"
    elif any(x in last_msg for x in ["quero", "adicionar", "1x", "2x", "3x", "morango", "coca"]):
        state["last_intent"] = "adicionar_item"
        state["current_step"] = "BUILDING_CART"
    elif any(x in last_msg for x in ["só isso", "finalizar", "pronto", "delivery", "pix", "endereco"]):
        state["last_intent"] = "checkout"
        state["current_step"] = "AWAITING_CHECKOUT"
    elif any(x in last_msg for x in ["sim", "confirmar", "pode", "manda", "tudo certo"]):
        state["last_intent"] = "confirmar_pedido"
    else:
        state["last_intent"] = "fallback"
    
    return state


async def menu_node(state: AgentState) -> AgentState:
    """Apresenta o cardápio"""
    result = consultar_cardapio(
        tenant_id=state["tenant_id"],
        turno_especifico=verificar_status_e_turno(state["tenant_id","chat_id"]),         
        termo_busca=state["messages"][-1].content
    )
    state["messages"].append(AIMessage(content=str(result)))
    return state


async def cart_node(state: AgentState) -> AgentState:
    """
    Gerencia carrinho
    """
    # Aqui você pode melhorar o parsing da mensagem (ex: extrair quantidade e nome)
    # Por enquanto usa a mensagem inteira como exemplo
    result = await gerenciar_carrinho(
        tenant_id=state["tenant_id"],
        chat_id=state["chat_id"],
        acao="adicionar",
        itens=None,
        produto_nome=state["messages"][-1].content,
        qty=1,
        tipo_entrega=state.get("tipo_entrega", "BALCAO"),
        forma_pagamento=state.get("forma_pagamento", "PIX"),
        endereco=state.get("endereco", ""),
        troco_para=state.get("troco_para", "0.0")
    )
    
    # Atualiza o carrinho no estado
    cart_data = await buscar_resumo_carrinho_redis(state["tenant_id"], state["chat_id"])
    state["cart"] = cart_data.get("itens", [])
    state["messages"].append(AIMessage(content=str(result)))
    return state


async def checkout_node(state: AgentState) -> AgentState:
    """Coleta dados e salva checkout (STEP 4)"""
    await gerenciar_carrinho(
        tenant_id=state["tenant_id"],
        chat_id=state["chat_id"],
        acao="checkout",
        tipo_entrega=state.get("tipo_entrega", "DELIVERY"),
        forma_pagamento=state.get("forma_pagamento", "PIX"),
        endereco=state.get("endereco", ""),
        troco_para=state.get("troco_para", "0.0"),
        produto_nome=None,
        qty=None,
        itens=None
    )
    
    await enviar_resumo_pedido(state["tenant_id"], state["chat_id"])
    state["current_step"] = "AGUARDANDO_CONFIRMACAO"
    state["messages"].append(AIMessage(content="Resumo do pedido enviado! Está tudo certo para confirmar?"))
    return state


async def confirm_node(state: AgentState) -> AgentState:
    """Confirmação final do pedido"""
    result = await lancar_pedido_sistema(state["tenant_id"], state["chat_id"])
    state["current_step"] = "FINALIZADO"
    state["messages"].append(AIMessage(content=str(result)))
    return state


async def summarizer_node(state: AgentState) -> AgentState:
    """Resumidor em background (economiza tokens nos próximos turnos)"""
    itens = ", ".join([f"{i.get('qty')}x {i.get('nome')}" for i in state.get("cart", [])])
    state["conversation_summary"] = f"Pedido atual: {itens or 'vazio'}"
    return state