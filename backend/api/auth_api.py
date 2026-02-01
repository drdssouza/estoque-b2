from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.utils.jwt_handler import create_access_token

router = APIRouter()

USERS = {
    "admin": "arena123"
}

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(request: LoginRequest):
    if request.username not in USERS or USERS[request.username] != request.password:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    access_token = create_access_token(data={"sub": request.username})
    return {"access_token": access_token, "token_type": "bearer"}