from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from langgraph.graph.message import RemoveMessage

from core.agent.model import IntentRouter
from core.agent.state import AgentState
from core.data.database.model.restaurant.product import Produto
from core.data.database.conection.conection_orm import get_db
from core.utils.agent_util import formatar_cardapio_whatsapp


from core.agent.service_tool import (
    consultar_cardapio_state,
    lancar_pedido_sistema_state, 
    enviar_resumo_pedido_state
)

def log(*args):
    print("[NODES]", *args, flush=True)

llm_router = ChatOpenAI(model="gpt-5.4-mini-2026-03-17", temperature=0)
llm_chat = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

async def router_node(state: AgentState) -> dict:
    """Detecta intenção usando LLM com Structured Output"""
    last_msg = state["messages"][-1].content
    passo_atual = state.get("current_step", "MENU")

    prompt = ChatPromptTemplate.from_messages([
        ("system", 
        f"""Você é o cérebro de roteamento de uma lanchonete.
            Sua função é classificar a intenção do cliente com extrema precisão e extrair entidades.

            === CONTEXTO CRÍTICO ===
            FASE ATUAL DO CLIENTE: '{passo_atual}'
            ========================

            🚨 REGRA DE OURO PARA RESPOSTAS CURTAS ("Sim", "Ok", "Pode mandar", "Isso"):
            Quando o cliente responde apenas confirmando, a intenção DEPENDE da FASE ATUAL:
            - Se FASE ATUAL for 'OFERECEU_CARDAPIO' -> A intenção é 'ver_cardapio'.
            - Se FASE ATUAL for 'AGUARDANDO_CONFIRMACAO' -> A intenção é 'confirmar_pedido'.
            - Se FASE ATUAL for 'AWAITING_CHECKOUT' -> A intenção é 'confirmar_pedido'.

            REGRAS GERAIS DE CLASSIFICAÇÃO:
            1. 'saudacao': Apenas "oi", "bom dia", "boa noite", "tudo bem?".
            2. 'ver_cardapio': Pede o menu, quer saber o que vende (ou diz "sim" na fase OFERECEU_CARDAPIO).
            3. 'adicionar_item': Quer INCLUIR algo. ATENÇÃO: Só extraia para 'itens_extraidos' se for o nome real de um produto. Se disser "outro", "mais um", classifique a intenção, mas deixe os itens VAZIOS.
            4. 'remover_item': Quer tirar algo do pedido.
            5. 'informar_dados': Passando dados de entrega/pagamento (Pix, Cartão, Dinheiro, nome da rua, retirar no balcão). Extraia para 'tipo_entrega', 'endereco', 'forma_pagamento', 'troco_para'. (Se tiver endereço na frase, é SEMPRE informar_dados).
            6. 'checkout': Quer fechar a conta, ir para o pagamento, ou disse "só isso", "finalizar".
            7. 'confirmar_pedido': Está confirmando que o resumo está correto (ou diz "sim" na fase AGUARDANDO_CONFIRMACAO).
            8. 'duvida_geral': Perguntas ou assuntos que não se encaixam acima.

            Siga estritamente este mapeamento."""),
        ("human", "Mensagem do cliente: {user_input}")
    ])

    chain = prompt | llm_router.with_structured_output(IntentRouter)

    try:
        resultado = await chain.ainvoke({"user_input": last_msg})
    except Exception as e:
        log(f"Erro no LLM Router: {e}")
        return {"last_intent": "fallback"}
    
    
    # Validação rígida
    if resultado.endereco or resultado.forma_pagamento:
        resultado.intent = "informar_dados"

    # Cria um dicionário 
    updates = {
        "last_intent": resultado.intent,
        "temp_items": resultado.itens_extraidos,
        "termo_busca": resultado.termo_busca_cardapio,
        "tipo_entrega": resultado.tipo_entrega,
        "endereco": resultado.endereco,
        "forma_pagamento": resultado.forma_pagamento,
        "troco_para": resultado.troco_para
    }

    # Retorna as chaves que não são nulas para não sobrescrever o state com 'None'
    return {k: v for k, v in updates.items() if v is not None}


