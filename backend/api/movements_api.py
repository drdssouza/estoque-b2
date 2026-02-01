from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.utils.data_loader import DataLoader
from backend.api.products_api import verify_auth

router = APIRouter()
data_loader = DataLoader()

@router.get("/movements")
def get_movements(auth=Depends(verify_auth)):
    df = data_loader.load_movements()
    result = df.to_dict(orient="records")
    for item in result:
        if 'created_at' in item:
            item['created_at'] = str(item['created_at'])
    return result

@router.get("/movements/product/{product_id}")
def get_product_movements(product_id: int, auth=Depends(verify_auth)):
    df = data_loader.load_movements()
    df = df[df['product_id'] == product_id]
    result = df.to_dict(orient="records")
    for item in result:
        if 'created_at' in item:
            item['created_at'] = str(item['created_at'])
    return result