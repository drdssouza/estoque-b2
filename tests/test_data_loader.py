"""
Testes do DataLoader — camada de persistência de dados.
Cobre: produtos, movimentações, comandas, edge cases e stress.
Cada teste usa um diretório temporário isolado (nunca toca dados reais).
"""
import pytest
import threading
from backend.utils.data_loader import DataLoader


# ══════════════════════════════════════════════════════════════════════════════
# PRODUTOS
# ══════════════════════════════════════════════════════════════════════════════

class TestProdutos:

    def test_banco_vazio_retorna_produtos_default(self, loader):
        produtos = loader.load_products()
        assert len(produtos) > 0, "Banco novo deve ter produtos padrão"

    def test_adicionar_produto_retorna_id(self, loader):
        pid = loader.add_product("Item X", "cat", 1.0, 2.0, 5, 10)
        assert isinstance(pid, int)
        assert pid >= 1

    def test_ids_sequenciais_sem_lacunas(self, loader):
        ids = [loader.add_product(f"Produto {i}", "cat", 1.0, 2.0, 5, 10) for i in range(10)]
        for a, b in zip(ids, ids[1:]):
            assert b == a + 1, f"IDs não sequenciais: {a} → {b}"

    def test_produto_cadastrado_pode_ser_encontrado(self, loader):
        loader.add_product("Caneta Azul", "papelaria", 0.50, 1.50, 5, 20)
        df = loader.search_products(query="Caneta")
        assert len(df) == 1
        assert df.iloc[0]["name"] == "Caneta Azul"

    def test_busca_case_insensitive(self, loader):
        loader.add_product("Hortelã Fresca", "bebida", 1.0, 2.0, 5, 10)
        # Deve encontrar independente de maiúsculas/acentos
        assert len(loader.search_products(query="hortelã")) >= 1
        assert len(loader.search_products(query="HORTELÃ")) >= 1
        assert len(loader.search_products(query="Hortelã Fresca")) >= 1
        # Garante que o produto adicionado está nos resultados
        resultado = loader.search_products(query="Hortelã Fresca")
        assert any(r["name"] == "Hortelã Fresca" for _, r in resultado.iterrows())

    def test_busca_por_categoria(self, loader):
        loader.add_product("Coca-Cola", "bebida", 2.0, 5.0, 5, 10)
        loader.add_product("Ruffles", "snack", 3.0, 6.0, 5, 10)
        bebidas = loader.search_products(category="bebida")
        assert all(r["category"] == "bebida" for _, r in bebidas.iterrows())

    def test_busca_sem_resultado_retorna_vazio(self, loader):
        df = loader.search_products(query="xyzzy_inexistente")
        assert len(df) == 0

    def test_atualizar_preco_venda(self, loader):
        pid = loader.add_product("Item", "cat", 1.0, 2.0, 5, 10)
        loader.update_product(pid, sale_price=9.99)
        df = loader.load_products()
        row = df[df["id"] == pid].iloc[0]
        assert float(row["sale_price"]) == pytest.approx(9.99)

    def test_atualizar_multiplos_campos(self, loader):
        pid = loader.add_product("Item", "cat", 1.0, 2.0, 5, 10)
        loader.update_product(pid, name="Item Editado", minimum_stock=99, purchase_price=3.33)
        row = loader.load_products()[loader.load_products()["id"] == pid].iloc[0]
        assert row["name"] == "Item Editado"
        assert int(row["minimum_stock"]) == 99
        assert float(row["purchase_price"]) == pytest.approx(3.33)

    def test_desativar_produto(self, loader):
        pid = loader.add_product("Item", "cat", 1.0, 2.0, 5, 10)
        loader.deactivate_product(pid)
        row = loader.load_products()[loader.load_products()["id"] == pid].iloc[0]
        assert row["active"] == False

    def test_estoque_baixo_detectado(self, loader):
        loader.add_product("Crítico", "cat", 1.0, 2.0, minimum_stock=10, current_stock=5)
        baixo = loader.get_low_stock_products()
        assert len(baixo) > 0
        assert any(r["name"] == "Crítico" for _, r in baixo.iterrows())

    def test_produto_acima_minimo_nao_aparece_em_baixo_estoque(self, loader):
        loader.add_product("Folgado", "cat", 1.0, 2.0, minimum_stock=5, current_stock=100)
        baixo = loader.get_low_stock_products()
        nomes = [r["name"] for _, r in baixo.iterrows()]
        assert "Folgado" not in nomes

    def test_produto_exatamente_no_minimo_esta_em_baixo(self, loader):
        loader.add_product("Exato", "cat", 1.0, 2.0, minimum_stock=10, current_stock=10)
        baixo = loader.get_low_stock_products()
        assert any(r["name"] == "Exato" for _, r in baixo.iterrows())

    def test_cadastrar_100_produtos(self, loader):
        for i in range(100):
            loader.add_product(f"Produto_{i:03d}", "cat", float(i), float(i * 2), i, i * 3)
        df = loader.load_products()
        # Os defaults já existem; deve haver pelo menos 100 novos
        nomes = df["name"].tolist()
        assert all(f"Produto_{i:03d}" in nomes for i in range(100))

    def test_preco_zero_aceito(self, loader):
        pid = loader.add_product("Brinde", "cat", 0.0, 0.0, 0, 100)
        row = loader.load_products()[loader.load_products()["id"] == pid].iloc[0]
        assert float(row["sale_price"]) == 0.0

    def test_estoque_zero_aceito(self, loader):
        pid = loader.add_product("Esgotado", "cat", 1.0, 2.0, 5, 0)
        row = loader.load_products()[loader.load_products()["id"] == pid].iloc[0]
        assert int(row["current_stock"]) == 0


