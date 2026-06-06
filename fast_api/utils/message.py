

# -> Detecta se o "remote_jid" (chat_id da Evolution) é grupo.
# -> Grupos possuem "@g.us". Retorna True se for grupo.
def is_group(remote_jid: str | None) -> bool:
    return bool(remote_jid) and "@g.us" in remote_jid



def extract_message_evolution(payload: dict) -> tuple[str | None, str | None, str | None]:
    """Returns (chat_id, text, message_id)"""

    # -> A Evolution costuma enviar o payload dentro de payload["data"].
    data = (payload or {}).get("data") or {}

    # -> Dentro de "data", a chave "key" guarda identificadores (remoteJid/id etc.).
    key = (data.get("key") or {})

    # -> remoteJid = identificador do chat (ex: 5511...@s.whatsapp.net ou ...@g.us)
    # -> id = identificador único da mensagem (usado para dedupe).
    remote_jid = key.get("remoteJid")
    message_id = key.get("id")

    # -> "message" contém o conteúdo enviado (texto puro, texto extendido, mídia etc.).
    msg = (data.get("message") or {})

    # -> Vamos tentar encontrar o texto em diferentes formatos possíveis do WhatsApp.
    text = None

    # -> Texto simples (conversation)
    if isinstance(msg.get("conversation"), str):
        text = msg.get("conversation")

    # -> Texto em formato "extendedTextMessage" (muito comum)
    ext = msg.get("extendedTextMessage") or {}

    if not text and isinstance(ext.get("text"), str):
        text = ext.get("text")

    # -> Legenda em mensagens de mídia (imagem/vídeo/documento)
    tipos_media = ["imageMessage", "videoMessage", "documentMessage"]
    for k in tipos_media:
        mm = msg.get(k) or {}
        if not text and isinstance(mm.get("caption"), str):
            text = mm.get("caption")

    # -> Faz strip para remover espaços, e se ficar vazio retorna None.
    return remote_jid, (text or "").strip() or None, message_id


def extract_message_meta(payload: dict) -> tuple[str | None, str | None, str | None]:
    """Returns (chat_id, text, message_id) from Meta Cloud webhook payload."""
    try:
        entry = (payload or {}).get("entry") or []
        changes = (entry[0] or {}).get("changes") or []
        value = (changes[0] or {}).get("value") or {}
        messages = value.get("messages") or []
        if not messages:
            return None, None, None  # statuses/other callbacks

        msg = messages[0] or {}
        chat_id = msg.get("from")
        message_id = msg.get("id")

        text = None
        t = msg.get("text") or {}
        if isinstance(t.get("body"), str):
            text = t.get("body")

        # Basic support for interactive replies
        interactive = msg.get("interactive") or {}
        if not text and isinstance(interactive, dict):
            itype = interactive.get("type")
            if itype == "button_reply":
                br = interactive.get("button_reply") or {}
                text = br.get("title") or br.get("id")
            elif itype == "list_reply":
                lr = interactive.get("list_reply") or {}
                text = lr.get("title") or lr.get("id")

        return (str(chat_id).strip() if chat_id else None), (str(text).strip() if text else None), (str(message_id).strip() if message_id else None)
    except Exception:
        return None, None, None

