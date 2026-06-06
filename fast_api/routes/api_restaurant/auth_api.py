from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fast_api.core.database.conection.conection_orm import get_db
from fast_api.core.database.model.restaurant.auth import Usuario

from fast_api.core.security.auth import verify_password, create_access_token


router = APIRouter(tags=["Autenticação"])


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # 1. Busca o usuário pelo e-mail
    user = db.query(Usuario).filter(Usuario.email == form_data.username).first()

    # 2. Verifica se existe e se a senha bate
    if not user or not verify_password(form_data.password, user.senha_hash):
        raise HTTPException(status_code=400, detail="E-mail ou senha incorretos")

    # 3. Gera o Token colocando o ID do usuário e o Tenant dele dentro do token
    token_data = {"sub": str(user.id), "tenant_id": user.tenant_id, "role": user.role.value}
    access_token = create_access_token(data=token_data)

    return {"access_token": access_token, "token_type": "bearer"}




