"""
Testes de todos os controllers.
Cada controller tem o DataLoader injetado (isolado) via conftest.
"""
import pytest
from datetime import datetime, timedelta


# ══════════════════════════════════════════════════════════════════════════════
# PRODUCTS CONTROLLER
# ══════════════════════════════════════════════════════════════════════════════

class TestProductsController:

    def test_add_product_retorna_id(self, products_ctrl):
        pid = products_ctrl.add_product("Produto X", "cat", 1.0, 2.0, 5, 10)
        assert isinstance(pid, int) and pid >= 1

    def test_add_product_emite_sinal(self, products_ctrl):
        emitido = []
        products_ctrl.products_updated.connect(lambda: emitido.append(1))
        products_ctrl.add_product("X", "cat", 1.0, 2.0, 5, 10)
        assert len(emitido) == 1

    def test_get_all_products_retorna_lista(self, products_ctrl):
        products_ctrl.add_product("P1", "cat", 1.0, 2.0, 5, 10)
        resultado = products_ctrl.get_all_products()
        assert isinstance(resultado, list)
        assert any(p["name"] == "P1" for p in resultado)

    def test_update_product_altera_campo(self, products_ctrl):
        pid = products_ctrl.add_product("Original", "cat", 1.0, 2.0, 5, 10)
        products_ctrl.update_product(pid, name="Atualizado", sale_price=9.99)
        prods = products_ctrl.get_all_products()
        atualizado = next(p for p in prods if p["id"] == pid)
        assert atualizado["name"] == "Atualizado"
        assert float(atualizado["sale_price"]) == pytest.approx(9.99)

    def test_update_product_emite_sinal(self, products_ctrl):
        pid = products_ctrl.add_product("X", "cat", 1.0, 2.0, 5, 10)
        emitido = []
        products_ctrl.products_updated.connect(lambda: emitido.append(1))
        products_ctrl.update_product(pid, sale_price=5.0)
        assert len(emitido) == 1

    def test_deactivate_product_marca_inativo(self, products_ctrl):
        pid = products_ctrl.add_product("Inativo", "cat", 1.0, 2.0, 5, 10)
        products_ctrl.deactivate_product(pid)
        prods = products_ctrl.get_all_products()
        prod = next(p for p in prods if p["id"] == pid)
        assert prod["active"] == False

    def test_deactivate_product_emite_sinal(self, products_ctrl):
        pid = products_ctrl.add_product("X", "cat", 1.0, 2.0, 5, 10)
        emitido = []
        products_ctrl.products_updated.connect(lambda: emitido.append(1))
        products_ctrl.deactivate_product(pid)
        assert len(emitido) == 1

    def test_search_products_por_nome(self, products_ctrl):
        products_ctrl.add_product("Caneta Azul", "papelaria", 0.5, 1.0, 5, 10)
        resultado = products_ctrl.search_products(query="Caneta")
        assert any(p["name"] == "Caneta Azul" for p in resultado)

    def test_search_products_por_categoria(self, products_ctrl):
        products_ctrl.add_product("Produto Especial", "especial_cat", 1.0, 2.0, 5, 10)
        resultado = products_ctrl.search_products(category="especial_cat")
        assert all(p["category"] == "especial_cat" for p in resultado)

    def test_search_products_sem_resultado(self, products_ctrl):
        resultado = products_ctrl.search_products(query="xyzzy_inexistente")
        assert resultado == []

    def test_adicionar_10_produtos_ids_unicos(self, products_ctrl):
        ids = [products_ctrl.add_product(f"P{i}", "cat", 1.0, 2.0, 5, 10) for i in range(10)]
        assert len(ids) == len(set(ids))


# ══════════════════════════════════════════════════════════════════════════════
# ORDERS CONTROLLER
# ══════════════════════════════════════════════════════════════════════════════