# ══════════════════════════════════════════════════════════════════════════════
# MOVIMENTAÇÕES
# ══════════════════════════════════════════════════════════════════════════════

class TestMovimentacoes:

    def test_entrada_aumenta_estoque(self, loader):
        pid = loader.add_product("Produto", "cat", 1.0, 2.0, 5, 10)
        loader.add_movement(pid, "ENTRY", 20)
        row = loader.load_products()[loader.load_products()["id"] == pid].iloc[0]
        assert int(row["current_stock"]) == 30

    def test_saida_diminui_estoque(self, loader):
        pid = loader.add_product("Produto", "cat", 1.0, 2.0, 5, 10)
        loader.add_movement(pid, "EXIT", 5)
        row = loader.load_products()[loader.load_products()["id"] == pid].iloc[0]
        assert int(row["current_stock"]) == 5

    def test_saida_com_estoque_insuficiente_retorna_erro(self, loader):
        pid = loader.add_product("Produto", "cat", 1.0, 2.0, 5, 10)
        mid, err = loader.add_movement(pid, "EXIT", 999)
        assert mid is None
        assert err is not None
        assert "insuficiente" in err.lower() or "disponível" in err.lower()

    def test_estoque_nao_muda_quando_ha_erro(self, loader):
        pid = loader.add_product("Produto", "cat", 1.0, 2.0, 5, 10)
        loader.add_movement(pid, "EXIT", 999)
        row = loader.load_products()[loader.load_products()["id"] == pid].iloc[0]
        assert int(row["current_stock"]) == 10  # inalterado

    def test_produto_inexistente_retorna_erro(self, loader):
        mid, err = loader.add_movement(999999, "ENTRY", 10)
        assert mid is None
        assert err is not None

    def test_saida_exata_do_estoque_funciona(self, loader):
        pid = loader.add_product("Produto", "cat", 1.0, 2.0, 5, 10)
        _, err = loader.add_movement(pid, "EXIT", 10)
        assert err is None
        row = loader.load_products()[loader.load_products()["id"] == pid].iloc[0]
        assert int(row["current_stock"]) == 0

    def test_saida_de_estoque_zero_retorna_erro(self, loader):
        pid = loader.add_product("Esgotado", "cat", 1.0, 2.0, 5, 0)
        mid, err = loader.add_movement(pid, "EXIT", 1)
        assert mid is None
        assert err is not None

    def test_ids_movimentacoes_sequenciais(self, loader):
        pid = loader.add_product("Produto", "cat", 1.0, 2.0, 0, 1000)
        ids = []
        for _ in range(20):
            mid, _ = loader.add_movement(pid, "EXIT", 1)
            ids.append(mid)
        for a, b in zip(ids, ids[1:]):
            assert b == a + 1

    def test_movimentacao_salva_nota(self, loader):
        pid = loader.add_product("Produto", "cat", 1.0, 2.0, 0, 50)
        loader.add_movement(pid, "ENTRY", 10, note="Reposição mensal")
        df = loader.load_movements()
        assert any("Reposição mensal" in str(n) for n in df["note"].tolist())

    def test_movimentacao_sem_nota_aceita(self, loader):
        pid = loader.add_product("Produto", "cat", 1.0, 2.0, 0, 50)
        mid, err = loader.add_movement(pid, "ENTRY", 5)
        assert err is None
        assert mid is not None

    def test_multiplas_entradas_acumulam_estoque(self, loader):
        pid = loader.add_product("Produto", "cat", 1.0, 2.0, 0, 0)
        for _ in range(10):
            loader.add_movement(pid, "ENTRY", 10)
        row = loader.load_products()[loader.load_products()["id"] == pid].iloc[0]
        assert int(row["current_stock"]) == 100

    def test_100_movimentacoes_alternadas(self, loader):
        pid = loader.add_product("Produto", "cat", 1.0, 2.0, 0, 0)
        # 100 entradas
        for _ in range(100):
            loader.add_movement(pid, "ENTRY", 1)
        # 50 saídas
        for _ in range(50):
            loader.add_movement(pid, "EXIT", 1)
        row = loader.load_products()[loader.load_products()["id"] == pid].iloc[0]
        assert int(row["current_stock"]) == 50

    def test_movimentacao_salva_timestamp(self, loader):
        pid = loader.add_product("Produto", "cat", 1.0, 2.0, 0, 50)
        loader.add_movement(pid, "ENTRY", 5)
        df = loader.load_movements()
        assert df.iloc[-1]["created_at"] is not None


