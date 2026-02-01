from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import auth_api, products_api, movements_api

app = FastAPI(title="Arena B2 - API de Estoque")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_api.router, prefix="/api/auth", tags=["auth"])
app.include_router(products_api.router, prefix="/api", tags=["products"])
app.include_router(movements_api.router, prefix="/api", tags=["movements"])

@app.get("/")
def root():
    return {"message": "Arena B2 API - Sistema de Controle de Estoque"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)