class TestOrdersController:

    def _add_produto(self, orders_ctrl, nome="Produto", preco=5.0, estoque=100):
        """Helper: adiciona produto direto no data_loader do controller."""
        return orders_ctrl.data_loader.add_product(nome, "cat", 1.0, preco, 0, estoque)

    def test_create_order_retorna_id(self, orders_ctrl):
        oid = orders_ctrl.create_order("João")
        assert isinstance(oid, int) and oid >= 1

    def test_create_order_emite_sinal(self, orders_ctrl):
        emitido = []
        orders_ctrl.orders_updated.connect(lambda: emitido.append(1))
        orders_ctrl.create_order("João")
        assert len(emitido) == 1

    def test_add_item_produto_valido_retorna_true(self, orders_ctrl):
        pid = self._add_produto(orders_ctrl, preco=7.50)
        oid = orders_ctrl.create_order("João")
        assert orders_ctrl.add_item_to_order(oid, pid, 3) == True

    def test_add_item_usa_preco_de_venda_do_produto(self, orders_ctrl):
        pid = self._add_produto(orders_ctrl, preco=9.99)
        oid = orders_ctrl.create_order("João")
        orders_ctrl.add_item_to_order(oid, pid, 2)
        items = orders_ctrl.get_order_items(oid)
        assert float(items[0]["unit_price"]) == pytest.approx(9.99)

    def test_add_item_produto_inexistente_retorna_false(self, orders_ctrl):
        oid = orders_ctrl.create_order("João")
        assert orders_ctrl.add_item_to_order(oid, 999999, 1) == False

    def test_add_item_nao_emite_sinal_quando_produto_inexistente(self, orders_ctrl):
        oid = orders_ctrl.create_order("João")
        emitido = []
        orders_ctrl.orders_updated.connect(lambda: emitido.append(1))
        orders_ctrl.add_item_to_order(oid, 999999, 1)
        assert len(emitido) == 0

    def test_get_order_items_inclui_nome_do_produto(self, orders_ctrl):
        pid = self._add_produto(orders_ctrl, nome="Cerveja Gelada", preco=6.0)
        oid = orders_ctrl.create_order("João")
        orders_ctrl.add_item_to_order(oid, pid, 1)
        items = orders_ctrl.get_order_items(oid)
        assert items[0]["product_name"] == "Cerveja Gelada"

    def test_get_order_items_produto_inexistente_mostra_desconhecido(self, orders_ctrl):
        oid = orders_ctrl.create_order("João")
        # Insere item com product_id inválido diretamente no data_loader
        orders_ctrl.data_loader.add_order_item(oid, 99999, 1, 5.0)
        items = orders_ctrl.get_order_items(oid)
        assert items[0]["product_name"] == "Produto desconhecido"

    def test_remove_item_retorna_true(self, orders_ctrl):
        pid = self._add_produto(orders_ctrl)
        oid = orders_ctrl.create_order("João")
        orders_ctrl.add_item_to_order(oid, pid, 2)
        items_df = orders_ctrl.data_loader.load_order_items()
        iid = int(items_df.iloc[-1]["id"])
        assert orders_ctrl.remove_item_from_order(iid) == True

    def test_remove_item_inexistente_retorna_false(self, orders_ctrl):
        assert orders_ctrl.remove_item_from_order(999999) == False

    def test_remove_item_nao_emite_sinal_quando_falha(self, orders_ctrl):
        emitido = []
        orders_ctrl.orders_updated.connect(lambda: emitido.append(1))
        orders_ctrl.remove_item_from_order(999999)
        assert len(emitido) == 0

    def test_update_item_quantity(self, orders_ctrl):
        pid = self._add_produto(orders_ctrl, preco=10.0)
        oid = orders_ctrl.create_order("João")
        orders_ctrl.add_item_to_order(oid, pid, 1)
        items_df = orders_ctrl.data_loader.load_order_items()
        iid = int(items_df.iloc[-1]["id"])
        assert orders_ctrl.update_item_quantity(iid, 5) == True
        # Total deve ser 50.00
        orders_df = orders_ctrl.data_loader.load_orders()
        total = float(orders_df[orders_df["id"] == oid].iloc[0]["total"])
        assert total == pytest.approx(50.0)

    def test_close_order_muda_status(self, orders_ctrl):
        pid = self._add_produto(orders_ctrl)
        oid = orders_ctrl.create_order("João")
        orders_ctrl.add_item_to_order(oid, pid, 1)
        orders_ctrl.close_order(oid)
        orders = orders_ctrl.get_all_orders()
        ordem = next(o for o in orders if o["id"] == oid)
        assert ordem["status"] == "fechada"

    def test_delete_order_remove_comanda(self, orders_ctrl):
        oid = orders_ctrl.create_order("João")
        orders_ctrl.delete_order(oid)
        orders = orders_ctrl.get_all_orders()
        assert not any(o["id"] == oid for o in orders)

    def test_get_open_orders_retorna_apenas_abertas(self, orders_ctrl):
        pid = self._add_produto(orders_ctrl)
        o1 = orders_ctrl.create_order("João")
        o2 = orders_ctrl.create_order("Maria")
        orders_ctrl.add_item_to_order(o1, pid, 1)
        orders_ctrl.close_order(o1)
        abertas = orders_ctrl.get_open_orders()
        assert all(o["status"] == "aberta" for o in abertas)
        assert any(o["id"] == o2 for o in abertas)
        assert not any(o["id"] == o1 for o in abertas)

    def test_get_closed_orders_retorna_apenas_fechadas(self, orders_ctrl):
        pid = self._add_produto(orders_ctrl)
        o1 = orders_ctrl.create_order("João")
        orders_ctrl.create_order("Maria")
        orders_ctrl.add_item_to_order(o1, pid, 1)
        orders_ctrl.close_order(o1)
        fechadas = orders_ctrl.get_closed_orders()
        assert all(o["status"] == "fechada" for o in fechadas)

    def test_search_orders_por_nome(self, orders_ctrl):
        orders_ctrl.create_order("Eduardo Silva")
        orders_ctrl.create_order("Maria Santos")
        resultado = orders_ctrl.search_orders(query="Eduardo")
        assert all("Eduardo" in o["customer_name"] for o in resultado)

    def test_search_orders_por_status(self, orders_ctrl):
        pid = self._add_produto(orders_ctrl)
        o1 = orders_ctrl.create_order("João")
        orders_ctrl.create_order("Maria")
        orders_ctrl.add_item_to_order(o1, pid, 1)
        orders_ctrl.close_order(o1)
        fechadas = orders_ctrl.search_orders(status_filter="fechada")
        assert all(o["status"] == "fechada" for o in fechadas)

    def test_search_orders_combinado_nome_e_status(self, orders_ctrl):
        pid = self._add_produto(orders_ctrl)
        o1 = orders_ctrl.create_order("Ana")
        orders_ctrl.create_order("Ana")
        orders_ctrl.add_item_to_order(o1, pid, 1)
        orders_ctrl.close_order(o1)
        resultado = orders_ctrl.search_orders(query="Ana", status_filter="fechada")
        assert len(resultado) == 1
        assert resultado[0]["status"] == "fechada"

    def test_remove_last_entry_for_product_reduz_quantidade(self, orders_ctrl):
        pid = self._add_produto(orders_ctrl, preco=5.0)
        oid = orders_ctrl.create_order("João")
        orders_ctrl.add_item_to_order(oid, pid, 3)
        orders_ctrl.remove_last_entry_for_product(oid, pid)
        items_df = orders_ctrl.data_loader.load_order_items()
        item = items_df[items_df["order_id"] == oid].iloc[0]
        assert int(item["quantity"]) == 2

    def test_remove_last_entry_for_product_sem_itens_retorna_false(self, orders_ctrl):
        pid = self._add_produto(orders_ctrl)
        oid = orders_ctrl.create_order("João")
        assert orders_ctrl.remove_last_entry_for_product(oid, pid) == False

    def test_remove_last_entry_remove_item_quando_quantidade_chega_a_zero(self, orders_ctrl):
        pid = self._add_produto(orders_ctrl, preco=5.0)
        oid = orders_ctrl.create_order("João")
        orders_ctrl.add_item_to_order(oid, pid, 1)
        orders_ctrl.remove_last_entry_for_product(oid, pid)
        items_df = orders_ctrl.data_loader.load_order_items()
        assert len(items_df[items_df["order_id"] == oid]) == 0

    def test_remove_last_entry_remove_entrada_mais_recente(self, orders_ctrl):
        """Com múltiplas entradas do mesmo produto, remove a última (maior ID)."""
        pid = self._add_produto(orders_ctrl, preco=5.0)
        oid = orders_ctrl.create_order("João")
        orders_ctrl.data_loader.add_order_item(oid, pid, 10, 5.0)  # entrada 1: qty=10
        orders_ctrl.data_loader.add_order_item(oid, pid, 5, 5.0)   # entrada 2: qty=5
        orders_ctrl.remove_last_entry_for_product(oid, pid)
        items_df = orders_ctrl.data_loader.load_order_items()
        itens = items_df[items_df["order_id"] == oid]
        # A última entrada (qty=5) deve ter virado qty=4; a primeira (qty=10) intacta
        qtds = sorted(itens["quantity"].tolist())
        assert 10 in qtds  # primeira intacta
        assert 4 in qtds   # segunda reduzida


