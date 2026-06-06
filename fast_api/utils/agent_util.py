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