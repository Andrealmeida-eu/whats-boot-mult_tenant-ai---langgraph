from langchain_core.messages import AIMessage
from fast_api.core.agent.state import AgentState
from fast_api.core.agent.model import IntentRouter
from fast_api.core.agent.tools import (
    consultar_cardapio, 
    gerenciar_carrinho, 
    enviar_resumo_pedido, 
    lancar_pedido_sistema
)
from fast_api.redis.cart import buscar_resumo_carrinho_redis
from fast_api.utils.service_tool import verificar_status_e_turno
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI # Ou a biblioteca do modelo que você usa
# from fast_api.core.config.configapi import settings # Para pegar a API KEY se necessário

llm_router = ChatOpenAI(model="gpt-4o-mini", temperature=0)

llm_chat = ChatOpenAI(model="gpt-4o-mini", temperature=0.7) # Um pouco de criatividade para falar

async def router_node(state: AgentState) -> AgentState:
    """Detecta intenção usando LLM com Structured Output"""
    last_msg = state["messages"][-1].content
    
    # 1. Cria um prompt rápido para guiar o roteador
    prompt = ChatPromptTemplate.from_messages([
        (
            "system", """Você é o cérebro de roteamento de uma lanchonete.
                Sua função é classificar a intenção do cliente com extrema precisão e preencher os campos corretamente.

                REGRAS RÍGIDAS:
                1. SAUDAÇÃO ('saudacao'): O cliente disse apenas "oi", "bom dia", "tudo bem?".
                2. VER CARDÁPIO ('ver_cardapio'): O cliente quer saber o que a loja vende. 
                - Se for geral ("cardapio", "o que tem"): deixe 'termo_busca_cardapio' VAZIO.
                - Se for específico ("quais as bebidas?", "tem sobremesa?"): coloque a palavra em 'termo_busca_cardapio' (ex: "bebidas", "sobremesa").
                3. ADICIONAR ITEM ('adicionar_item'): O cliente quer INCLUIR algo no pedido ("quero 1 coca", "me ve um x-tudo", "vou querer batata").
                - OBRIGATÓRIO: Liste os itens pedidos e quantidades em 'itens_extraidos' (Ex: ["1x coca", "1x x-tudo"]).
                - NUNCA preencha 'termo_busca_cardapio' aqui.
                4. CHECKOUT ('checkout'): Cliente quer encerrar, fechar a conta, pagar, ou disse "só isso".

                Siga estritamente essas regras."""
        ),
        ("human", "Mensagem do cliente: {user_input}")
    ])
    
    # 2. Força o LLM a responder no formato do Pydantic
    chain = prompt | llm_router.with_structured_output(IntentRouter)
    
    # 3. Executa a análise
    try:
        resultado = await chain.ainvoke({"user_input": last_msg})
    except Exception as e:
        # Fallback de segurança caso a API falhe
        print(f"Erro no LLM Router: {e}")
        state["last_intent"] = "fallback"
        return state

    # 4. Atualiza o estado com a inteligência extraída
    state["last_intent"] = resultado.intent
    
    # Mapeia os steps de acordo com a intenção
    if resultado.intent == "ver_cardapio":
        state["current_step"] = "MENU"
        state["termo_busca"] = resultado.termo_busca_cardapio or ""
    
    elif resultado.intent == "adicionar_item":
        state["current_step"] = "BUILDING_CART"
        # BÔNUS: Salvamos os itens extraídos no estado temporariamente!
        # Você pode criar uma chave "temp_items" no seu AgentState (TypedDict) para isso
        state["temp_items"] = resultado.itens_extraidos 
    
    elif resultado.intent == "checkout":
        state["current_step"] = "AWAITING_CHECKOUT"
        
    elif resultado.intent == "confirmar_pedido":
        state["current_step"] = "AGUARDANDO_CONFIRMACAO"
        
    return state




