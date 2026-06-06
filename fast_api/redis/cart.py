
import redis.asyncio as redis
from rich import json

from fast_api.core.config.configapi import settings
from fast_api.core.database.conection.conection_orm import get_db
from fast_api.core.database.model.restaurant.product import Produto

client = redis.Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True
)

CART_TTL = 3600


def log(*args):
    print("[CART]", *args, flush=True)

def cart_key(
        tenant_id:str,
        chat_id:str
) -> str:
    return f"CART:{tenant_id}:{chat_id}"




async def add_item_to_cart_state(
        tenant_id: str,
        chat_id: str,
        produto_nome: str,
        qty: int
):

    log(f"Adicionando item ao carrinho =====> tenant-id: {tenant_id}, chat_id:, produto: {produto_nome}, quantidade: {qty}")
    key = cart_key(tenant_id, chat_id)

    db = next(get_db())
    try:
        produto = db.query(Produto).filter(
            Produto.nome.icontains(produto_nome, autoescape=True),
            Produto.tenant_id == tenant_id
        ).all()
    finally:
        db.close()

    for prod in produto:
        log(f" produto ilike: {prod.nome}")

    if not produto:
        return f"❌ AI ALERT: The item '{produto_nome}' does not exist on the menu. Inform the customer that we do not carry this and ask them to choose another valid option."

    if len(produto) > 1:
        options = ", ".join([p.nome for p in produto])
        return f"❌ AI ALERT: I found SEVERAL options for '{produto_nome}': {options}. Ask the customer EXACTLY which one of these options they would like."

    produto_exato = produto[0]
    preco_final = produto_exato.preco
    nome_real = produto_exato.nome

    item_existente = await client.hget(key, nome_real)

    if item_existente:
        dados_item = json.loads(item_existente)
        dados_item["qty"] += qty
    else:
        # Se é novo, monta o objeto completo
        dados_item = {
            "preco": float(preco_final),
            "qty": qty
        }

    # 2. Salva o objeto como uma string JSON dentro do HSET
    await client.hset(key, produto_nome, json.dumps(dados_item))
    await client.expire (key, CART_TTL)

    return f"Success! {qty}x {nome_real} successfully added to the cart."


async def set_item_quantity_state(
        tenant_id: str,
        chat_id: str,
        produto_nome: str,
        qty: int
):
    log(f"Mudando item do carrinho =====> tenant-id: {tenant_id}, chat_id: {chat_id}, produto: {produto_nome}, quantidade: {qty}")
    key = cart_key(tenant_id, chat_id)

    if qty <= 0:
        await client.hdel(key, produto_nome)
    else:
        # Puxa o JSON do item atual
        item_existente = await client.hget(key, produto_nome)

        if item_existente:
            # Converte para dicionário, atualiza a quantidade e salva de novo
            dados_item = json.loads(item_existente)
            dados_item["qty"] = qty

            await client.hset(key, produto_nome, json.dumps(dados_item))
            await client.expire(key, CART_TTL)
        else:
            log(f"Aviso: Tentativa de alterar quantidade de um item ({produto_nome}) que não está no carrinho.")

async def remove_item_from_cart_state(
        tenant_id: str,
        chat_id: str,
        produto_nome: str,
):
    log(f"removendo item do carrinho =====> tenant-id: {tenant_id}, chat_id: {chat_id}, produto: {produto_nome}")
    key = cart_key(tenant_id, chat_id)
    await client.hdel(key, produto_nome)


import json


async def get_cart_state(
        tenant_id: str,
        chat_id: str,
):
    log(f"Consultando carrinho =====> tenant-id: {tenant_id}, chat_id: {chat_id}")
    key = cart_key(tenant_id, chat_id)
    data = await client.hgetall(key)

    await client.expire(key, CART_TTL)

    # Transforma cada string JSON do Redis de volta em um dicionário Python
    return {
        produto_nome: json.loads(json_string)
        for produto_nome, json_string in data.items()
    }


async def clear_cart_state(
        tenant_id: str,
        chat_id: str,
):
    log(f"Limpando carrinho =====> tenant-id: {tenant_id}, chat_id: {chat_id}")
    key = cart_key(tenant_id, chat_id)
    await client.delete(key)


async def atualizar_dados_checkout(
        tenant_id: str,
        chat_id: str,
        tipo_entrega: str,  # Ex: "Delivery" ou "Retirada"
        endereco: str,
        forma_pagamento: str  # Ex: "Pix", "Cartão", "Dinheiro"
):
    """
    Use this tool ONLY when the customer provides the address (if it's delivery) and a payment method.
    """
    key = cart_key(tenant_id, chat_id)

    existe = await client.exists(key)
    if not existe:
        return "❌ ERRO: Carrinho vazio. Peça para o cliente escolher os itens primeiro."

    await client.hset(key, "tipo_entrega", tipo_entrega)
    await client.hset(key, "endereco", endereco)
    await client.hset(key, "forma_pagamento", forma_pagamento)

    await client.hset(key, "status", "PRONTO_PARA_RESUMO")
    await client.expire(key, CART_TTL)

    return "Dados de checkout salvos com sucesso! Agora você DEVE acionar a ferramenta 'enviar_resumo_pedido' IMEDIATAMENTE."


async def buscar_resumo_carrinho_redis(tenant_id: str, chat_id: str) -> dict:
    key = f"carrinho:{tenant_id}:{chat_id}"

    # Busca todos os campos do Hash de forma assíncrona com await
    carrinho_cru = await client.hgetall(key)

    if not carrinho_cru:
        return {"status": "MONTANDO_PEDIDO", "itens": []}

    itens = []
    status_pedido = "MONTANDO_PEDIDO"

    for campo_bytes, valor_bytes in carrinho_cru.items():
        campo = campo_bytes.decode('utf-8') if isinstance(campo_bytes, bytes) else campo_bytes
        valor = valor_bytes.decode('utf-8') if isinstance(valor_bytes, bytes) else valor_bytes

        if campo == "status":
            status_pedido = valor
        elif campo in ["tipo_entrega", "endereco", "forma_pagamento"]:
            continue  # Pula os campos extras de texto para não misturar com os produtos
        else:
            # É um produto cadastrado pelo hset
            try:
                dados_item = json.loads(valor)
                itens.append({
                    "nome": campo,
                    "qty": dados_item.get("qty", 1)
                })
            except Exception as e:
                log(str(e))
                continue

    return {
        "status": status_pedido,
        "itens": itens
    }

async def atualizar_status_cart_state(
        tenant_id:str,
        chat_id:str,
        novo_status:str
):
    key = f"carrinho:{tenant_id}:{chat_id}"

    cart_data = await client.get(key)

    if cart_data:
        cart_dict = json.loads(cart_data)

        cart_dict["status"] = novo_status

        await client.set(key, json.dumps(cart_dict))
    else:
        # Se por acaso o carrinho não existir, cria um do zero com o novo status
        novo_carrinho = {
            "status": novo_status,
            "itens": []
        }
        await client.set(key, json.dumps(novo_carrinho))