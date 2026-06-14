from datetime import datetime, timedelta
from typing import Optional
import jwt

import bcrypt


SECRET_KEY = "uma_chave_secreta_muito_longa_e_dificil"
ALGORITHM = "HS256"



def get_password_hash(password: str) -> str:
    # Transforma a string em bytes
    pwd_bytes = password.encode('utf-8')

    # Gera o salt e o hash
    salt = bcrypt.gensalt()
    hash_bytes = bcrypt.hashpw(pwd_bytes, salt)
    # Retorna como string para salvar no banco
    return hash_bytes.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now() + (expires_delta or timedelta(minutes=1440)) # 24 horas
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)