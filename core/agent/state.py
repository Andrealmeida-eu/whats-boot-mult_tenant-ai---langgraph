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
    name_cliente: str
    chat_id: str
    current_step: str        
    status: Any
    cart: List[CartItem]
    
    conversation_summary: Optional[str]
    termo_busca: Optional[str]
    tipo_entrega: Optional[str]
    forma_pagamento: Optional[str]
    endereco: Optional[str]
    troco_para: Optional[str]
    

    temp_items: Optional[List[Any]] 
    last_intent: Optional[str]