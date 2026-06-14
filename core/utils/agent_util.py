from typing import Any


def format_ai_output_gem(raw_output: Any) -> str:
    """
    Trata o output bruto do LangChain/LLMs (como o Gemini)
    para garantir que o retorno seja sempre uma string limpa.
    """

    if isinstance(raw_output, str):
        return raw_output.strip()

    final_text = ""

    if isinstance(raw_output, list):
        for item in raw_output:
            if isinstance(item, str):
                final_text += item
            elif isinstance(item, dict) and 'text' in item:
                final_text += item['text']
        return final_text.strip()

    return str(raw_output).strip()

def formatar_cardapio_whatsapp(payload: dict) -> str:
    tipo = payload.get("tipo")

    if tipo == "erro" or tipo == "vazio":
        return payload["mensagem"]

    if tipo == "categorias":
        taxa = payload.get("taxa_entrega", 0.0)
        categorias = payload.get("categorias", [])

        linhas = [
            "*📋 CARDÁPIO*",
            "",
            f"🛵 *Taxa de Entrega:* R$ {taxa:.2f}",
            "",
            "Veja nossas categorias:",
            ""
        ]

        for cat in categorias:
            linhas.append(f"- ```{cat}```")

        linhas.append("")
        linhas.append("Qual dessas você deseja conferir? É só me falar aqui.")
        return "\n".join(linhas)

    if tipo == "categoria_produtos":
        categoria = payload.get("categoria", "Cardápio")
        subtipos = payload.get("subtipos", {})

        emoji_categoria = {
            "hambúrgueres": "🍔",
            "combos": "🍟",
            "porções": "🍟",
            "bebidas": "🥤",
            "sobremesas": "🍰"
        }.get(categoria.strip().lower(), "📋")

        linhas = [f"*{emoji_categoria} {categoria}*", ""]

        contador = 1
        for subtipo in sorted(subtipos.keys()):
            produtos = subtipos[subtipo]

            if subtipo.strip().lower() != "geral":
                linhas.append(f"*{subtipo}*")
                linhas.append("")

            for p in produtos:
                linhas.append(f"{contador}. *{p['nome']}* - R$ {p['preco']:.2f}")
                linhas.append(f"> _{p['descricao']}_")
                linhas.append("")
                linhas.append("")
                contador += 1

        linhas.append("Digite o número ou nome do item para fazer seu pedido.")
        return "\n".join(linhas).strip()

    return "Não foi possível montar o cardápio."