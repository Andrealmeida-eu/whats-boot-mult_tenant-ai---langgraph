from typing import TypedDict, List, Optional, Annotated, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class CartItem(TypedDict):
    nome: str
    qty: int
    preco: float


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    
    tenant_id: str
    chat_id: str
    current_step: str          # MENU | BUILDING_CART | AWAITING_CHECKOUT | AGUARDANDO_CONFIRMACAO | FINALIZADO
    status: Any
    cart: List[CartItem]
    conversation_summary: str = ""
    termo_busca: str
    tipo_entrega: Optional[str] = None
    forma_pagamento: Optional[str] = None
    endereco: Optional[str] = None
    troco_para: Optional[str] = None
    
    last_intent: str = ""