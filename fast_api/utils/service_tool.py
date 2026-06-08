from collections import defaultdict
from typing import List, Optional, Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from contextlib import contextmanager
from sqlalchemy import or_, and_
import json
import asyncio
from fast_api.core.database.model.base_tenant.horarioFuncionamento import HorarioFuncionamento, TurnoCardapio
from fast_api.redis.cart import add_item_to_cart_state, get_cart_state, remove_item_from_cart_state, clear_cart_state, \
    set_item_quantity_state, atualizar_status_cart_state,buscar_resumo_carrinho_redis,buscar_resumo_carrinho_full_redis
from fast_api.routes.api_restaurant.funcionamento import verificar_status_e_turno
from fast_api.core.database.conection.conection_orm import get_db
from fast_api.core.database.model.restaurant.orders import Pedido, ItemPedido, StatusPedido
from fast_api.core.database.model.restaurant.product import Produto
from fast_api.core.database.model.restaurant.client_modal import Cliente
from fast_api.core.database.model.base_tenant.tenantBase import Tenant
from providers.factory import get_provider




# ==========================================
# 2. FERRAMENTAS (TOOLS) PARA O AGENTE
# ==========================================

def log(*args):
    print("[TOOLS]", *args, flush=True)

def consultar_preco_produto_state(
        tenant_id: str,
        produto_nome: str,
        **kwargs
) -> Any:

    """
        Use SEMPRE que após o cliente pedir para adicionar um item e este  item nao tiver o preço.
    """
    with contextmanager(get_db)() as db:
        try:


            status_atual = verificar_status_e_turno(tenant_id, db)
            turno_pesquisa = status_atual["turno"] if status_atual["aberto"] else None

            turno_atual = turno_pesquisa

            produto = db.query(Produto).filter(

                    Produto.tenant_id == tenant_id,
                    Produto.nome.ilike(f"%{produto_nome.lower().strip()}%"),


                or_(
                    Produto.disponibilidade_turno == turno_atual,
                    Produto.disponibilidade_turno == TurnoCardapio.TODOS
                )

                # Produto.ativo == True # (Descomente se tiver um campo 'ativo' no Produto)
            ).all()


            if not produto:
                return "O cardápio não esta disponível no momento"

                # Cenário 1: Achou apenas 1 produto exato
            if len(produto) == 1:
                p = produto[0]
                return f"SUCESSO: O preço de '{p.nome}' é R$ {p.preco:.2f}. Pode adicionar ao carrinho com este nome exato."

                # Cenário 2: Achou VÁRIOS produtos (ex: "Coca" achou Lata, 600ml e 2L)
            if len(produto) > 1:
                opcoes = [f"- {p.nome} (R$ {p.preco:.2f})" for p in produto]
                opcoes_texto = "\n".join(opcoes)
                return (
                        f"ALERTA: Encontrei VÁRIAS opções para '{produto_nome}'. "
                        f"NÃO ADICIONE AO CARRINHO. Pergunte ao cliente qual destas opções ele quer:\n{opcoes_texto}"
                    )

        except Exception as e:
            return f"Erro ao acessar o cardápio: {str(e)}"

def consultar_cardapio_state(
        tenant_id: str,
        turno_especifico: str,
        termo_busca: str
) -> Any:
    """
        Use SEMPRE que o cliente pedir para ver o cardápio.
        Se não passar termo_busca, lista as Categorias Principais.
        Se o termo_busca for uma categoria (ex: "Bebidas"), retorna os produtos separados por sub-tipos.
    """
    with contextmanager(get_db)() as db:
        try:
            # Busca a taxa de entrega da loja
            tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
            taxa = tenant.taxa_entrega_padrao if tenant and tenant.taxa_entrega_padrao else 0.0


            if not turno_especifico:
                status_atual = verificar_status_e_turno(tenant_id, db)
                turno_pesquisa = status_atual["turno"] if status_atual["aberto"] else None
            else:
                turno_pesquisa = turno_especifico

            turno_atual = turno_pesquisa

            produtos = db.query(Produto).filter(
                Produto.tenant_id == tenant_id,
                or_(
                    Produto.disponibilidade_turno == turno_atual,
                    Produto.disponibilidade_turno == TurnoCardapio.TODOS
                )

                # Produto.ativo == True # (Descomente se tiver um campo 'ativo' no Produto)
            ).all()


            if not produtos:
                return "O cardápio está indisponível no momento."

            if not termo_busca:
                categorias = set(
                    [
                        str(p.categoria.nome) for p in produtos if p.categoria
                    ]
                )

                resposta_texto = f"Taxa de Entrega: R$ {taxa:.2f}\nCategorias Disponíveis:\n"
                for cat in categorias:
                    resposta_texto += f"- {cat}\n"

                resposta_texto += "\nINSTRUÇÃO INTERNA: Mostre apenas os nomes dessas categorias ao cliente e pergunte qual ele deseja ver."
                return resposta_texto
            termo_busca_normalize = termo_busca.lower().strip()
            produtos_filtrados = [p for p in produtos if
                                  p.categoria and p.categoria.nome.lower() == termo_busca_normalize]

            if not produtos_filtrados:
                return f"Nenhum produto encontrado na categoria '{termo_busca_normalize}'."

            cardapio_agrupado = defaultdict(list)
            for p in produtos_filtrados:
                # Se o produto não tiver sub_tipo cadastrado, joga em "GERAL"
                chave = p.sub_tipo if getattr(p, 'sub_tipo', None) else "GERAL"
                cardapio_agrupado[chave].append(p)

            resposta_texto = f"Itens da categoria {termo_busca_normalize}:\n"

            for sub_tipo, lista_produtos in cardapio_agrupado.items():
                resposta_texto += f"\n**{sub_tipo.upper()}**:\n"
                for p in lista_produtos:
                    resposta_texto += f"- {p.nome} | R$ {float(p.preco):.2f} | Descrição: {p.descricao or 'Sem descrição'}\n"

            return resposta_texto
        except Exception as e:
            return f"Erro ao acessar o cardápio: {str(e)}"



