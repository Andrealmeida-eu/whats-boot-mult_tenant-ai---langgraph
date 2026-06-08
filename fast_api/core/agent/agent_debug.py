import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from langchain_core.messages import HumanMessage, AIMessage
from openai import OpenAI
from langchain_community.callbacks.manager import get_openai_callback

from fast_api.routes.api_restaurant.gestao_ia import salvar_dados_interacao, GestaoCreate


client = OpenAI()
fuso_sp = ZoneInfo("America/Sao_Paulo")

def log(*args):
    print("[AGENT-DEBUG]", *args, flush=True)
    
def to_openai_messages(messages):
    role_map = {
        "human": "user",
        "ai": "assistant",
        "system": "system",
        "tool": "tool",
    }
    result = []
    for m in messages:
        result.append({
            "role": role_map.get(m.type, "user"),
            "content": m.content
        })
    return result

def count_input_tokens(messages, model):
    result = client.responses.input_tokens.count(
        model=model,
        input=messages
    )
    return result.input_tokens

async def invoke_with_debug(
    chain_with_history,
    get_session_history,
    tenant_id,
    provider,
    chat_id,
    full_message,
):
    session_id = f"{tenant_id}:{chat_id}"

    history = get_session_history(session_id)
    mensagens = history.messages

    print(f"[HISTORY] count ==> {mensagens}")

    if len(mensagens) == 0:
        texto_saudacao = (
            f"Seja Bem-vindo a(o) *{tenant_id.replace("-", " ")}*!\n\n"
            "Eu sou o assistente virtual e estou aqui para agilizar seu pedido.\n\n"
            "Para começar, digite o que você quer comer, ou peça para ver o *Cardápio*."
        )

        await asyncio.to_thread(provider.send_text, chat_id, texto_saudacao)

        history.add_message(HumanMessage(content=full_message))
        history.add_message(AIMessage(content="Automatic greeting sent."))

        return "Greeting bypass executed in a secondary thread."


    with get_openai_callback() as cb:

        ai_response_obj = await chain_with_history.ainvoke(
            {"input": full_message},
            config={
                "configurable": {
                    "session_id": session_id
                }
            },
        )
        log(f"tokens de entrada --> {cb.prompt_tokens}, tokens saida --> {cb.completion_tokens}, total: {cb.total_tokens}, custo: {cb.total_cost}")
        dados_consumo = GestaoCreate(
            tokens_entrada=cb.prompt_tokens,
            tokens_saida=cb.completion_tokens,
            tokens_total=cb.total_tokens,
            custo_dolares=cb.total_cost,
            data_hora=datetime.now(fuso_sp)
        )

        salvar_dados_interacao(
            dados_consumo,
            tenant_id,
        )


    return ai_response_obj