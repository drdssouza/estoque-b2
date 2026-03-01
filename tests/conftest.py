import sys
import pytest
import tempfile
import shutil
from pathlib import Path

# Garante que o root do projeto está no path
root = Path(__file__).parent.parent
sys.path.insert(0, str(root))

from backend.utils.data_loader import DataLoader


# ── Qt (necessário para controllers PySide6) ──────────────────────────────────

@pytest.fixture(scope="session")
def qt_app():
    """QApplication única para toda a sessão de testes."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


# ── DataLoader isolado ────────────────────────────────────────────────────────

@pytest.fixture
def tmp_data_dir():
    """Diretório temporário isolado para cada teste — nunca afeta dados reais."""
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def loader(tmp_data_dir):
    """DataLoader apontando para diretório temporário isolado."""
    return DataLoader(data_dir=tmp_data_dir)


@pytest.fixture
def loader_with_products(loader):
    """DataLoader com 3 produtos padrão já cadastrados."""
    loader.add_product("Água Mineral 500ml", "bebida", 1.50, 3.00, 20, 50)
    loader.add_product("Coca-Cola 350ml", "bebida", 2.50, 5.00, 15, 30)
    loader.add_product("Ruffles 100g", "snack", 4.00, 8.00, 10, 25)
    return loader


@pytest.fixture
def loader_with_open_order(loader_with_products):
    """DataLoader com produtos + uma comanda aberta com 2 itens."""
    dl = loader_with_products
    order_id = dl.add_order("Cliente Teste")
    products = dl.load_products()
    p1_id = int(products.iloc[0]["id"])
    p2_id = int(products.iloc[1]["id"])
    p1_price = float(products.iloc[0]["sale_price"])
    p2_price = float(products.iloc[1]["sale_price"])
    dl.add_order_item(order_id, p1_id, 3, p1_price)
    dl.add_order_item(order_id, p2_id, 2, p2_price)
    return dl, order_id, p1_id, p2_id


# ── Controllers com loader injetado ──────────────────────────────────────────

@pytest.fixture
def products_ctrl(qt_app, loader):
    from desktop.controllers.products_controller import ProductsController
    ctrl = ProductsController()
    ctrl.data_loader = loader
    return ctrl


@pytest.fixture
def orders_ctrl(qt_app, loader):
    from desktop.controllers.orders_controller import OrdersController
    ctrl = OrdersController()
    ctrl.data_loader = loader
    return ctrl


@pytest.fixture
def movements_ctrl(qt_app, loader):
    from desktop.controllers.movements_controller import MovementsController
    ctrl = MovementsController()
    ctrl.data_loader = loader
    return ctrl


@pytest.fixture
def reports_ctrl(qt_app, loader):
    from desktop.controllers.reports_controller import ReportsController
    ctrl = ReportsController()
    ctrl.data_loader = loader
    return ctrl


@pytest.fixture
def dashboard_ctrl(qt_app, loader):
    from desktop.controllers.dashboard_controller import DashboardController
    ctrl = DashboardController()
    ctrl.data_loader = loader
    return ctrl
