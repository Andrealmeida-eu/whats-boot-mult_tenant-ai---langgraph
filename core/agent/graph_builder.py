from langgraph.graph import StateGraph, END
from langgraph.checkpoint.redis import AsyncRedisSaver
from langchain_core.runnables import RunnableConfig
from core.config.configapi import settings
from core.agent.state import AgentState
from core.agent.nodes import (
    router_node, greeting_node, menu_node, cart_node, checkout_node, confirm_node, summarizer_node, support_node
)

async def build_graph():
    """Constrói e compila o grafo de execução principal"""
    workflow = StateGraph(AgentState)
    
    # 1. Registro dos Nós 
    workflow.add_node("router", router_node)
    workflow.add_node("greeting", greeting_node)
    workflow.add_node("menu", menu_node)
    workflow.add_node("cart", cart_node)
    workflow.add_node("checkout", checkout_node)
    workflow.add_node("confirm", confirm_node)
    workflow.add_node("support", support_node) 
    workflow.add_node("summarizer", summarizer_node)
    
    # 2. Lógica de Roteamento Condicional Completa
    def route(state: AgentState):
        intent = state.get("last_intent", "")
        
        if intent == "ver_cardapio":
            return "menu"
        if intent in ["adicionar_item", "remover_item"]: 
            return "cart"
        if intent in ["checkout", "informar_dados"]:    
            return "checkout"
        if intent == "confirmar_pedido":
            return "confirm"
        if intent == "duvida_geral":
            return "support"
            
        # Fallback padrão (saudacao ou não reconhecido)
        return "greeting"
    
    workflow.add_conditional_edges("router", route)
    
    # 3. Fluxo de convergência para o Summarizer
    workflow.add_edge("greeting", "summarizer")
    workflow.add_edge("support", "summarizer")
    workflow.add_edge("menu", "summarizer")
    workflow.add_edge("cart", "summarizer")
    workflow.add_edge("checkout", "summarizer")
    workflow.add_edge("confirm", "summarizer")
    workflow.add_edge("summarizer", END)
    
    workflow.set_entry_point("router")
    
    print("Conectando ao checkpointer Redis...")
    checkpointer = AsyncRedisSaver(settings.REDIS_URL)
    await checkpointer.setup()
    
    graph = workflow.compile(checkpointer=checkpointer)
    
   
    return graph

# ==========================================
# PARA O LANGGRAPH STUDIO (DESENVOLVIMENTO)
# ==========================================
async def build_studio_graph(config: RunnableConfig):
    """
    Função de fábrica simplificada exclusiva para o LangGraph Studio.
    Retorna apenas o grafo compilado.
    """
    workflow = StateGraph(AgentState)
    
    workflow.add_node("router", router_node)
    workflow.add_node("greeting", greeting_node)
    workflow.add_node("menu", menu_node)
    workflow.add_node("cart", cart_node)
    workflow.add_node("checkout", checkout_node)
    workflow.add_node("confirm", confirm_node)
    workflow.add_node("support", support_node) 
    workflow.add_node("summarizer", summarizer_node)
    
    def route(state: AgentState):
        intent = state.get("last_intent", "")
        
        if intent == "ver_cardapio":
            return "menu"
        if intent in ["adicionar_item", "remover_item"]: 
            return "cart"
        if intent in ["checkout", "informar_dados"]:     
            return "checkout"
        if intent == "confirmar_pedido":
            return "confirm"
        if intent == "duvida_geral":
            return "support"
            
        return "greeting"
    
    workflow.add_conditional_edges("router", route)
    
    workflow.add_edge("greeting", "summarizer")
    workflow.add_edge("support", "summarizer")
    workflow.add_edge("menu", "summarizer")
    workflow.add_edge("cart", "summarizer")
    workflow.add_edge("checkout", "summarizer")
    workflow.add_edge("confirm", "summarizer")
    workflow.add_edge("summarizer", END)
    
    workflow.set_entry_point("router")
    
    checkpointer = AsyncRedisSaver(settings.REDIS_URL)
    await checkpointer.setup()
    
    return workflow.compile(checkpointer=checkpointer)