# ══════════════════════════════════════════════════════════════════════════════
# MOVEMENTS CONTROLLER
# ══════════════════════════════════════════════════════════════════════════════

class TestMovementsController:

    def _add_produto(self, movements_ctrl, estoque=50):
        return movements_ctrl.data_loader.add_product("Produto", "cat", 1.0, 2.0, 0, estoque)

    def test_add_movement_entrada_retorna_id(self, movements_ctrl):
        pid = self._add_produto(movements_ctrl)
        mid, err = movements_ctrl.add_movement(pid, "ENTRY", 10)
        assert err is None
        assert mid is not None

    def test_add_movement_emite_sinal(self, movements_ctrl):
        pid = self._add_produto(movements_ctrl)
        emitido = []
        movements_ctrl.movements_updated.connect(lambda: emitido.append(1))
        movements_ctrl.add_movement(pid, "ENTRY", 5)
        assert len(emitido) == 1

    def test_add_movement_estoque_insuficiente_retorna_erro(self, movements_ctrl):
        pid = self._add_produto(movements_ctrl, estoque=5)
        mid, err = movements_ctrl.add_movement(pid, "EXIT", 100)
        assert mid is None
        assert err is not None

    def test_add_movement_nao_emite_sinal_quando_erro(self, movements_ctrl):
        pid = self._add_produto(movements_ctrl, estoque=0)
        emitido = []
        movements_ctrl.movements_updated.connect(lambda: emitido.append(1))
        movements_ctrl.add_movement(pid, "EXIT", 1)
        assert len(emitido) == 0

    def test_get_all_movements(self, movements_ctrl):
        pid = self._add_produto(movements_ctrl)
        movements_ctrl.add_movement(pid, "ENTRY", 10)
        movs = movements_ctrl.get_all_movements()
        assert len(movs) >= 1

    def test_get_product_movements_filtra_por_produto(self, movements_ctrl):
        p1 = self._add_produto(movements_ctrl)
        p2 = movements_ctrl.data_loader.add_product("P2", "cat", 1.0, 2.0, 0, 100)
        movements_ctrl.add_movement(p1, "ENTRY", 10)
        movements_ctrl.add_movement(p2, "ENTRY", 20)
        movs_p1 = movements_ctrl.get_product_movements(p1)
        assert all(m["product_id"] == p1 for m in movs_p1)

    def test_delete_movement_reverte_estoque_entrada(self, movements_ctrl):
        pid = self._add_produto(movements_ctrl, estoque=50)
        mid, _ = movements_ctrl.add_movement(pid, "ENTRY", 30)
        # Estoque agora: 80
        movements_ctrl.delete_movement(mid)
        # Deve voltar a 50
        prods = movements_ctrl.data_loader.load_products()
        row = prods[prods["id"] == pid].iloc[0]
        assert int(row["current_stock"]) == 50

    def test_delete_movement_reverte_estoque_saida(self, movements_ctrl):
        pid = self._add_produto(movements_ctrl, estoque=50)
        mid, _ = movements_ctrl.add_movement(pid, "EXIT", 20)
        # Estoque agora: 30
        movements_ctrl.delete_movement(mid)
        # Deve voltar a 50
        prods = movements_ctrl.data_loader.load_products()
        row = prods[prods["id"] == pid].iloc[0]
        assert int(row["current_stock"]) == 50

    def test_delete_movement_inexistente_retorna_false(self, movements_ctrl):
        assert movements_ctrl.delete_movement(999999) == False

    def test_delete_movement_emite_sinal(self, movements_ctrl):
        pid = self._add_produto(movements_ctrl)
        mid, _ = movements_ctrl.add_movement(pid, "ENTRY", 5)
        emitido = []
        movements_ctrl.movements_updated.connect(lambda: emitido.append(1))
        movements_ctrl.delete_movement(mid)
        assert len(emitido) == 1

    def test_delete_movement_nao_emite_sinal_quando_nao_existe(self, movements_ctrl):
        emitido = []
        movements_ctrl.movements_updated.connect(lambda: emitido.append(1))
        movements_ctrl.delete_movement(999999)
        assert len(emitido) == 0


