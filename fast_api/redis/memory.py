# -> Implementação pronta de histórico de mensagens usando Redis
# -> Guarda mensagens no formato LangChain (HumanMessage / AIMessage)
from langchain_community.chat_message_histories import RedisChatMessageHistory

# -> URL de conexão com Redis (vem do .env)
from fast_api.core.config.configapi import settings

class trimedRedisHistory(RedisChatMessageHistory):
    def __init__(
        self, 
        session_id:str,
        url:str,
        key_prefix:str,
        ttl: int,
        max_messages: int
        ):
        
        super().__init__(
            session_id = session_id,
            url=url,
            key_prefix=key_prefix,
            ttl=ttl,
            )
        
        self.max_messages = max_messages
        
    @property
    def messages(self):
        
        all_messages = super().messages
        
        return all_messages[-self.max_messages:] if all_messages else []

def get_session_history(session_id):

    return trimedRedisHistory(
        session_id=session_id,
        url=settings.REDIS_URL,
        key_prefix="lc_history",
        ttl=3600,
        max_messages=6
    )