# ══════════════════════════════════════════════════════════════════════════════
# COMANDAS
# ══════════════════════════════════════════════════════════════════════════════

class TestComandas:

    def test_criar_comanda_retorna_id(self, loader):
        oid = loader.add_order("João")
        assert isinstance(oid, int)
        assert oid >= 1

    def test_comanda_criada_com_status_aberta(self, loader):
        oid = loader.add_order("João")
        df = loader.load_orders()
        row = df[df["id"] == oid].iloc[0]
        assert row["status"] == "aberta"

    def test_comanda_criada_com_total_zero(self, loader):
        oid = loader.add_order("João")
        df = loader.load_orders()
        row = df[df["id"] == oid].iloc[0]
        assert float(row["total"]) == 0.0

    def test_ids_comandas_sequenciais(self, loader):
        ids = [loader.add_order(f"Cliente {i}") for i in range(10)]
        for a, b in zip(ids, ids[1:]):
            assert b == a + 1

    def test_adicionar_item_atualiza_total(self, loader):
        pid = loader.add_product("Produto", "cat", 1.0, 5.00, 0, 100)
        oid = loader.add_order("João")
        loader.add_order_item(oid, pid, 3, 5.00)
        df = loader.load_orders()
        row = df[df["id"] == oid].iloc[0]
        assert float(row["total"]) == pytest.approx(15.00)

    def test_multiplos_itens_somam_total_correto(self, loader):
        p1 = loader.add_product("P1", "cat", 1.0, 5.00, 0, 100)
        p2 = loader.add_product("P2", "cat", 1.0, 8.00, 0, 100)
        oid = loader.add_order("João")
        loader.add_order_item(oid, p1, 2, 5.00)   # 10.00
        loader.add_order_item(oid, p2, 3, 8.00)   # 24.00
        df = loader.load_orders()
        row = df[df["id"] == oid].iloc[0]
        assert float(row["total"]) == pytest.approx(34.00)

    def test_remover_item_recalcula_total(self, loader):
        p1 = loader.add_product("P1", "cat", 1.0, 5.00, 0, 100)
        p2 = loader.add_product("P2", "cat", 1.0, 8.00, 0, 100)
        oid = loader.add_order("João")
        loader.add_order_item(oid, p1, 2, 5.00)   # 10.00
        iid2 = loader.add_order_item(oid, p2, 3, 8.00)  # 24.00
        loader.remove_order_item(iid2)
        df = loader.load_orders()
        row = df[df["id"] == oid].iloc[0]
        assert float(row["total"]) == pytest.approx(10.00)

    def test_remover_item_inexistente_retorna_false(self, loader):
        assert loader.remove_order_item(999999) == False

    def test_atualizar_quantidade_recalcula_total(self, loader):
        pid = loader.add_product("Produto", "cat", 1.0, 10.00, 0, 100)
        oid = loader.add_order("João")
        iid = loader.add_order_item(oid, pid, 1, 10.00)
        loader.update_order_item_quantity(iid, 5)
        df = loader.load_orders()
        row = df[df["id"] == oid].iloc[0]
        assert float(row["total"]) == pytest.approx(50.00)

    def test_atualizar_quantidade_para_zero_remove_item(self, loader):
        pid = loader.add_product("Produto", "cat", 1.0, 10.00, 0, 100)
        oid = loader.add_order("João")
        iid = loader.add_order_item(oid, pid, 3, 10.00)
        loader.update_order_item_quantity(iid, 0)
        items = loader.load_order_items()
        assert len(items[items["id"] == iid]) == 0

    def test_atualizar_quantidade_negativa_remove_item(self, loader):
        pid = loader.add_product("Produto", "cat", 1.0, 10.00, 0, 100)
        oid = loader.add_order("João")
        iid = loader.add_order_item(oid, pid, 3, 10.00)
        loader.update_order_item_quantity(iid, -1)
        items = loader.load_order_items()
        assert len(items[items["id"] == iid]) == 0

    def test_atualizar_item_inexistente_retorna_false(self, loader):
        assert loader.update_order_item_quantity(999999, 5) == False

    def test_fechar_comanda_muda_status(self, loader):
        pid = loader.add_product("Produto", "cat", 1.0, 5.00, 0, 100)
        oid = loader.add_order("João")
        loader.add_order_item(oid, pid, 1, 5.00)
        loader.close_order(oid)
        df = loader.load_orders()
        row = df[df["id"] == oid].iloc[0]
        assert row["status"] == "fechada"

    def test_fechar_comanda_gera_movimentacoes_de_saida(self, loader):
        pid = loader.add_product("Produto", "cat", 1.0, 5.00, 0, 100)
        oid = loader.add_order("João")
        loader.add_order_item(oid, pid, 5, 5.00)
        loader.close_order(oid)
        df = loader.load_movements()
        exits = df[(df["product_id"] == pid) & (df["movement_type"] == "EXIT")]
        assert len(exits) > 0
        assert int(exits.iloc[-1]["quantity"]) == 5

    def test_fechar_comanda_diminui_estoque(self, loader):
        pid = loader.add_product("Produto", "cat", 1.0, 5.00, 0, 100)
        oid = loader.add_order("João")
        loader.add_order_item(oid, pid, 7, 5.00)
        loader.close_order(oid)
        row = loader.load_products()[loader.load_products()["id"] == pid].iloc[0]
        assert int(row["current_stock"]) == 93

    def test_excluir_comanda_remove_pedido_e_itens(self, loader):
        pid = loader.add_product("Produto", "cat", 1.0, 5.00, 0, 100)
        oid = loader.add_order("João")
        loader.add_order_item(oid, pid, 2, 5.00)
        loader.delete_order(oid)
        orders = loader.load_orders()
        items = loader.load_order_items()
        assert len(orders[orders["id"] == oid]) == 0
        assert len(items[items["order_id"] == oid]) == 0

    def test_excluir_comanda_nao_afeta_outras_comandas(self, loader):
        pid = loader.add_product("Produto", "cat", 1.0, 5.00, 0, 100)
        o1 = loader.add_order("João")
        o2 = loader.add_order("Maria")
        loader.add_order_item(o1, pid, 2, 5.00)
        loader.add_order_item(o2, pid, 3, 5.00)
        loader.delete_order(o1)
        orders = loader.load_orders()
        assert len(orders[orders["id"] == o2]) == 1

    def test_comanda_vazia_tem_total_zero(self, loader):
        oid = loader.add_order("Vazio")
        df = loader.load_orders()
        assert float(df[df["id"] == oid].iloc[0]["total"]) == 0.0

    def test_added_at_preenchido_ao_adicionar_item(self, loader):
        pid = loader.add_product("Produto", "cat", 1.0, 5.00, 0, 100)
        oid = loader.add_order("João")
        loader.add_order_item(oid, pid, 1, 5.00)
        items = loader.load_order_items()
        last = items.iloc[-1]
        assert last["added_at"] is not None and str(last["added_at"]) != "NaT"

    def test_migracao_coluna_added_at(self, loader):
        """Se o arquivo não tiver coluna added_at, deve ser adicionada automaticamente."""
        import pandas as pd
        # Cria arquivo sem a coluna added_at
        items_sem_coluna = pd.DataFrame({
            "id": pd.Series([1], dtype="int64"),
            "order_id": pd.Series([1], dtype="int64"),
            "product_id": pd.Series([1], dtype="int64"),
            "quantity": pd.Series([1], dtype="int64"),
            "unit_price": pd.Series([5.0], dtype="float64"),
            "subtotal": pd.Series([5.0], dtype="float64"),
        })
        from pathlib import Path
        items_sem_coluna.to_parquet(Path(loader.data_dir) / "order_items.parquet", index=False)
        # load_order_items deve migrar automaticamente
        df = loader.load_order_items()
        assert "added_at" in df.columns

    def test_subtotal_calculado_corretamente(self, loader):
        pid = loader.add_product("Produto", "cat", 1.0, 7.50, 0, 100)
        oid = loader.add_order("João")
        loader.add_order_item(oid, pid, 4, 7.50)
        items = loader.load_order_items()
        last = items.iloc[-1]
        assert float(last["subtotal"]) == pytest.approx(30.00)

    def test_get_order_items_retorna_apenas_itens_da_comanda(self, loader):
        p1 = loader.add_product("P1", "cat", 1.0, 5.00, 0, 100)
        p2 = loader.add_product("P2", "cat", 1.0, 8.00, 0, 100)
        o1 = loader.add_order("João")
        o2 = loader.add_order("Maria")
        loader.add_order_item(o1, p1, 1, 5.00)
        loader.add_order_item(o2, p2, 1, 8.00)
        items_o1 = loader.load_order_items()
        items_o1 = items_o1[items_o1["order_id"] == o1]
        assert len(items_o1) == 1
        assert int(items_o1.iloc[0]["product_id"]) == p1


