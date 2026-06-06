# 🚀 Delivery AI Platform

### Assistente Virtual Inteligente para Delivery via WhatsApp

> Plataforma SaaS multitenant para automação de atendimento, vendas e gestão de pedidos via WhatsApp utilizando IA Generativa, LangChain e FastAPI.








![WhatsApp-Automation-green?style=for-the-badge)

---

# 📌 Visão Geral

O Delivery AI Platform é uma solução completa para restaurantes, marmitarias, hamburguerias, pizzarias e lanchonetes que desejam automatizar seu atendimento pelo WhatsApp sem perder controle operacional.

A plataforma combina Inteligência Artificial, automação conversacional e gestão operacional para transformar mensagens em pedidos estruturados.

O cliente conversa naturalmente pelo WhatsApp enquanto a IA:

* Apresenta o cardápio
* Monta pedidos
* Gerencia carrinho
* Sugere adicionais
* Coleta endereço
* Define pagamento
* Calcula troco
* Finaliza pedidos
* Integra com o sistema de gestão

Tudo isso sem intervenção humana.

---

# 🎯 Problema Resolvido

Empresas de delivery enfrentam diariamente:

* Alto volume de mensagens
* Erros de digitação em pedidos
* Demora no atendimento
* Perda de vendas em horários de pico
* Custos elevados com atendentes

A plataforma elimina esses gargalos através de um agente autônomo especializado em vendas para delivery.

---

# 🏗 Arquitetura

```text
Cliente WhatsApp
       │
       ▼
Webhook FastAPI
       │
       ▼
Fila Redis + Debounce
       │
       ▼
AgentExecutor (LangChain)
       │
 ┌─────┼─────┐
 ▼     ▼     ▼
Tools  Redis PostgreSQL
       │
       ▼
Sistema de Gestão
       │
       ▼
Resposta para WhatsApp
```

---

# ⚡ Principais Diferenciais

## 🧠 IA Orientada por Estado

O comportamento do agente muda dinamicamente conforme a etapa da venda.

Exemplos:

* Navegação do cardápio
* Montagem do pedido
* Captura de endereço
* Pagamento
* Confirmação final

Isso reduz drasticamente alucinações da IA.

---

## 🛒 Carrinho Persistente

Utilizando Redis para armazenamento de contexto:

* Adição de itens
* Remoção
* Alteração de quantidade
* Recuperação de sessão

Mesmo que o usuário interrompa a conversa.

---

## ⚙️ Debounce Inteligente

Quando o cliente envia várias mensagens seguidas:

```text
"Quero uma pizza"

"Calabresa"

"Grande"

"Com borda"
```

O sistema agrupa as mensagens antes de chamar o LLM.

Benefícios:

* Menor consumo de tokens
* Menor latência
* Menor custo operacional

---

## 🔧 Tool Calling Estruturado

O agente não manipula dados livremente.

Toda operação passa por ferramentas tipadas:

```python
AdicionarItemTool
RemoverItemTool
BuscarCardapioTool
CheckoutTool
CalcularTrocoTool
```

Garantindo integridade dos dados.

---

# 🏢 Multi-Tenant

A plataforma foi projetada para operar centenas de estabelecimentos simultaneamente.

Cada tenant possui:

* Cardápio próprio
* Horários próprios
* Configurações próprias
* Prompts próprios
* Instâncias WhatsApp próprias

Sem compartilhamento de dados.

---

# 📱 Multi-Provedor WhatsApp

Arquitetura preparada para múltiplos gateways:

* Evolution API
* Meta Cloud API
* Z-API
* UltraMsg
* Provedores customizados

Bastando implementar um adapter.

---

# 🖥 Painel Administrativo

Frontend desenvolvido em React + TypeScript.

Funcionalidades:

### Gestão de Cardápio

* Categorias
* Produtos
* Adicionais
* Preços

### Operação

* Turnos
* Horários
* Status Aberto/Fechado

### Caixa

* Abertura de caixa
* Fechamento de caixa
* Controle operacional

### Configuração da IA

* Prompt personalizado
* Mensagens automáticas
* Estratégias de venda

---

# 🔐 Segurança

* JWT Authentication
* Multi-Tenant Isolation
* SQLAlchemy ORM
* Validação Pydantic
* Controle de permissões
* Variáveis protegidas via .env

---

# 🛠 Stack Tecnológica

## Backend

* Python 3.11+
* FastAPI
* SQLAlchemy
* Pydantic
* PostgreSQL

## IA

* LangChain
* AgentExecutor
* OpenAI

## Infraestrutura

* Redis
* Docker
* Docker Compose

## Frontend

* React
* TypeScript

---

# 📈 Casos de Uso

✅ Restaurantes

✅ Hamburguerias

✅ Pizzarias

✅ Marmitarias

✅ Lanchonetes

✅ Delivery de Açaí

✅ Dark Kitchens

---

# 🚀 Roadmap

* [ ] Dashboard Analítico
* [ ] Integração iFood
* [ ] Integração Anota AI
* [ ] Integração ERP
* [ ] Voice AI
* [ ] Multi-LLM Support
* [ ] RAG para FAQs
* [ ] Monitoramento em Tempo Real
* [ ] Painel SaaS para Revendas

---

# 📄 Licença

Este projeto está sob licença MIT.

---

# 👨‍💻 Autor

Desenvolvido com foco em arquitetura escalável, IA conversacional e automação de vendas para delivery.

Se este projeto foi útil para você, deixe uma ⭐ no repositório.
