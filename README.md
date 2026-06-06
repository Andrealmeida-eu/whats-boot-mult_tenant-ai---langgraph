# WhatsApp AI Bot (produção simples, 1 tenant)

Este projeto é uma versão **simples e vendável** para produção:
- **1 tenant por VPS**
- Webhooks prontos:
  - **Evolution:** `POST /webhook/evolution` (com **Segurança 1**: `X-Tenant-Secret`)
  - **Meta Cloud:** `GET /webhook/meta` (verificação) e `POST /webhook/meta` (assinatura)
- Buffer + debounce (evita responder “picado”)
- Dedupe de webhook (evita resposta duplicada quando o provedor reenviar)

> Observação: O RAG usa pgvector (Postgres). As **embeddings** continuam em OpenAI por padrão.

---

## Rodar com Docker

1) Configure o `.env`:

```bash
cp .env .env
```

2) Suba Postgres + Redis + Bot:

```bash
docker compose up -d --build
```

3) Teste:

- `GET http://SEU_IP:8000/health`
- Docs: `http://SEU_IP:8000/docs`

---

## Configurar o webhook (Evolution)

No `.env`:

- `WHATSAPP_PROVIDER=evolution`

Aponte o webhook da Evolution para:

- URL: `http://SEU_IP:8000/webhook/evolution`
- Header: `X-Tenant-Secret: <TENANT_SECRET do .env>`

O bot ignora grupos (`@g.us`).

---

## Configurar o webhook (Meta Cloud)

No `.env`:

- `WHATSAPP_PROVIDER=meta`
- `META_VERIFY_TOKEN=...`
- `META_APP_SECRET=...`
- `META_PHONE_NUMBER_ID=...`
- `META_ACCESS_TOKEN=...`

### 1) Verificação do webhook
No painel da Meta, configure o webhook para:

- Verify URL: `http://SEU_IP:8000/webhook/meta`

O endpoint responde ao desafio (`hub.challenge`) se `hub.verify_token` bater com `META_VERIFY_TOKEN`.

### 2) Recebimento de mensagens
O mesmo endpoint recebe eventos em:

- `POST http://SEU_IP:8000/webhook/meta`

E valida a assinatura `X-Hub-Signature-256` usando `META_APP_SECRET`.

---

## Trocar provedor de LLM (OpenAI / Groq / Together)

No `.env`:

- `LLM_PROVIDER=openai` (default)
- `LLM_PROVIDER=groq`
- `LLM_PROVIDER=together`

E coloque sua chave em `LLM_API_KEY`.

> Esses provedores são **OpenAI-compatible**, então o código usa `base_url` automaticamente.

---

## Ingestão de documentos (RAG)

Coloque arquivos em:

- `data/rag_files/default`

Depois chame:

- `POST /admin/ingest`

Se você definir `ADMIN_API_KEY` no `.env`, envie header:

- `X-API-Key: <ADMIN_API_KEY>`