# ══════════════════════════════════════════════════════════════════════════════
# REPORTS CONTROLLER
# ══════════════════════════════════════════════════════════════════════════════

class TestReportsController:

    def _setup_dia_com_vendas(self, reports_ctrl):
        """Cria produtos, abre e fecha comandas para hoje."""
        dl = reports_ctrl.data_loader
        p1 = dl.add_product("Água", "bebida", 1.0, 3.0, 0, 1000)
        p2 = dl.add_product("Coca", "bebida", 2.0, 5.0, 0, 1000)
        p3 = dl.add_product("Ruffles", "snack", 3.0, 8.0, 0, 1000)

        o1 = dl.add_order("João")
        dl.add_order_item(o1, p1, 2, 3.0)   # 6.00
        dl.add_order_item(o1, p2, 1, 5.0)   # 5.00
        dl.close_order(o1)

        o2 = dl.add_order("Maria")
        dl.add_order_item(o2, p3, 3, 8.0)   # 24.00
        dl.close_order(o2)

        return p1, p2, p3, o1, o2

    def test_relatorio_sem_vendas_retorna_zeros(self, reports_ctrl):
        relatorio = reports_ctrl.get_daily_report()
        assert relatorio["total_orders"] == 0
        assert relatorio["total_revenue"] == 0.0

    def test_relatorio_conta_comandas_fechadas_do_dia(self, reports_ctrl):
        self._setup_dia_com_vendas(reports_ctrl)
        relatorio = reports_ctrl.get_daily_report()
        assert relatorio["total_orders"] == 2

    def test_relatorio_calcula_receita_total(self, reports_ctrl):
        self._setup_dia_com_vendas(reports_ctrl)
        relatorio = reports_ctrl.get_daily_report()
        assert relatorio["total_revenue"] == pytest.approx(35.0)  # 11+24

    def test_relatorio_agrupa_por_categoria(self, reports_ctrl):
        self._setup_dia_com_vendas(reports_ctrl)
        relatorio = reports_ctrl.get_daily_report()
        cats = relatorio["by_category"]
        assert "bebida" in cats
        assert "snack" in cats
        assert cats["bebida"]["revenue"] == pytest.approx(11.0)
        assert cats["snack"]["revenue"] == pytest.approx(24.0)

    def test_relatorio_lista_por_produto(self, reports_ctrl):
        self._setup_dia_com_vendas(reports_ctrl)
        relatorio = reports_ctrl.get_daily_report()
        nomes = [p["product_name"] for p in relatorio["by_product"]]
        assert "Água" in nomes
        assert "Coca" in nomes
        assert "Ruffles" in nomes

    def test_relatorio_lista_comandas_do_dia(self, reports_ctrl):
        self._setup_dia_com_vendas(reports_ctrl)
        relatorio = reports_ctrl.get_daily_report()
        nomes = [o["customer_name"] for o in relatorio["order_list"]]
        assert "João" in nomes
        assert "Maria" in nomes

    def test_relatorio_nao_conta_comandas_abertas(self, reports_ctrl):
        dl = reports_ctrl.data_loader
        p = dl.add_product("Prod", "cat", 1.0, 5.0, 0, 100)
        oid = dl.add_order("Aberta")
        dl.add_order_item(oid, p, 1, 5.0)
        # NÃO fecha — comanda permanece aberta
        relatorio = reports_ctrl.get_daily_report()
        nomes = [o["customer_name"] for o in relatorio["order_list"]]
        assert "Aberta" not in nomes

    def test_get_available_dates_retorna_datas_com_fechamentos(self, reports_ctrl):
        self._setup_dia_com_vendas(reports_ctrl)
        datas = reports_ctrl.get_available_dates()
        assert len(datas) >= 1
        assert datetime.now().date() in datas

    def test_get_available_dates_sem_fechamentos_retorna_vazio(self, reports_ctrl):
        datas = reports_ctrl.get_available_dates()
        assert datas == []

    def test_produtos_ordenados_por_receita_descendente(self, reports_ctrl):
        self._setup_dia_com_vendas(reports_ctrl)
        relatorio = reports_ctrl.get_daily_report()
        receitas = [p["revenue"] for p in relatorio["by_product"]]
        assert receitas == sorted(receitas, reverse=True)


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD CONTROLLER
# ══════════════════════════════════════════════════════════════════════════════

