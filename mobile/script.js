const API_URL = 'http://localhost:8000/api';
let token = null;
let allProducts = [];

async function login() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    try {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        if (response.ok) {
            const data = await response.json();
            token = data.access_token;
            localStorage.setItem('token', token);
            
            document.getElementById('login-section').classList.add('hidden');
            document.getElementById('main-section').classList.remove('hidden');
            
            showProducts();
        } else {
            document.getElementById('login-error').textContent = 'Credenciais inválidas';
        }
    } catch (error) {
        document.getElementById('login-error').textContent = 'Erro ao conectar com o servidor';
        console.error(error);
    }
}

function logout() {
    token = null;
    localStorage.removeItem('token');
    document.getElementById('main-section').classList.add('hidden');
    document.getElementById('login-section').classList.remove('hidden');
}

async function showProducts() {
    hideAllViews();
    document.getElementById('products-view').classList.remove('hidden');
    
    try {
        const response = await fetch(`${API_URL}/products`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            allProducts = await response.json();
            displayProducts(allProducts);
        }
    } catch (error) {
        console.error(error);
    }
}

function displayProducts(products) {
    const container = document.getElementById('products-list');
    container.innerHTML = '';
    
    products.forEach(product => {
        if (!product.active) return;
        
        const isLowStock = product.current_stock <= product.minimum_stock;
        const card = document.createElement('div');
        card.className = `product-card ${isLowStock ? 'stock-low' : ''}`;
        
        card.innerHTML = `
            <h3>${product.name}</h3>
            <p><strong>Categoria:</strong> ${product.category}</p>
            <p><strong>Estoque:</strong> ${product.current_stock} unidades</p>
            <p><strong>Estoque Mínimo:</strong> ${product.minimum_stock} unidades</p>
            <p><strong>Preço de Venda:</strong> R$ ${product.sale_price.toFixed(2)}</p>
            ${isLowStock ? '<p style="color: #e74c3c; font-weight: bold;">⚠️ ESTOQUE BAIXO!</p>' : ''}
        `;
        
        container.appendChild(card);
    });
}

function searchProducts() {
    const query = document.getElementById('search-input').value.toLowerCase();
    const filtered = allProducts.filter(p => 
        p.name.toLowerCase().includes(query)
    );
    displayProducts(filtered);
}

async function showLowStock() {
    hideAllViews();
    document.getElementById('low-stock-view').classList.remove('hidden');
    
    try {
        const response = await fetch(`${API_URL}/products/low-stock`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            const products = await response.json();
            const container = document.getElementById('low-stock-list');
            container.innerHTML = '';
            
            if (products.length === 0) {
                container.innerHTML = '<p style="text-align: center; color: #27ae60;">✅ Todos os produtos com estoque adequado!</p>';
                return;
            }
            
            products.forEach(product => {
                const card = document.createElement('div');
                card.className = 'product-card stock-low';
                
                card.innerHTML = `
                    <h3>${product.name}</h3>
                    <p><strong>Estoque Atual:</strong> ${product.current_stock} unidades</p>
                    <p><strong>Estoque Mínimo:</strong> ${product.minimum_stock} unidades</p>
                    <p style="color: #e74c3c; font-weight: bold;">⚠️ REPOSIÇÃO NECESSÁRIA!</p>
                `;
                
                container.appendChild(card);
            });
        }
    } catch (error) {
        console.error(error);
    }
}

async function showMovements() {
    hideAllViews();
    document.getElementById('movements-view').classList.remove('hidden');
    
    try {
        const response = await fetch(`${API_URL}/movements`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            const movements = await response.json();
            const container = document.getElementById('movements-list');
            container.innerHTML = '';
            
            const productsResponse = await fetch(`${API_URL}/products`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const products = await productsResponse.json();
            const productsMap = {};
            products.forEach(p => productsMap[p.id] = p.name);
            
            movements.reverse().slice(0, 50).forEach(movement => {
                const card = document.createElement('div');
                card.className = `movement-card ${movement.movement_type.toLowerCase()}`;
                
                const type = movement.movement_type === 'ENTRY' ? '📥 ENTRADA' : '📤 SAÍDA';
                const date = new Date(movement.created_at).toLocaleString('pt-BR');
                
                card.innerHTML = `
                    <h3>${type}</h3>
                    <p><strong>Produto:</strong> ${productsMap[movement.product_id] || 'Desconhecido'}</p>
                    <p><strong>Quantidade:</strong> ${movement.quantity} unidades</p>
                    <p><strong>Data:</strong> ${date}</p>
                    ${movement.note ? `<p><strong>Obs:</strong> ${movement.note}</p>` : ''}
                `;
                
                container.appendChild(card);
            });
        }
    } catch (error) {
        console.error(error);
    }
}

function hideAllViews() {
    document.querySelectorAll('.view').forEach(view => {
        view.classList.add('hidden');
    });
}

window.onload = () => {
    const savedToken = localStorage.getItem('token');
    if (savedToken) {
        token = savedToken;
        document.getElementById('login-section').classList.add('hidden');
        document.getElementById('main-section').classList.remove('hidden');
        showProducts();
    }
};