async def greeting_node(state: AgentState) -> dict:
    mensagem_usuario = state["messages"][-1].content
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Você é o garçom virtual super simpático da lanchonete. Dê boas-vindas curtas e pergunte se quer ver o cardápio. Use emojis."),
        ("human", "{texto}")
    ])
    chain = prompt | llm_chat
    resposta = await chain.ainvoke({"texto": mensagem_usuario})
    return {
        "messages": [
            AIMessage(
                content=resposta.content
                )
            ],
        "current_step": "OFERECEU_CARDAPIO"
        }


async def menu_node(state: AgentState) -> dict:
    termo = state.get("termo_busca", "")
    cardapio_response = await consultar_cardapio_state(
        tenant_id = state["tenant_id"],
        turno_especifico = str(state["status"]),
        termo_busca = termo,
    )
    cardapio_response_format = formatar_cardapio_whatsapp(cardapio_response)
    return {
        "messages": [
            AIMessage(
                content=str(
                    cardapio_response_format
                    )
                )
            ]
        }


async def cart_node(state: AgentState) -> dict:
    """Gerencia carrinho 100% no State (Sem Redis)"""
    itens_extraidos = state.get("temp_items") or []

    if not itens_extraidos:
        resposta = AIMessage(content="Poderia me confirmar o nome exato do item e a quantidade que deseja adicionar? 🤔")
        return {"messages": [resposta]}

    chegou_remover = state.get("last_intent") == "remover_item"
    carrinho_atual = state.get("cart", []) or []
    tenant_id = state["tenant_id"]

    resultados_sistema = []
    db = next(get_db())
    
    try:
        for item in itens_extraidos:
            if isinstance(item, dict):
                nome_req = item.get("nome_produto", "")
                qtd_req = int(item.get("quantidade", 1))
            else:
                nome_req = getattr(item, "nome_produto", "")
                qtd_req = int(getattr(item, "quantidade", 1))
                
            if not nome_req: continue

            if chegou_remover:
                item_encontrado = next((i for i in carrinho_atual if i["nome"].lower() == nome_req.lower()), None)
                if item_encontrado:
                    if item_encontrado["qty"] > qtd_req:
                        item_encontrado["qty"] -= qtd_req
                        resultados_sistema.append(f"Sucesso: Removido {qtd_req}x de '{nome_req}'.")
                    else:
                        carrinho_atual.remove(item_encontrado)
                        resultados_sistema.append(f"Sucesso: '{nome_req}' removido do carrinho.")
                else:
                    resultados_sistema.append(f"Erro: '{nome_req}' não estava no carrinho.")
            else:
                produto_db = db.query(Produto).filter(
                    Produto.nome.ilike(f"%{nome_req}%"),
                    Produto.tenant_id == tenant_id
                ).first()

                if produto_db:
                    item_existente = next((i for i in carrinho_atual if i["nome"] == produto_db.nome), None)
                    if item_existente:
                        item_existente["qty"] += qtd_req 
                    else:
                        carrinho_atual.append({
                            "nome": produto_db.nome,
                            "qty": qtd_req,
                            "preco": float(produto_db.preco)
                        })
                    resultados_sistema.append(f"Sucesso: {qtd_req}x '''{produto_db.nome}''' adicionado.")
                else:
                    resultados_sistema.append(f"Erro: '''{nome_req}''' não encontrado no cardápio.")
    finally:
        db.close()

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Você é o garçom virtual da lanchonete.
            Ocorreu o seguinte evento no sistema: '{retorno_sistema}'.
            REGRAS:
            1. Fale DIRETAMENTE com o cliente.
            2. Se for ERRO, avise educadamente.
            3. Se for SUCESSO, confirme o que foi alterado."""),
        ("human", "Responda ao cliente agora.")
    ])

    texto_resultado = " | ".join(resultados_sistema)
    log("Ação do Carrinho:", texto_resultado)
    
    chain = prompt | llm_chat
    resposta_amigavel = await chain.ainvoke({"retorno_sistema": texto_resultado})

    return {
        "cart": carrinho_atual,
        "messages": [AIMessage(content=resposta_amigavel.content)],
        "temp_items": [] # Esvazia temporários
    }

async def checkout_node(state: AgentState) -> dict:
    """Coleta dados e gera o resumo (sem chamar a tool de redis)"""
    dados_faltantes = []
    tipo_entrega = state.get("tipo_entrega")
    
    if not tipo_entrega:
        dados_faltantes.append("se o pedido é para Entrega ou Retirada no Balcão")
    elif tipo_entrega.upper() == "DELIVERY" and not state.get("endereco"):
        dados_faltantes.append("o endereço completo para entrega")

    if not state.get("forma_pagamento"):
        dados_faltantes.append("a forma de pagamento (Pix, Cartão ou Dinheiro e se precisa de troco)")

    if dados_faltantes:
        itens_para_pedir = ", ".join(dados_faltantes)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "O cliente quer fechar, mas faltam estas informações: '{itens_para_pedir}'. Peça os dados de forma curta e direta."),
            ("human", "Peça os dados ao cliente sem rodeios.")
        ])
        chain = prompt | llm_chat
        resposta = await chain.ainvoke({"itens_para_pedir": itens_para_pedir})
        return {
            "current_step": "AWAITING_CHECKOUT",
            "messages": [AIMessage(content=resposta.content)]
        }

    # Gera a string do resumo do pedido para enviar ao cliente (precisa ler do 'state["cart"]')
    texto_resumo = await enviar_resumo_pedido_state(
        tenant_id=state["tenant_id"], 
        itens=state.get("cart", []), 
        entrega=tipo_entrega, 
        pagamento=state.get("forma_pagamento")
    )

    mensagem_final = f"{texto_resumo}\n\nEstá tudo certo para confirmarmos? 👍"

    return {
        "current_step": "AGUARDANDO_CONFIRMACAO",
        "messages": [AIMessage(content=mensagem_final)]
    }


async def confirm_node(state: AgentState) -> dict:
    """Confirmação final enviando variáveis do State para a função"""
    result = await lancar_pedido_sistema_state(
        tenant_id=state["tenant_id"],
        chat_id=state["chat_id"],
        name_cliente=state["name_cliente"],
        tipo_entrega=state.get("tipo_entrega", ""),
        forma_pagamento=state.get("forma_pagamento", ""),
        endereco_entrega=state.get("endereco", ""),
        troco_para=state.get("troco_para", "0.0"),
        itens_carrinho=state.get("cart", [])
    )
    
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """O sistema tentou finalizar o pedido e retornou isso: '{retorno_sistema}'.
            REGRAS:
            1. Se for erro, peça desculpas.
            2. Se for sucesso, informe que foi para a cozinha e agradeça!"""),
        ("human", "Responda ao cliente agora.")
    ])

    chain = prompt | llm_chat
    resposta_amigavel = await chain.ainvoke({"retorno_sistema": str(result)})

    if "Sucesso" in result:
        
        messages_del = [RemoveMessage(id=m.id) for m in state["messages"]]
        new_message =  [AIMessage(content=resposta_amigavel.content)]
        
        messages_update = messages_del + [new_message]
        return {
            "current_step": "FINALIZADO",
            "cart": [],             
            "endereco": "",
            "tipo_entrega": "",        
            "forma_pagamento": "",
            "troco_para": "", 
            "temp_items": [],
            "termo_busca": "",
            "conversation_summary": "",   
            "messages": messages_update
        }
    else:
        return {
            "messages": [AIMessage(content=resposta_amigavel.content)]
        }

async def support_node(state: AgentState) -> dict:
    mensagem_usuario = state["messages"][-1].content
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Responda à dúvida geral de forma curta e gentil. Lembre-o de que pode continuar fazendo o pedido."),
        ("human", "{texto}")
    ])
    chain = prompt | llm_chat
    resposta = await chain.ainvoke({"texto": mensagem_usuario})
    return {"messages": [AIMessage(content=resposta.content)]}

async def summarizer_node(state: AgentState) -> dict:
    cart_items = state.get("cart", []) or []
    itens = ", ".join([f"{i.get('qty', 1)}x {i.get('nome', 'Item')}" for i in cart_items])
    return {"conversation_summary": f"Pedido atual: {itens or 'vazio'}"}