import textwrap
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.redis import RedisSaver
from fast_api.core.config.configapi import settings
from fast_api.core.agent.state import AgentState
from fast_api.core.agent.nodes import (
    router_node, menu_node, cart_node, checkout_node, confirm_node, summarizer_node
)


def get_system_prompt(tenant, status_loja, chat_id, carrinho):
    """Prompt base compartilhado (versão reduzida do antigo)"""
    status_pedido = carrinho.get("status", "MONTANDO_PEDIDO")
    texto_itens = ", ".join([f"{i['qty']}x {i['nome']}" for i in carrinho.get("itens", [])]) or "Vazio"

    if status_pedido == "PRONTO_PARA_RESUMO":
        trava = "🚨 MODO RESTRITO: Não pergunte mais nada. Chame enviar_resumo_pedido e confirme."
    elif status_pedido == "AGUARDANDO_CONFIRMACAO":
        trava = "🚨 MODO CONFIRMAÇÃO: Só aceite 'sim' ou mude se o cliente pedir."
    else:
        trava = "✅ MODO NORMAL: Atenda como garçom atencioso."

    return textwrap.dedent(f"""\
        Você é o assistente virtual da {tenant.nome_fantasia}.
        {trava}
        
        Loja: {tenant.id} | Cliente: {chat_id}
        Turno: {status_loja.get('turno', 'noite')}
        Carrinho atual: {texto_itens}
        
        Responda curto, natural e em português brasileiro. Use emojis com moderação.
    """)


def build_graph(tenant, status_loja, chat_id, carrinho_dados):
    workflow = StateGraph(AgentState)
    
    workflow.add_node("router", router_node)
    workflow.add_node("menu", menu_node)
    workflow.add_node("cart", cart_node)
    workflow.add_node("checkout", checkout_node)
    workflow.add_node("confirm", confirm_node)
    workflow.add_node("summarizer", summarizer_node)
    
    def route(state: AgentState):
        intent = state.get("last_intent", "")
        if intent == "ver_cardapio":
            return "menu"
        if intent == "adicionar_item":
            return "cart"
        if intent == "checkout":
            return "checkout"
        if intent == "confirmar_pedido":
            return "confirm"
        return "menu"
    
    workflow.add_conditional_edges("router", route)
    
    workflow.add_edge("menu", "summarizer")
    workflow.add_edge("cart", "summarizer")
    workflow.add_edge("checkout", "summarizer")
    workflow.add_edge("confirm", "summarizer")
    workflow.add_edge("summarizer", END)
    
    workflow.set_entry_point("router")
    
    checkpointer = RedisSaver.from_conn_info(url=settings.REDIS_URL)
    graph = workflow.compile(checkpointer=checkpointer)
    
    return {
        "graph": graph,
        "system_prompt": get_system_prompt(tenant, status_loja, chat_id, carrinho_dados)
    }