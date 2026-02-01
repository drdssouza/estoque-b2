import pandas as pd
from pathlib import Path

# Criar pasta data
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

# Criar DataFrame de produtos
products = pd.DataFrame({
    'id': [1, 2, 3],
    'name': ['Água Mineral 500ml', 'Refrigerante Coca-Cola 350ml', 'Chips Ruffles 100g'],
    'category': ['bebida', 'bebida', 'chips'],
    'purchase_price': [1.50, 2.50, 4.00],
    'sale_price': [3.00, 5.00, 8.00],
    'minimum_stock': [20, 15, 10],
    'current_stock': [50, 30, 25],
    'active': [True, True, True]
})

# Criar DataFrame de movimentações (vazio)
movements = pd.DataFrame({
    'id': pd.Series([], dtype='int64'),
    'product_id': pd.Series([], dtype='int64'),
    'movement_type': pd.Series([], dtype='str'),
    'quantity': pd.Series([], dtype='int64'),
    'created_at': pd.Series([], dtype='datetime64[ns]'),
    'note': pd.Series([], dtype='str')
})

# Salvar arquivos
products_file = data_dir / "products.parquet"
movements_file = data_dir / "movements.parquet"

print("Salvando products.parquet...")
products.to_parquet(products_file, index=False)
print(f"✅ Arquivo criado: {products_file}")

print("Salvando movements.parquet...")
movements.to_parquet(movements_file, index=False)
print(f"✅ Arquivo criado: {movements_file}")

print("\n📦 Produtos cadastrados:")
print(products)

print("\n✅ Sistema inicializado!")