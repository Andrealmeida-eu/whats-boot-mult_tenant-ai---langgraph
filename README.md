# 🍔 Assistente Virtual Inteligente para Delivery (WhatsApp AI Bot)

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=langchain)
![OpenAI](https://img.shields.io/badge/OpenAI-412991.svg?style=for-the-badge&logo=OpenAI&logoColor=white)

Um agente conversacional autônomo projetado para automatizar o atendimento de ponta a ponta de lanchonetes e restaurantes via WhatsApp. Construído com uma arquitetura assíncrona orientada a eventos, o bot não apenas conversa com o cliente, mas gerencia o estado do carrinho, negocia itens e processa o checkout de forma determinística, evitando "alucinações" comuns em LLMs.

## 🚀 O Problema que Resolve
Atendimentos manuais via WhatsApp geram gargalos em horários de pico, erros na anotação de pedidos e frustração para o cliente. Este projeto resolve isso através de um LLM que atua como um "garçom digital", orquestrado por um backend robusto que garante que os dados do pedido (itens, endereço, pagamento e troco) sejam estruturados e salvos perfeitamente no sistema da loja.

## 🧠 Diferenciais Técnicos (Enterprise-Grade)

Ao contrário de bots de IA simples que dependem apenas de prompt inicial, esta aplicação foi desenhada para cenários reais de alta concorrência:

* **State-Driven Prompting:** O prompt do agente é injetado dinamicamente com base no estado atual do pedido no banco de dados (ex: `MONTANDO_PEDIDO`, `PRONTO_PARA_RESUMO`, `AGUARDANDO_CONFIRMACAO`). Isso garante que a IA siga regras de negócio estritas e não ofereça itens quando deveria estar fechando a venda.
* **Gestão de Concorrência com Redis (Async Debounce):** Implementação de uma fila e debounce assíncrono para mensagens do WhatsApp. Se o cliente enviar 5 mensagens consecutivas em frações de segundo, o sistema consolida o buffer e faz uma única chamada ao LLM, otimizando o consumo de tokens (redução de custos) e evitando respostas duplicadas.
* **Tool Calling Estrito (Pydantic):** A IA não interage com o banco de dados via texto livre. Ela é forçada a acionar ferramentas (`@tool`) tipadas para Adicionar ao Carrinho, Consultar Preço e Fazer Checkout, garantindo consistência total dos dados.

## 🛠️ Principais Features

- [x] **Cardápio Dinâmico:** Apresentação inteligente de categorias e itens.
- [x] **Gestão de Carrinho:** Adição, remoção e alteração de quantidades (Upsert/Incremento).
- [x] **Validação de Horário de Funcionamento:** O bot reconhece os turnos da loja e recusa pedidos fora do horário.
- [x] **Checkout Estruturado:** Captura de forma de pagamento (com cálculo de troco) e endereço completo.
- [x] **Upsell Inteligente:** Sugere acompanhamentos ou bebidas sutilmente antes do fechamento.
- [x] **Integração com Evolution API:** Conexão fluida com instâncias de WhatsApp.

## 💻 Stack Tecnológica

* **Backend:** Python, FastAPI
* **Orquestração de IA:** LangChain, OpenAI API (GPT-4o-mini)
* **Cache e Mensageria:** Redis (Asyncio)
* **Integração WhatsApp:** Evolution API
* **Persistência de Dados:** SQLAlchemy / PostgreSQL (ou o banco que estiver usando)

## ⚙️ Arquitetura do Fluxo

1. O cliente envia uma mensagem no WhatsApp.
2. O webhook do FastAPI intercepta e enfileira no Redis (Debounce).
3. O estado atual do cliente é consultado (Carrinho, Turno, Status).
4. O `AgentExecutor` do LangChain avalia a intenção e aciona a `tool` necessária (ex: `gerenciar_carrinho(acao="checkout")`).
5. O estado é atualizado no backend e a resposta humanizada volta para o WhatsApp.