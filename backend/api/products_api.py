from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from backend.utils.data_loader import DataLoader
from backend.utils.jwt_handler import verify_token

router = APIRouter()
data_loader = DataLoader()

def verify_auth(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token não fornecido")
    
    token = authorization.split(" ")[1]
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    
    return payload

@router.get("/products")
def get_products(auth=Depends(verify_auth)):
    df = data_loader.load_products()
    return df.to_dict(orient="records")

@router.get("/products/{product_id}")
def get_product(product_id: int, auth=Depends(verify_auth)):
    df = data_loader.load_products()
    product = df[df['id'] == product_id]
    if len(product) == 0:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return product.to_dict(orient="records")[0]

@router.get("/products/low-stock")
def get_low_stock(auth=Depends(verify_auth)):
    df = data_loader.get_low_stock_products()
    return df.to_dict(orient="records")

@router.get("/products/search")
def search_products(query: str = "", category: str = None, auth=Depends(verify_auth)):
    df = data_loader.search_products(query, category)
    return df.to_dict(orient="records")