class TestDashboardController:

    def test_dashboard_banco_vazio_retorna_estrutura_completa(self, dashboard_ctrl):
        data = dashboard_ctrl.get_dashboard_data()
        campos_obrigatorios = [
            "total_products", "total_bebidas", "total_doces",
            "total_salgado", "total_acessorios", "low_stock_count",
            "low_stock_items", "entries_7days", "exits_7days", "top_products"
        ]
        for campo in campos_obrigatorios:
            assert campo in data, f"Campo ausente: {campo}"

    def test_dashboard_conta_produtos_ativos(self, dashboard_ctrl):
        dl = dashboard_ctrl.data_loader
        dl.add_product("P1", "bebida", 1.0, 2.0, 5, 10)
        dl.add_product("P2", "bebida", 1.0, 2.0, 5, 10)
        dl.add_product("P3", "snack", 1.0, 2.0, 5, 10)
        data = dashboard_ctrl.get_dashboard_data()
        # Os defaults já existem; deve contar pelo menos os 3 adicionados
        assert data["total_products"] >= 3

    def test_dashboard_nao_conta_produto_inativo(self, dashboard_ctrl):
        dl = dashboard_ctrl.data_loader
        pid = dl.add_product("Inativo", "bebida", 1.0, 2.0, 5, 10)
        before = dashboard_ctrl.get_dashboard_data()["total_products"]
        dl.deactivate_product(pid)
        after = dashboard_ctrl.get_dashboard_data()["total_products"]
        assert after == before - 1

    def test_dashboard_conta_por_categoria(self, dashboard_ctrl):
        dl = dashboard_ctrl.data_loader
        # Remove defaults limpando via loader isolado e adicionando controlado
        dl.add_product("Beb1", "bebida", 1.0, 2.0, 0, 10)
        dl.add_product("Beb2", "bebida", 1.0, 2.0, 0, 10)
        data = dashboard_ctrl.get_dashboard_data()
        assert data["total_bebidas"] >= 2

    def test_dashboard_detecta_estoque_baixo(self, dashboard_ctrl):
        dl = dashboard_ctrl.data_loader
        dl.add_product("Crítico", "cat", 1.0, 2.0, minimum_stock=20, current_stock=5)
        data = dashboard_ctrl.get_dashboard_data()
        assert data["low_stock_count"] >= 1
        nomes = [p["name"] for p in data["low_stock_items"]]
        assert "Crítico" in nomes

    def test_dashboard_conta_movimentacoes_recentes(self, dashboard_ctrl):
        dl = dashboard_ctrl.data_loader
        pid = dl.add_product("Prod", "cat", 1.0, 2.0, 0, 100)
        dl.add_movement(pid, "ENTRY", 10)
        dl.add_movement(pid, "EXIT", 5)
        data = dashboard_ctrl.get_dashboard_data()
        assert data["entries_7days"] >= 1
        assert data["exits_7days"] >= 1

    def test_dashboard_top_products_tem_no_maximo_5(self, dashboard_ctrl):
        dl = dashboard_ctrl.data_loader
        for i in range(10):
            pid = dl.add_product(f"Prod{i}", "cat", 1.0, 2.0, 0, 100)
            dl.add_movement(pid, "ENTRY", i + 1)
        data = dashboard_ctrl.get_dashboard_data()
        assert len(data["top_products"]) <= 5