async def greeting_node(state: AgentState) -> AgentState:
    """Nó exclusivo para dar boas-vindas e manter o tom amigável"""
    mensagem_usuario = state["messages"][-1].content
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Você é o garçom virtual super simpático da lanchonete. O cliente acabou de mandar uma mensagem. Responda de forma bem curta, dê as boas-vindas e pergunte se ele quer ver o cardápio ou fazer um pedido. Use emojis."),
        ("human", "{texto}")
    ])
    
    chain = prompt | llm_chat
    
    # A IA gera a resposta amigável
    resposta = await chain.ainvoke({"texto": mensagem_usuario})
    
    # Salvamos a resposta falada no estado para ser enviada ao WhatsApp
    state["messages"].append(AIMessage(content=resposta.content))
    return state

async def menu_node(state: AgentState) -> AgentState:
    """Apresenta o cardápio"""
    termo = state.get("termo_busca", "")
    result = consultar_cardapio.invoke({
        "tenant_id": state["tenant_id"],
        "turno_especifico": str(state["status"]), # Convertendo para string por precaução       
        "termo_busca": termo
    })
    
    state["messages"].append(AIMessage(content=str(result)))
    return state

async def cart_node(state: AgentState) -> AgentState:
    """Gerencia carrinho"""
    # Envolva os argumentos com { }
    result = await gerenciar_carrinho.ainvoke({
        "tenant_id": state["tenant_id"],
        "chat_id": state["chat_id"],
        "acao": "adicionar",
        "itens": None,
        "produto_nome": state["messages"][-1].content,
        "qty": 1,
        "tipo_entrega": state.get("tipo_entrega", "BALCAO"),
        "forma_pagamento": state.get("forma_pagamento", "PIX"),
        "endereco": state.get("endereco", ""),
        "troco_para": state.get("troco_para", "0.0")
    })
    
    # Atualiza o carrinho no estado
    cart_data = await buscar_resumo_carrinho_redis(state["tenant_id"], state["chat_id"])
    state["cart"] = cart_data.get("itens", [])
    state["messages"].append(AIMessage(content=str(result)))
    return state

async def checkout_node(state: AgentState) -> AgentState:
    """Coleta dados e salva checkout (STEP 4)"""
    # Envolva os argumentos com { }
    await gerenciar_carrinho.ainvoke({
        "tenant_id": state["tenant_id"],
        "chat_id": state["chat_id"],
        "acao": "checkout",
        "tipo_entrega": state.get("tipo_entrega", "DELIVERY"),
        "forma_pagamento": state.get("forma_pagamento", "PIX"),
        "endereco": state.get("endereco", ""),
        "troco_para": state.get("troco_para", "0.0"),
        "produto_nome": None,
        "qty": None,
        "itens": None
    })
    
    # IMPORTANTE: enviar_resumo_pedido também é uma tool! Passe como dicionário:
    await enviar_resumo_pedido.ainvoke({
        "tenant_id": state["tenant_id"], 
        "chat_id": state["chat_id"]
    })
    
    state["current_step"] = "AGUARDANDO_CONFIRMACAO"
    state["messages"].append(AIMessage(content="Resumo do pedido enviado! Está tudo certo para confirmar?"))
    return state

async def confirm_node(state: AgentState) -> AgentState:
    """Confirmação final do pedido"""
    # Envolva os argumentos com { } e use as chaves correspondentes ao esquema da Tool
    result = await lancar_pedido_sistema.ainvoke({
        "tenant_id": state["tenant_id"], 
        "chat_id": state["chat_id"]
    })
    
    state["current_step"] = "FINALIZADO"
    state["messages"].append(AIMessage(content=str(result)))
    return state


async def summarizer_node(state: AgentState) -> AgentState:
    """Resumidor em background (economiza tokens nos próximos turnos)"""
    itens = ", ".join([f"{i.get('qty')}x {i.get('nome')}" for i in state.get("cart", [])])
    state["conversation_summary"] = f"Pedido atual: {itens or 'vazio'}"
    return state