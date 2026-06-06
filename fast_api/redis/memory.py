# -> Implementação pronta de histórico de mensagens usando Redis
# -> Guarda mensagens no formato LangChain (HumanMessage / AIMessage)
from langchain_community.chat_message_histories import RedisChatMessageHistory

# -> URL de conexão com Redis (vem do .env)
from fast_api.core.config.configapi import settings


def get_session_history(session_id):
    # -> Retorna um objeto de histórico de conversa ligado a uma sessão específica
    #
    # -> session_id normalmente é algo como:
    # -> "tenant_id:chat_id"
    #
    # -> Isso garante que:
    # -> - cada conversa tem seu próprio histórico
    # -> - o histórico persiste entre mensagens
    # -> - se o processo reiniciar, o histórico não se perde (Redis)
    return RedisChatMessageHistory(
        session_id=session_id,  # -> chave única da conversa
        url=settings.REDIS_URL,# -> conexão com o Redis
        key_prefix="lc_history",
        ttl=3600
    )
