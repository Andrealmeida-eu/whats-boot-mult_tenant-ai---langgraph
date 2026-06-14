from __future__ import annotations


from fastapi import FastAPI
from sqlalchemy.util import ordered_column_set

from fast_api.api_restaurant import auth_api, caixa, cardapio, client, funcionamento, order
from fast_api.webhook import webhooks
from fast_api.health import health

from core.config.configapi import settings
from fast_api.api_restaurant import tenant_controller
from core.data.database.conection.conection_orm import Base, engine



app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    openapi_url='/openapi.json'
)

Base.metadata.create_all(bind=engine)


app.include_router(webhooks.router)
app.include_router(funcionamento.router)
app.include_router(client.router)
app.include_router(auth_api.router)
app.include_router(tenant_controller.router)
app.include_router(health.router)
app.include_router(cardapio.router)
app.include_router(order.router)
app.include_router(caixa.router)