def consultar_status_pedido_state(tenant_id: str, whatsapp_cliente: str) -> str:
    """
    Use quando o cliente perguntar "Cadê meu lanche?", "Já saiu para entrega?" ou "Qual o status do meu pedido?".
    """
    with contextmanager(get_db)() as db:
        try:
            # Busca o cliente
            cliente = db.query(Cliente).filter(
                Cliente.whatsapp_id == whatsapp_cliente,
                Cliente.tenant_id == tenant_id
            ).first()

            if not cliente:
                return "Não encontrei nenhum cadastro com este número. Tem certeza que já fez o pedido?"

            # Busca o pedido mais recente (último criado)
            ultimo_pedido = db.query(Pedido).filter(
                Pedido.cliente_id == cliente.id,
                Pedido.tenant_id == tenant_id
            ).order_by(Pedido.id.desc()).first()

            if not ultimo_pedido:
                return "Você ainda não tem nenhum pedido registrado no nosso sistema."

            # Traduz os status para uma linguagem amigável
            mensagens_status = {
                "PENDENTE": "está na fila aguardando a cozinha iniciar.",
                "EM_PREPARO": "está na chapa sendo preparado com muito carinho! 👨‍🍳",
                "PRONTO_PARA_RETIRADA": "já está pronto te esperando no balcão! 🛍️",
                "EM_ROTA": "saiu para entrega! O motoboy já está a caminho. 🏍️",
                "CONCLUIDO": "já consta como entregue. Bom apetite! ✅",
                "CANCELADO": "foi cancelado. ❌"
            }

            # Ajuste 'ultimo_pedido.status.value' caso StatusPedido seja um Enum
            status_str = ultimo_pedido.status.value if hasattr(ultimo_pedido.status, 'value') else ultimo_pedido.status
            msg = mensagens_status.get(status_str, "está sendo processado.")

            return f"O seu pedido #{ultimo_pedido.id} {msg}"

        except Exception as e:
            return f"Erro ao consultar o status: {str(e)}"



