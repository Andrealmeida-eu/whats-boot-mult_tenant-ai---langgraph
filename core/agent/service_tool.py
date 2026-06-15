from collections import defaultdict
from typing import List, Optional, Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from contextlib import contextmanager
from sqlalchemy import or_, and_

from core.data.database.model.base_tenant.horarioFuncionamento import HorarioFuncionamento, TurnoCardapio
from fast_api.api_restaurant.funcionamento import verificar_status_e_turno
from core.data.database.conection.conection_orm import get_db
from core.data.database.model.restaurant.orders import Pedido, ItemPedido, StatusPedido
from core.data.database.model.restaurant.product import Produto
from core.data.database.model.restaurant.client_modal import Cliente
from core.data.database.model.base_tenant.tenantBase import Tenant
from core.providers.factory import get_provider
from collections import defaultdict
from contextlib import contextmanager
from typing import Any, Dict, List




# ==========================================
# 2. FERRAMENTAS (TOOLS) PARA O AGENTE
# ==========================================

def log(*args):
    print("[TOOLS]", *args, flush=True)

async def consultar_preco_produto_state(
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



async def consultar_cardapio_state(
    tenant_id: str,
    turno_especifico: str | None = None,
    termo_busca: str | None = None
) -> Dict[str, Any]:
    with contextmanager(get_db)() as db:
        try:
            tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
            taxa = float(tenant.taxa_entrega_padrao) if tenant and tenant.taxa_entrega_padrao else 0.0

            if not turno_especifico:
                status_atual = verificar_status_e_turno(tenant_id, db)
                turno_pesquisa = status_atual["turno"] if status_atual["aberto"] else None
            else:
                turno_pesquisa = turno_especifico
            log(f"no Consultar cardapio _/-/_/-/_/->{turno_pesquisa}")
            produtos = db.query(Produto).filter(
                Produto.tenant_id == tenant_id,
                or_(
                    Produto.disponibilidade_turno == turno_pesquisa,
                    Produto.disponibilidade_turno == TurnoCardapio.TODOS
                )
            ).all()

            if not produtos:
                return {
                    "tipo": "erro",
                    "mensagem": "O cardápio está indisponível no momento."
                }

            if not termo_busca:
                categorias = sorted({
                    str(p.categoria.nome).strip()
                    for p in produtos if p.categoria and p.categoria.nome
                })
                return {
                    "tipo": "categorias",
                    "taxa_entrega": taxa,
                    "categorias": categorias
                }

            termo_busca_normalizado = termo_busca.strip().lower()

            produtos_filtrados = [
                p for p in produtos
                if p.categoria and p.categoria.nome.strip().lower() == termo_busca_normalizado
            ]

            if not produtos_filtrados:
                return {
                    "tipo": "vazio",
                    "mensagem": f"Nenhum produto encontrado na categoria '{termo_busca}'."
                }

            categoria_nome = produtos_filtrados[0].categoria.nome.strip()
            agrupado = defaultdict(list)

            for p in produtos_filtrados:
                subtipo = getattr(p, "sub_tipo", None) or "Geral"
                agrupado[subtipo].append({
                    "nome": p.nome,
                    "preco": float(p.preco),
                    "descricao": (p.descricao or "Sem descrição").strip()
                })

            return {
                "tipo": "categoria_produtos",
                "categoria": categoria_nome,
                "taxa_entrega": taxa,
                "subtipos": dict(agrupado)
            }

        except Exception as e:
            return {
                "tipo": "erro",
                "mensagem": f"Erro ao acessar o cardápio: {str(e)}"
            }

async def consultar_status_pedido_state(tenant_id: str, whatsapp_cliente: str) -> str:
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
        name_cliente: str,
        tipo_entrega: str,
        forma_pagamento: str,
        endereco_entrega: str,
        troco_para: str,
        itens_carrinho: list
) -> str:
    """
    Salva o pedido oficial no sistema da lanchonete usando os dados do State.
    """
    if not itens_carrinho:
        return "❌ ALERTA PARA A IA: O carrinho está vazio! O pedido NÃO foi gerado. Avise o cliente."

    with contextmanager(get_db)() as db:
        try:
            log(f"Lançando pedido - Entrega: {tipo_entrega}, Pagamento: {forma_pagamento}, Endereço: {endereco_entrega}")
            
            # 1. Busca ou cadastra o cliente
            cliente = db.query(Cliente).filter(
                Cliente.whatsapp_id == chat_id,
                Cliente.tenant_id == tenant_id
            ).first()

            if not cliente:
                cliente = Cliente(
                    tenant_id=tenant_id,
                    whatsapp_id=chat_id,
                    nome=name_cliente,
                    endereco_padrao=endereco_entrega
                )
                db.add(cliente)
                db.flush()

            # 2. Cria o cabeçalho do Pedido
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

            # 3. Adiciona os itens (que vieram direto do State do LangGraph)
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

            # 4. Calcula taxa de entrega
            if tipo_entrega and tipo_entrega.upper() == "DELIVERY":
                tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
                if tenant and getattr(tenant, "taxa_entrega_padrao", None):
                    valor_total += float(tenant.taxa_entrega_padrao)

            novo_pedido.valor_total = valor_total
            db.commit()

            return f"Sucesso! Pedido '''{novo_pedido.id}''' enviado para cozinha. Valor total: '''R$ {valor_total:.2f}'''."

        except Exception as e:
            db.rollback()
            return f"Erro interno ao salvar o pedido: {str(e)}"
        
