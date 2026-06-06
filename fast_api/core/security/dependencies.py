from fastapi import Depends, Header, HTTPException
from fastapi.security import OAuth2PasswordBearer
import  jwt
from sqlalchemy.orm import Session

from fast_api.core.database.model.restaurant.auth import Usuario, Role
from fast_api.core.security.auth import SECRET_KEY, ALGORITHM

from fast_api.core.database.conection.conection_orm import get_db # Ajuste para o seu caminho real
from fast_api.core.database.model.base_tenant.tenantBase import Tenant


# Isso diz ao FastAPI onde o frontend deve buscar o token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Usuario:
    try:
        # Abre o token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")

        user_id = int(user_id_str)

        if user_id is None:
            raise HTTPException(status_code=401, detail="Token inválido")

    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token expirado ou inválido")

    # Busca o usuário no banco
    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")

    return user

def get_admin_user(current_user: Usuario = Depends(get_current_user)):
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Acesso negado. Esta operação exige perfil de Administrador."
        )
    return current_user

def get_current_tenant(
    x_tenant_id: str = Header(..., description="ID da Lanchonete"),
    db: Session = Depends(get_db)
) -> Tenant:


    tenant = db.query(Tenant).filter(Tenant.id == x_tenant_id, Tenant.ativo == True).first()
    if not tenant:
        raise HTTPException(status_code=403, detail="Lanchonete (Tenant) inválida ou inativa.")
    return tenant
