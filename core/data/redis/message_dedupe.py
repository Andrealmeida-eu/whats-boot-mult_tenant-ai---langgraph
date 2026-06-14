from __future__ import annotations

import redis.asyncio as redis

from core.config.configapi import settings

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

#   -> valida se a mensagem é duplicada 
async def dedupe_check_and_mark(tenant_id: str, message_id: str) -> bool:
    """Returns True if message is new; False if already seen."""
    
#   -> se message_id é falso entao é uma mensagem nova, retorna true e esta feito
    if not message_id:
        return True
    
#   -> se ja existe o id ele cria uma chave unica
    key = f"dedupe:{tenant_id}:{message_id}"
    
#   -> seta se nao existe depois ignora o restante
    was_set = await redis_client.setnx(key, "1")
    
#   -> se ja foi setado coloca um tempo de expiração que excluira a key
    if was_set:
        await redis_client.expire(key, int(settings.BUFFER_TTL))
        return True
    return False
