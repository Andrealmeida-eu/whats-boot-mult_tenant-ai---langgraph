import asyncio
from contextlib import contextmanager
import redis.asyncio as redis
from fast_api.core.config.configapi import settings
from fast_api.core.agent.agent import build_prompts
from fast_api.core.database.conection.conection_orm import get_db
from fast_api.core.database.model.base_tenant.tenantBase import Tenant
from fast_api.redis.cart import buscar_resumo_carrinho_redis
from fast_api.routes.api_restaurant.funcionamento import verificar_status_e_turno
from fast_api.utils.agent_util import format_ai_output_gem
from fast_api.core.agent.agent_debug import  invoke_with_debug
from providers.factory import get_provider
from fast_api.core.agent.graph_builder import build_graph
from langchain_core.messages import HumanMessage, SystemMessag


redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

debounce_tasks: dict[tuple[str, str], asyncio.Task] = {}
debounce_tokens: dict[tuple[str, str], int] = {}
chains_cache: dict[str, object] = {}

graphs_cache = {}

def log(*args):
    print("[BUFFER]", *args, flush=True)

def _task_done(t: asyncio.Task, tenant_id: str, chat_id: str):
    try:
        if t.cancelled():
            log(f"[DEBOUNCE] cancelada {tenant_id}:{chat_id}")
            return
        exc = t.exception()
        if exc:
            log(f"[DEBOUNCE] ERRO {tenant_id}:{chat_id} -> {type(exc).__name__}: {exc}")
        else:
            log(f"[DEBOUNCE] finalizou ok {tenant_id}:{chat_id}")
    except Exception as e:
        log(f"[DEBOUNCE] erro ao ler resultado da task: {e!r}")

async def buffer_message(tenant_id: str, chat_id: str, message: str):
    key = (tenant_id, chat_id)
    buffer_key = f"{tenant_id}:{chat_id}{settings.BUFFER_KEY_SUFIX}"

    await redis_client.rpush(buffer_key, message)
    await redis_client.expire(buffer_key, settings.BUFFER_TTL)
    log(f"Mensagem adicionada ao buffer de {tenant_id}:{chat_id}: {message}")

    # cancela task anterior
    old = debounce_tasks.get(key)
    log(f"task do debounce: {old}")
    if old and not old.done():
        old.cancel()
        log(f"Debounce resetado para {tenant_id}:{chat_id}")

    # token anti-corrida
    debounce_tokens[key] = debounce_tokens.get(key, 0) + 1
    token = debounce_tokens[key]

    loop = asyncio.get_running_loop()


    t = loop.create_task(handle_debounce(tenant_id, chat_id, token))
    t.add_done_callback(lambda tt: _task_done(tt, tenant_id, chat_id))
    debounce_tasks[key] = t


async def handle_debounce(tenant_id: str, chat_id: str, token: int):
    key = (tenant_id, chat_id)
    buffer_key = f"{tenant_id}:{chat_id}{settings.BUFFER_KEY_SUFIX}"

    # PROVA “hard” de que entrou
    print(f"[DEBOUNCE] ENTROU {tenant_id}:{chat_id} token={token}", flush=True)

    with contextmanager(get_db)() as db:
        try:

                tenant = await asyncio.to_thread(
                    lambda: db.query(Tenant).filter(Tenant.id == tenant_id).first()
                )

                if not tenant:
                    log(f"ERRO: Tenant {tenant_id} não encontrado no banco.")
                    return
                if not tenant.ativo:
                    log(f"Aviso: Tenant {tenant_id} está inativo. Ignorando mensagens.")
                    return

                provider = get_provider(tenant)


                log(f"[DEBOUNCE] Iniciando debounce para {tenant_id}:{chat_id} token={token}")
                await asyncio.sleep(float(settings.DEBOUNCE_SECONDS))

                # se chegou mensagem nova, não envia
                if debounce_tokens.get(key) != token:
                    log(f"[DEBOUNCE] Task antiga ignorada {tenant_id}:{chat_id} token={token}")
                    return

                messages = await redis_client.lrange(buffer_key, 0, -1)
                full_message = " ".join(messages).strip()

                if not full_message:
                    log(f" [DEBOUNCE] Buffer vazio {tenant_id}:{chat_id}")
                    return

                status_loja = verificar_status_e_turno(tenant_id, db)


                if not status_loja["aberto"]:
                    mensagem_fechado = f"Olá! O *{tenant.nome_fantasia}* está fechado no momento. 😴 Voltamos mais tarde!"
                    await asyncio.to_thread(provider.send_text, chat_id, mensagem_fechado)
                    await redis_client.delete(buffer_key)
                    log(f"Loja fechada. Resposta automática enviada para {chat_id}")
                    return

                status = status_loja

                carrinho_dados = await buscar_resumo_carrinho_redis(tenant.id, chat_id)
                log(f"carrinho resumo: {carrinho_dados}")
                
                cache_key = f"{tenant_id}:{chat_id}"
                
                if cache_key not in graphs_cache:
                    graphs_cache[cache_key] = build_graph(
                        tenant,
                        status,
                        chat_id,
                        carrinho_dados
                    )
                    
                graphs_ctx = graphs_cache[cache_key]
                graph = graphs_ctx["graph"]
                
                config = {
                    "configurable": {
                        "thread_id": f"{tenant_id}:{chat_id}"
                    }
                }
                
                input_state = {
                    "messages": [
                        HumanMessage(
                            content=full_message
                            )
                        ],
                    
                    "tenant_id": tenant_id,
                    "chat_id": chat_id,
                    "current_step": "MENU",
                    "cart": []
                    
                }
                
                result_graph = await graph.ainvoke(
                    input_state,
                    config=config
                )
                
                
                log(f"chamarei o invoke")
                
                ai_response = result_graph["messages"][-1]

                log(f"voltei do invoke")

                response = ai_response.replace('**', '*')
                log(f"voltei das formatação")

                result = await asyncio.to_thread(provider.send_text, chat_id, response)
                log("[SEND] ok:", result)

                await redis_client.delete(buffer_key)
                log(f"[DEBOUNCE] Enviado e limpo buffer {tenant_id}:{chat_id}")

        except asyncio.CancelledError:
            log(f"[DEBOUNCE] Debounce cancelado para {tenant_id}:{chat_id}")
            raise
        finally:
            # limpa referência se essa task ainda for a atual
            t = debounce_tasks.get(key)
            if t is asyncio.current_task():
                if key in debounce_tasks:
                    del debounce_tasks[key]