# ══════════════════════════════════════════════════════════════════════════════
# CONCORRÊNCIA
# ══════════════════════════════════════════════════════════════════════════════

class TestConcorrencia:

    def test_escritas_concorrentes_nao_corrompem_dados(self, loader):
        """10 threads escrevendo produtos ao mesmo tempo — IDs devem ser únicos."""
        loader.add_product("Base", "cat", 1.0, 2.0, 0, 9999)
        ids_criados = []
        erros = []
        lock = threading.Lock()

        def criar_produto(i):
            try:
                pid = loader.add_product(f"Concorrente_{i}", "cat", 1.0, 2.0, 0, 10)
                with lock:
                    ids_criados.append(pid)
            except Exception as e:
                with lock:
                    erros.append(str(e))

        threads = [threading.Thread(target=criar_produto, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(erros) == 0, f"Erros nas threads: {erros}"
        assert len(ids_criados) == len(set(ids_criados)), "IDs duplicados detectados!"

    def test_movimentacoes_concorrentes_nao_corrompem_estoque(self, loader):
        """5 threads adicionando estoque ao mesmo produto — total deve ser exato."""
        pid = loader.add_product("Produto Shared", "cat", 1.0, 2.0, 0, 0)
        erros = []
        lock = threading.Lock()

        def adicionar(qtd):
            try:
                loader.add_movement(pid, "ENTRY", qtd)
            except Exception as e:
                with lock:
                    erros.append(str(e))

        threads = [threading.Thread(target=adicionar, args=(10,)) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(erros) == 0
        row = loader.load_products()[loader.load_products()["id"] == pid].iloc[0]
        assert int(row["current_stock"]) == 50
