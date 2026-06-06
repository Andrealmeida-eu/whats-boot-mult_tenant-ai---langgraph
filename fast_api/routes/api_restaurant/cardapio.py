from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from fast_api.core.database.conection.conection_orm import get_db
from fast_api.core.security.dependencies import get_current_tenant, get_admin_user
from fast_api.core.database.model.base_tenant.tenantBase import Tenant
from fast_api.core.database.model.restaurant.product import Categoria, Produto
from fast_api.core.database.model.restaurant.auth import Usuario

from pydantic import BaseModel

router = APIRouter(prefix="/cardapio", tags=["Cardápio"])


class ProdutoCreate(BaseModel):
    nome: str
    descricao: str | None = None
    preco: float
    categoria_id: int
    sub_tipo: str
    disponibilidade_turno: str

class ProdutoUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    preco: Optional[float] = None
    categoria_id: Optional[int] = None
    sub_tipo: Optional[str] = None

class CategoriaCreate(BaseModel):
    nome: str


# --- CATEGORIAS ---

@router.get("/categorias")
def listar_categorias(
        db: Session = Depends(get_db),
        tenant: Tenant = Depends(get_current_tenant)
):
    return db.query(Categoria).filter(Categoria.tenant_id == tenant.id).all()


@router.post("/categorias")
def criar_categoria(
        payload: CategoriaCreate,
        db: Session = Depends(get_db),
        admin: Usuario = Depends(get_admin_user)
):

    categoria_existente = db.query(Categoria).filter(
        Categoria.nome == payload.nome,
        Categoria.tenant_id == admin.tenant_id
    ).first()

    if categoria_existente:
        raise HTTPException(status_code=400, detail="Já existe uma categoria com este nome.")

    nova_categoria = Categoria(
        tenant_id=admin.tenant_id,
        nome=payload.nome
    )

    db.add(nova_categoria)
    db.commit()
    db.refresh(nova_categoria)
    return nova_categoria


@router.delete("/categorias/{categoria_id}")
def deletar_categoria(
        categoria_id: int,
        db: Session = Depends(get_db),
        admin: Usuario = Depends(get_admin_user)
):
    categoria = db.query(Categoria).filter(
        Categoria.id == categoria_id,
        Categoria.tenant_id == admin.tenant_id
    ).first()

    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria não encontrada.")

    # Opcional: Verificar se existem produtos vinculados antes de deletar
    produtos_vinculados = db.query(Produto).filter(Produto.categoria_id == categoria_id).first()
    if produtos_vinculados:
        raise HTTPException(status_code=400, detail="Não é possível deletar uma categoria que possui produtos.")

    db.delete(categoria)
    db.commit()
    return {"detail": "Categoria deletada com sucesso."}




@router.get("/categoria")
def listar_categorias(
        db: Session = Depends(get_db),
        tenant: Tenant = Depends(get_current_tenant)
):
    return db.query(Categoria).filter(Categoria.tenant_id == tenant.id). all()



@router.get("/produtos")
def listar_produtos(
        db: Session = Depends(get_db),
        tenant: Tenant = Depends(get_current_tenant)
):
    # SEGURANÇA: Filtra sempre pelo tenant.id
    return db.query(Produto).filter(Produto.tenant_id == tenant.id).all()


@router.post("/produtos")
def criar_produto(
        payload: ProdutoCreate,
        db: Session = Depends(get_db),
        admin: Usuario = Depends(get_admin_user)
):

    categoria = db.query(Categoria).filter(
        Categoria.id == payload.categoria_id,
        Categoria.tenant_id == admin.tenant_id
    ).first()

    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria não encontrada neste Tenant.")

    novo_produto = Produto(
        tenant_id=admin.tenant_id,
        nome=payload.nome,
        descricao=payload.descricao,
        preco=payload.preco,
        categoria_id=payload.categoria_id,
        sub_tipo=payload.sub_tipo,
        disponibilidade_turno = payload.disponibilidade_turno
    )
    db.add(novo_produto)
    db.commit()
    db.refresh(novo_produto)
    return novo_produto



@router.patch("/produtos/{produto_id}")
def atualizar_produto(
        produto_id: int,
        payload: ProdutoUpdate,
        db: Session = Depends(get_db),
        admin: Usuario = Depends(get_admin_user)
):
    produto = db.query(Produto).filter(
        Produto.id == produto_id,
        Produto.tenant_id == admin.tenant_id
    ).first()

    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")


    if payload.categoria_id is not None and payload.categoria_id != produto.categoria_id:
        categoria_valida = db.query(Categoria).filter(
            Categoria.id == payload.categoria_id,
            Categoria.tenant_id == admin.tenant_id
        ).first()
        if not categoria_valida:
            raise HTTPException(status_code=404, detail="Nova categoria não encontrada neste Tenant.")


    update_data = payload.model_dump(exclude_unset=True)


    for chave, valor in update_data.items():
        setattr(produto, chave, valor)

    db.commit()
    db.refresh(produto)
    return produto

@router.delete("/produtos/{produto_id}")
def deletar_produto(
        produto_id: int,
        db: Session = Depends(get_db),
        admin: Usuario = Depends(get_admin_user)
):
    produto = db.query(Produto).filter(
        Produto.id == produto_id,
        Produto.tenant_id == admin.tenant_id
    ).first()

    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")

    db.delete(produto)
    db.commit()
    return {"detail": "Produto deletado com sucesso."}




@router.get("/cardapio")
def obter_cardapio_completo(
        db: Session = Depends(get_db),
        tenant: Tenant = Depends(get_current_tenant)
):
    """
    Retorna as categorias junto com os produtos que pertencem a elas.
    Ideal para montar a tela de cardápio digital ou a tela de vendas do caixa.
    """
    categorias = (
        db.query(Categoria)
        .filter(Categoria.tenant_id == tenant.id)
        .options(selectinload(Categoria.produtos))
        .all()
    )

    return categorias