async def lancar_pedido_sistema_state(
        tenant_id: str,
        chat_id: str,
) -> str:
    """
    Use ONLY at the end of the service, after sending the summary and the customer says "Sim, pode confirmar".
    Saves the official order in the diner's system.
    """
 
    db = next(get_db())
    try:

        cart = await buscar_resumo_carrinho_full_redis(tenant_id, chat_id)

        if not cart or cart == "{}":
            return "❌ ALERTA PARA A IA: O carrinho está vazio! O pedido NÃO foi gerado. Avise o cliente."

        cart_dict = json.loads(cart) if isinstance(cart, str) else cart
            
        tipo_entrega = cart_dict.get("tipo_entrega")
        forma_pagamento = cart_dict.get("forma_pagamento")
        endereco_entrega = cart_dict.get("endereco_entrega")
        troco_para = cart_dict.get("troco_para")
        log(f"cart resumo full: tipo entrega {tipo_entrega}, forma pagamento: {forma_pagamento}, endereco: {endereco_entrega}, troco: {troco_para}")
        cliente = db.query(Cliente).filter(
            Cliente.whatsapp_id == chat_id,
            Cliente.tenant_id == tenant_id
        ).first()

        if not cliente:
            cliente = Cliente(
                tenant_id=tenant_id,
                endereco_padrao=endereco_entrega
            )
            db.add(cliente)
            db.flush()


        novo_pedido = Pedido(
            tenant_id=tenant_id,
            cliente_id=cliente.id,
            status=StatusPedido.PENDENTE,
            tipo_entrega=tipo_entrega.upper() if tipo_entrega else "",
            forma_pagamento=forma_pagamento.upper() if forma_pagamento else "",
            endereco_entrega=endereco_entrega,
            troco_para=troco_para,
            valor_total=0.0
            )
        db.add(novo_pedido)
        db.flush()

        valor_total = 0.0

        itens_carrinho = cart_dict.get("itens", [])

        for item in itens_carrinho:
            nome_prod = item.get("nome")
            qtd_prod = int(item.get('qty', 1))


            produto = db.query(Produto).filter(
                Produto.nome == nome_prod,
                Produto.tenant_id == tenant_id
            ).first()

            if not produto:
                db.rollback()
                return f"Erro: Produto '{nome_prod}' não encontrado no banco. Peça para o cliente refazer a escolha."

            novo_item = ItemPedido(
                tenant_id=tenant_id,
                pedido_id=novo_pedido.id,
                produto_id=produto.id,
                quantidade=qtd_prod,
                preco_unitario=produto.preco
            )
            db.add(novo_item)
            valor_total += (produto.preco * qtd_prod)


        if tipo_entrega.upper() == "DELIVERY":
            tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if tenant and tenant.taxa_entrega_padrao:
                valor_total += tenant.taxa_entrega_padrao

        novo_pedido.valor_total = valor_total
        db.commit()

        await clear_cart_state(tenant_id, chat_id)

        return f"Sucesso! Pedido #{novo_pedido.id} gerado na cozinha. Valor total (com taxa, se houver): R$ {valor_total:.2f}."

    except Exception as e:
        db.rollback()
        return f"Erro interno ao salvar o pedido: {str(e)}"
    finally:
        db.close()
        
        
async def enviar_resumo_pedido_state(
        tenant_id: str,
        chat_id: str
) -> str:
    with contextmanager(get_db)() as db:
        try:
            
            cart = await buscar_resumo_carrinho_redis(tenant_id, chat_id)
            taxa_entrega = 5.00

            cart_dict = json.loads(cart) if isinstance(cart, str) else cart

            log(f" peguei o carrinho --> {cart_dict}")
            subtotal = 0.0

            # 1. Cabeçalho do Recibo
            texto_recibo = (
                "🧾 *RESUMO DO SEU PEDIDO* 🧾\n"
                f"🏪 *{tenant_id.replace("-", " ")}*\n"
                "--------------------------------------\n"
            )

            log(f"type(cart_dict)={type(cart_dict)} valor={cart_dict}")
            
            # 2. Loop para preencher os itens
            for item in cart_dict["itens"]:
                nome = item["nome"]
                qtd_item = int(item["qty"])
                preco_item = float(item['preco'])
                valor_linha = preco_item * qtd_item
                subtotal += valor_linha

                valor_linha_str = f"{valor_linha:.2f}".replace('.', ',')
                texto_recibo += f"▪️ {qtd_item}x {nome} — R$ {valor_linha_str}\n"

            total_geral = subtotal + taxa_entrega

            subtotal_str = f"{subtotal:.2f}".replace('.', ',')
            taxa_str = f"{taxa_entrega:.2f}".replace('.', ',')
            total_str = f"{total_geral:.2f}".replace('.', ',')

            texto_recibo += (
                "--------------------------------------\n"
                f"💵 *Subtotal:* R$ {subtotal_str}\n"
            )

            if taxa_entrega > 0:
                texto_recibo += f"🚚 *Taxa de Entrega:* R$ {taxa_str}\n"

            texto_recibo += (
                "--------------------------------------\n"
                f"💰 *TOTAL A PAGAR: R$ {total_str}*\n\n"
                "_Aguarde um instante, o assistente já vai confirmar a forma de entrega e pagamento com você..._ ⏳"
            )

            tenant = db.query(Tenant).filter(
                Tenant.id == tenant_id
            ).first()
            
            log(f" peguei o tenant --> {tenant.id}")

            provider = get_provider(tenant)
            log(f" peguei o provider --> {provider.api_url}")
            
            await asyncio.to_thread(provider.send_text, chat_id, texto_recibo)
            log(f" enviei texto")
            await atualizar_status_cart_state(tenant_id, chat_id, "AGUARDANDO_CONFIRMACAO")
            log(f" atualizei")
            return (
                    "SYSTEM: The receipt has been successfully sent via API.\n"
                )
        except Exception as e:
            return f"Erro interno ao enviar o resumo: {str(e)}"