async def enviar_resumo_pedido_state(
        tenant_id: str,
        itens: list,
        entrega: str,
        pagamento: str
) -> str:
    """
    Lê os itens diretamente do State do LangGraph, calcula os valores 
    e formata o recibo do pedido para o cliente.
    """
    with contextmanager(get_db)() as db:
        try:
            subtotal = 0.0
            taxa_entrega = 0.0

            # 1. Consulta a taxa de entrega real no banco de dados se for DELIVERY
            if entrega and entrega.upper() == "DELIVERY":
                tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
                if tenant and tenant.taxa_entrega_padrao:
                    taxa_entrega = float(tenant.taxa_entrega_padrao)

            # 2. Cabeçalho do Recibo
            texto_recibo = (
                "🧾 *RESUMO DO SEU PEDIDO* 🧾\n"
                f"🏪 *{tenant_id.replace('-', ' ').title()}*\n"
                "--------------------------------------\n"
            )
            
            # 3. Loop para preencher os itens que vieram do State
            for item in itens:
                nome = item.get("nome", "Item")
                qtd_item = int(item.get("qty", 1))
                preco_item = float(item.get("preco", 0.0))
                
                valor_linha = preco_item * qtd_item
                subtotal += valor_linha

                valor_linha_str = f"{valor_linha:.2f}".replace('.', ',')
                texto_recibo += f"▪️ {qtd_item}x {nome} — R$ {valor_linha_str}\n"

            total_geral = subtotal + taxa_entrega

            subtotal_str = f"{subtotal:.2f}".replace('.', ',')
            taxa_str = f"{taxa_entrega:.2f}".replace('.', ',')
            total_str = f"{total_geral:.2f}".replace('.', ',')

            # 4. Fechamento de valores
            texto_recibo += (
                "--------------------------------------\n"
                f"💵 *Subtotal:* R$ {subtotal_str}\n"
            )

            if taxa_entrega > 0:
                texto_recibo += f"🚚 *Taxa de Entrega:* R$ {taxa_str}\n"

            texto_recibo += (
                "--------------------------------------\n"
                f"💰 *TOTAL A PAGAR: R$ {total_str}*\n"
            )
            
            # 5. Confirmação dos dados finais
            pagamento_texto = pagamento.upper() if pagamento else "Não informado"
            entrega_texto = "Entrega (Delivery)" if (entrega and entrega.upper() == "DELIVERY") else "Retirada no Balcão"
            
            texto_recibo += f"\n📦 *Tipo:* {entrega_texto}"
            texto_recibo += f"\n💳 *Pagamento:* {pagamento_texto}"

    
            return texto_recibo

        except Exception as e:
            return f"⚠️ Erro ao gerar o resumo do pedido: {str(e)}"