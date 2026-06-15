
# 🚀 Whats Boot AI — Multi-Tenant WhatsApp Agent Platform

## 🧠 Plataforma SaaS de IA Conversacional para Automação de Delivery

> Sistema backend escalável baseado em **LangGraph + FastAPI + Multi-Tenant Architecture**, projetado para automação de atendimento e pedidos via WhatsApp com agentes de IA orientados por estado.

---

## 📌 Elevator Pitch 

Plataforma backend de alta complexidade que implementa um **agente de IA conversacional stateful** utilizando **LangGraph**, capaz de operar múltiplos estabelecimentos (multi-tenant), automatizando fluxos de atendimento e pedidos via WhatsApp com controle transacional, persistência de estado e roteamento inteligente de intenções.

---

# 🧩 Visão Geral do Sistema

O sistema transforma mensagens do WhatsApp em **fluxos estruturados de decisão e execução**, utilizando uma arquitetura baseada em:

* Agentes de IA com estado (Stateful AI Agents)
* Graph-based orchestration (LangGraph)
* APIs REST para gestão operacional
* Arquitetura multi-tenant isolada
* Persistência via PostgreSQL + Redis

---

# 🧠 Arquitetura de Agentes (LangGraph)

O núcleo do sistema é um **grafo de execução de decisões (StateGraph)**.

## 🔁 Fluxo de execução

O agente inicia no `router node`, que interpreta a intenção do usuário:

### Mapeamento de intenções:

* `ver_cardapio` → menu node
* `adicionar_item / remover_item` → cart node
* `checkout / informar_dados` → checkout node
* `confirmar_pedido` → confirm node
* `duvida_geral` → support node
* fallback → greeting node

## 🧠 Características técnicas

* Estado compartilhado (`AgentState`)
* Execução determinística baseada em intenção
* Encadeamento com nó final `summarizer`
* Persistência de estado via Redis checkpoint

---

# 🏢 Multi-Tenant Architecture

O sistema foi projetado para operar múltiplos estabelecimentos de forma isolada.

Cada tenant possui:

* Banco de dados lógico isolado
* Cardápio próprio
* Fluxos próprios de atendimento
* Configuração independente de IA
* Controle de usuários e pedidos

➡️ Arquitetura preparada para modelo SaaS escalável.

---

# 📦 Módulos Principais

## 🧾 Core Agent System

* `graph_builder.py` → definição do fluxo LangGraph
* `nodes.py` → lógica de cada etapa do agente
* `state.py` → estado central da execução
* `service_tool.py` → ferramentas operacionais do agente
* `model.py` → abstrações do modelo de IA

---

## 🏪 Domínio de Negócio (Restaurant System)

* Auth (autenticação)
* Orders (pedidos)
* Product (cardápio/produtos)
* Client (clientes)
* Financial (caixa e financeiro)
* Gestão de IA (configuração de comportamento do agente)

---

## 🌐 API Layer (FastAPI)

Endpoints organizados por domínio:

* `auth`
* `client`
* `order`
* `cardapio`
* `caixa`
* `tenant_controller`
* `webhook`
* `health`

---

## 🗄️ Infraestrutura

* PostgreSQL (persistência principal)
* FastApi
* Redis (cache + checkpoint de estado do agente)
* SQLAlchemy ORM
* Pydantic (validação de dados)

---

# 🔐 Segurança e Isolamento

* Autenticação via JWT
* Separação completa por tenant
* Controle de acesso por domínio
* Validação de payload com Pydantic
* Camada ORM para segurança de queries

---

# 🧠 Diferenciais Técnicos

## 1. Agentic AI real (não chatbot simples)

O sistema não usa apenas prompts:

* Usa **grafo de estados (LangGraph)**
* Tem roteamento determinístico por intenção
* Mantém memória de execução
* Executa ferramentas estruturadas

---

## 2. Arquitetura orientada a estado

O comportamento do agente depende de:

* intenção atual
* histórico de conversa
* estado do carrinho/pedido
* contexto do tenant

---

## 3. Escalabilidade SaaS

* Multi-tenant nativo
* Backend stateless com Redis checkpoint
* Separação de domínio por módulos

---

## 4. Engine de decisão híbrida

Combina:

* Regras determinísticas (router)
* IA generativa (nodes)
* ferramentas estruturadas (tools)


---

# 📈 Casos de Uso

* Automação de restaurantes
* Atendimento via WhatsApp com IA
* Sistemas SaaS de pedidos
* Agentes de vendas inteligentes
* Backend para plataformas de delivery

---

# 🧭 Roadmap Técnico

* [ ] Memória semântica (RAG)
* [ ] Painel admin completo multi-tenant
* [ ] Observabilidade (logs + tracing)
* [ ] Versionamento de agentes
* [ ] Suporte multi-LLM
* [ ] Analytics de conversação
* [ ] Otimização de custo por token

---

# 👨‍💻 Posicionamento Profissional

Este projeto demonstra competências em:

* Backend de alta escala (FastAPI)
* Engenharia de IA aplicada (LangGraph)
* Arquitetura SaaS multi-tenant
* Sistemas baseados em agentes (Agentic Systems)
* Integração de IA com sistemas reais de negócio

---

# 🏁 Resumo

Este não é apenas um chatbot.

É uma **plataforma de agentes de IA com arquitetura de produção**, focada em automação de operações reais de negócios via WhatsApp.

---

Se quiser, posso na próxima etapa:

* transformar isso em **README ainda mais “GitHub viral” (com badges + diagramas visuais)**
* ou montar uma versão **100% focada em vaga internacional (inglês + senior staff engineer pitch)**
* ou ainda criar um **portfólio PDF de recrutamento baseado nesse projeto**
