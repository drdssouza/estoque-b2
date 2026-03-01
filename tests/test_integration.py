"""
Testes de integração — fluxos completos end-to-end e stress.
Simula uso real do sistema: criar produtos → movimentar → abrir comanda → fechar.

Marcadores:
  pytest -m "not slow"   → só testes rápidos
  pytest -m slow         → só testes de stress pesado (podem demorar vários minutos)
"""
import pytest
import random
from backend.utils.data_loader import DataLoader


# ══════════════════════════════════════════════════════════════════════════════
# FLUXO COMPLETO DE UMA COMANDA
# ══════════════════════════════════════════════════════════════════════════════

class TestFluxoComanda:

    def test_ciclo_completo_abertura_itens_fechamento(self, loader):
        """Cria produto → abre comanda → adiciona itens → fecha → verifica estoque."""
        pid = loader.add_product("Cerveja 600ml", "bebida", 3.00, 7.00, 10, 50)

        oid = loader.add_order("Eduardo")
        loader.add_order_item(oid, pid, 6, 7.00)

        # Verifica total antes de fechar
        ordem = loader.load_orders()[loader.load_orders()["id"] == oid].iloc[0]
        assert float(ordem["total"]) == pytest.approx(42.00)
        assert ordem["status"] == "aberta"

        loader.close_order(oid)

        # Status deve ser fechada
        ordem = loader.load_orders()[loader.load_orders()["id"] == oid].iloc[0]
        assert ordem["status"] == "fechada"

        # Estoque deve ter diminuído
        prod = loader.load_products()[loader.load_products()["id"] == pid].iloc[0]
        assert int(prod["current_stock"]) == 44

        # Movimentação de saída deve ter sido criada
        movs = loader.load_movements()
        exit_mov = movs[(movs["product_id"] == pid) & (movs["movement_type"] == "EXIT")]
        assert len(exit_mov) == 1
        assert int(exit_mov.iloc[0]["quantity"]) == 6

    def test_adicionar_remover_adicionar_novamente(self, loader):
        """Fluxo real: adiciona item, remove, adiciona de novo."""
        pid = loader.add_product("Produto", "cat", 1.0, 5.00, 0, 100)
        oid = loader.add_order("Cliente")
        iid = loader.add_order_item(oid, pid, 3, 5.00)
        loader.remove_order_item(iid)
        loader.add_order_item(oid, pid, 5, 5.00)

        ordem = loader.load_orders()[loader.load_orders()["id"] == oid].iloc[0]
        assert float(ordem["total"]) == pytest.approx(25.00)

    def test_alterar_quantidade_multiplas_vezes(self, loader):
        pid = loader.add_product("Produto", "cat", 1.0, 10.00, 0, 100)
        oid = loader.add_order("Cliente")
        iid = loader.add_order_item(oid, pid, 1, 10.00)

        for qtd in [2, 5, 10, 3, 7]:
            loader.update_order_item_quantity(iid, qtd)

        ordem = loader.load_orders()[loader.load_orders()["id"] == oid].iloc[0]
        assert float(ordem["total"]) == pytest.approx(70.00)  # 7 × 10.00

    def test_multiplos_produtos_na_comanda_estoque_todos_decrementados(self, loader):
        p1 = loader.add_product("P1", "cat", 1.0, 5.00, 0, 100)
        p2 = loader.add_product("P2", "cat", 1.0, 8.00, 0, 100)
        p3 = loader.add_product("P3", "cat", 1.0, 3.00, 0, 100)
        oid = loader.add_order("Cliente")
        loader.add_order_item(oid, p1, 4, 5.00)
        loader.add_order_item(oid, p2, 2, 8.00)
        loader.add_order_item(oid, p3, 10, 3.00)
        loader.close_order(oid)

        prods = loader.load_products()
        assert int(prods[prods["id"] == p1].iloc[0]["current_stock"]) == 96
        assert int(prods[prods["id"] == p2].iloc[0]["current_stock"]) == 98
        assert int(prods[prods["id"] == p3].iloc[0]["current_stock"]) == 90

    def test_excluir_comanda_aberta_nao_afeta_estoque(self, loader):
        """Excluir comanda aberta não deve gerar movimentações."""
        pid = loader.add_product("Produto", "cat", 1.0, 5.00, 0, 100)
        oid = loader.add_order("Cliente")
        loader.add_order_item(oid, pid, 10, 5.00)
        loader.delete_order(oid)

        # Estoque não deve ter mudado
        prod = loader.load_products()[loader.load_products()["id"] == pid].iloc[0]
        assert int(prod["current_stock"]) == 100

        # Sem movimentações de saída
        movs = loader.load_movements()
        assert len(movs[movs["product_id"] == pid]) == 0

    def test_fechar_comanda_vazia_nao_gera_movimentacoes(self, loader):
        oid = loader.add_order("Cliente Vazio")
        loader.close_order(oid)
        movs = loader.load_movements()
        assert len(movs) == 0

    def test_duas_comandas_independentes_nao_interferem(self, loader):
        pid = loader.add_product("Produto", "cat", 1.0, 5.00, 0, 100)
        o1 = loader.add_order("João")
        o2 = loader.add_order("Maria")
        loader.add_order_item(o1, pid, 10, 5.00)
        loader.add_order_item(o2, pid, 5, 5.00)

        loader.close_order(o1)

        # o2 não deve ter sido afetada
        ord2 = loader.load_orders()[loader.load_orders()["id"] == o2].iloc[0]
        assert ord2["status"] == "aberta"
        assert float(ord2["total"]) == pytest.approx(25.00)

        # Estoque depois de fechar o1: 100 - 10 = 90
        prod = loader.load_products()[loader.load_products()["id"] == pid].iloc[0]
        assert int(prod["current_stock"]) == 90


# ══════════════════════════════════════════════════════════════════════════════
# INTEGRIDADE DE DADOS
# ══════════════════════════════════════════════════════════════════════════════

class TestIntegridadeDados:

    def test_total_sempre_coerente_com_itens(self, loader):
        """Total da comanda deve ser sempre soma exata dos subtotais dos itens."""
        pid = loader.add_product("Produto", "cat", 1.0, 7.77, 0, 1000)
        oid = loader.add_order("Cliente")

        for i in range(1, 11):
            loader.add_order_item(oid, pid, i, 7.77)
            items = loader.load_order_items()
            itens_comanda = items[items["order_id"] == oid]
            total_calculado = float(itens_comanda["subtotal"].sum())
            total_salvo = float(loader.load_orders()[loader.load_orders()["id"] == oid].iloc[0]["total"])
            assert total_salvo == pytest.approx(total_calculado, rel=1e-6)

    def test_estoque_nao_fica_negativo_com_varias_saidas(self, loader):
        pid = loader.add_product("Produto", "cat", 1.0, 5.00, 0, 10)
        # Primeiro exit válido
        loader.add_movement(pid, "EXIT", 10)
        # Segundo exit deve falhar (estoque zerado)
        mid, err = loader.add_movement(pid, "EXIT", 1)
        assert mid is None
        prod = loader.load_products()[loader.load_products()["id"] == pid].iloc[0]
        assert int(prod["current_stock"]) == 0

    def test_soma_movimentacoes_bate_com_estoque_atual(self, loader):
        """Estoque atual deve ser igual à soma de ENTRYs menos soma de EXITs."""
        pid = loader.add_product("Produto", "cat", 1.0, 5.00, 0, 0)
        ops = [
            ("ENTRY", 100), ("EXIT", 30), ("ENTRY", 50),
            ("EXIT", 20), ("ENTRY", 10), ("EXIT", 5),
        ]
        for tipo, qtd in ops:
            loader.add_movement(pid, tipo, qtd)

        movs = loader.load_movements()
        prod_movs = movs[movs["product_id"] == pid]
        entradas = int(prod_movs[prod_movs["movement_type"] == "ENTRY"]["quantity"].sum())
        saidas = int(prod_movs[prod_movs["movement_type"] == "EXIT"]["quantity"].sum())
        esperado = entradas - saidas

        prod = loader.load_products()[loader.load_products()["id"] == pid].iloc[0]
        assert int(prod["current_stock"]) == esperado

    def test_remover_item_nao_deixa_total_inconsistente(self, loader):
        p1 = loader.add_product("P1", "cat", 1.0, 10.00, 0, 100)
        p2 = loader.add_product("P2", "cat", 1.0, 20.00, 0, 100)
        oid = loader.add_order("Cliente")
        iid1 = loader.add_order_item(oid, p1, 3, 10.00)  # 30.00
        iid2 = loader.add_order_item(oid, p2, 2, 20.00)  # 40.00

        loader.remove_order_item(iid1)

        items = loader.load_order_items()
        itens_comanda = items[items["order_id"] == oid]
        total_esperado = float(itens_comanda["subtotal"].sum())
        total_salvo = float(loader.load_orders()[loader.load_orders()["id"] == oid].iloc[0]["total"])
        assert total_salvo == pytest.approx(total_esperado)
        assert total_salvo == pytest.approx(40.00)

    def test_precos_com_casas_decimais_precisas(self, loader):
        """Evita erros de ponto flutuante em cálculos de preço."""
        pid = loader.add_product("Produto", "cat", 1.0, 1.10, 0, 1000)
        oid = loader.add_order("Cliente")
        loader.add_order_item(oid, pid, 3, 1.10)  # 3 × 1.10 = 3.30
        ordem = loader.load_orders()[loader.load_orders()["id"] == oid].iloc[0]
        assert float(ordem["total"]) == pytest.approx(3.30, abs=0.001)


# ══════════════════════════════════════════════════════════════════════════════
# STRESS
# ══════════════════════════════════════════════════════════════════════════════

class TestStress:

    def test_50_comandas_com_5_itens_cada(self, loader):
        """Simula um dia agitado: 50 comandas abertas com 5 itens cada."""
        produtos = [
            loader.add_product(f"Produto_{i}", "cat", 1.0, float(i + 1), 0, 9999)
            for i in range(5)
        ]

        order_ids = []
        for c in range(50):
            oid = loader.add_order(f"Cliente_{c}")
            order_ids.append(oid)
            for i, pid in enumerate(produtos):
                loader.add_order_item(oid, pid, i + 1, float(i + 1))

        orders_df = loader.load_orders()
        for oid in order_ids:
            row = orders_df[orders_df["id"] == oid].iloc[0]
            assert row["status"] == "aberta"
            assert float(row["total"]) > 0

        assert len(orders_df[orders_df["id"].isin(order_ids)]) == 50

    def test_fechar_20_comandas_estoque_consistente(self, loader):
        """Fecha 20 comandas e verifica que o estoque descontado é exato."""
        pid = loader.add_product("Produto", "cat", 1.0, 5.00, 0, 10000)

        order_ids = []
        for _ in range(20):
            oid = loader.add_order("Cliente")
            loader.add_order_item(oid, pid, 10, 5.00)
            order_ids.append(oid)

        for oid in order_ids:
            loader.close_order(oid)

        prod = loader.load_products()[loader.load_products()["id"] == pid].iloc[0]
        assert int(prod["current_stock"]) == 10000 - (20 * 10)

    def test_200_movimentacoes_no_mesmo_produto(self, loader):
        """200 movimentações alternadas — estoque deve ser exato no final."""
        pid = loader.add_product("Produto", "cat", 1.0, 5.00, 0, 0)
        # 200 entradas de 5 unidades cada = 1000 total
        for _ in range(200):
            loader.add_movement(pid, "ENTRY", 5)
        # 100 saídas de 3 unidades = 300 total
        for _ in range(100):
            loader.add_movement(pid, "EXIT", 3)
        prod = loader.load_products()[loader.load_products()["id"] == pid].iloc[0]
        assert int(prod["current_stock"]) == 700  # 1000 - 300

    def test_banco_com_muitos_produtos_busca_rapida(self, loader):
        """Com 200 produtos no banco, busca por nome deve retornar só o certo."""
        for i in range(200):
            loader.add_product(f"Item Genérico {i:03d}", "cat", 1.0, 2.0, 5, 10)
        loader.add_product("Produto Único Especial", "especial", 1.0, 2.0, 5, 10)

        resultado = loader.search_products(query="Único Especial")
        assert len(resultado) == 1
        assert resultado.iloc[0]["name"] == "Produto Único Especial"

    def test_produto_com_nome_longo(self, loader):
        nome_longo = "A" * 500
        pid = loader.add_product(nome_longo, "cat", 1.0, 2.0, 5, 10)
        df = loader.search_products(query="A" * 10)
        assert any(r["name"] == nome_longo for _, r in df.iterrows())

    def test_multiplas_comandas_mesmo_cliente(self, loader):
        """Mesmo nome de cliente em várias comandas — todas independentes."""
        pid = loader.add_product("Produto", "cat", 1.0, 5.00, 0, 1000)
        ids = []
        for _ in range(10):
            oid = loader.add_order("Eduardo")
            loader.add_order_item(oid, pid, 1, 5.00)
            ids.append(oid)

        orders = loader.load_orders()
        eduardo_orders = orders[orders["customer_name"] == "Eduardo"]
        assert len(eduardo_orders) >= 10

        for oid in ids:
            row = eduardo_orders[eduardo_orders["id"] == oid].iloc[0]
            assert float(row["total"]) == pytest.approx(5.00)

    def test_recarregar_dataloader_preserva_dados(self, tmp_data_dir):
        """Simula reiniciar a aplicação — dados devem persistir no parquet."""
        dl1 = DataLoader(data_dir=tmp_data_dir)
        pid = dl1.add_product("Persistente", "cat", 1.0, 2.0, 5, 10)
        oid = dl1.add_order("Cliente")
        dl1.add_order_item(oid, pid, 3, 2.00)

        # "Reinicia" a aplicação com novo DataLoader apontando pro mesmo dir
        dl2 = DataLoader(data_dir=tmp_data_dir)
        prods = dl2.load_products()
        orders = dl2.load_orders()
        items = dl2.load_order_items()

        assert any(r["name"] == "Persistente" for _, r in prods.iterrows())
        assert len(orders[orders["id"] == oid]) == 1
        assert float(orders[orders["id"] == oid].iloc[0]["total"]) == pytest.approx(6.00)
        assert len(items[items["order_id"] == oid]) == 1

    def test_fechar_comanda_com_muitos_itens_diferentes(self, loader):
        """Fecha comanda com 20 produtos diferentes — todos os estoques decrementados."""
        pids = [
            loader.add_product(f"Produto_{i}", "cat", 1.0, 5.00, 0, 100)
            for i in range(20)
        ]
        oid = loader.add_order("Cliente VIP")
        for pid in pids:
            loader.add_order_item(oid, pid, 2, 5.00)

        loader.close_order(oid)

        prods = loader.load_products()
        for pid in pids:
            row = prods[prods["id"] == pid].iloc[0]
            assert int(row["current_stock"]) == 98  # 100 - 2


# ══════════════════════════════════════════════════════════════════════════════
# STRESS EXTREMO — DIA MUITO MOVIMENTADO (650 PESSOAS)
# Execute com: pytest -m slow -v
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.slow
class TestDiaMuitoMovimentado:
    """
    Simula um dia com 650 clientes fazendo pedidos simultâneos.
    Verifica que o sistema não quebra, não perde dados e não corrompe estoques.
    """

    NUM_PRODUTOS     = 40
    NUM_CLIENTES     = 650
    PEDIDOS_POR_CLI  = 2      # 650 × 2 = 1.300 comandas
    ITENS_MIN        = 3
    ITENS_MAX        = 8
    ESTOQUE_INICIAL  = 99999  # alto o bastante para não esgotar nos testes
    TAXA_FECHAMENTO  = 0.85   # 85% das comandas são fechadas no dia

    def _criar_produtos(self, loader):
        categorias = ["bebida", "bebida", "snack", "snack", "acessorios"]
        return [
            loader.add_product(
                f"Produto_{i:02d}",
                categorias[i % len(categorias)],
                float(i + 1),
                float((i + 1) * 2),
                minimum_stock=10,
                current_stock=self.ESTOQUE_INICIAL,
            )
            for i in range(self.NUM_PRODUTOS)
        ]

    def test_650_clientes_sem_crash(self, loader):
        """Sistema deve processar 650 clientes sem levantar nenhuma exceção."""
        random.seed(42)
        pids = self._criar_produtos(loader)

        for c in range(self.NUM_CLIENTES):
            for _ in range(self.PEDIDOS_POR_CLI):
                oid = loader.add_order(f"Cliente_{c:04d}")
                n_itens = random.randint(self.ITENS_MIN, self.ITENS_MAX)
                escolhidos = random.sample(pids, n_itens)
                for pid in escolhidos:
                    qtd = random.randint(1, 4)
                    preco = float(pids.index(pid) + 1) * 2
                    loader.add_order_item(oid, pid, qtd, preco)

        orders = loader.load_orders()
        total_esperado = self.NUM_CLIENTES * self.PEDIDOS_POR_CLI
        assert len(orders[orders["customer_name"].str.startswith("Cliente_")]) == total_esperado

    def test_1300_comandas_todas_com_total_correto(self, loader):
        """Nenhuma comanda pode ter total zerado se tem itens."""
        random.seed(7)
        pids = self._criar_produtos(loader)

        order_ids = []
        for c in range(self.NUM_CLIENTES):
            for _ in range(self.PEDIDOS_POR_CLI):
                oid = loader.add_order(f"Cliente_{c:04d}")
                order_ids.append(oid)
                n_itens = random.randint(self.ITENS_MIN, self.ITENS_MAX)
                for pid in random.sample(pids, n_itens):
                    qtd = random.randint(1, 5)
                    preco = float(pids.index(pid) + 1) * 2
                    loader.add_order_item(oid, pid, qtd, preco)

        orders = loader.load_orders()
        for oid in order_ids:
            total = float(orders[orders["id"] == oid].iloc[0]["total"])
            assert total > 0, f"Comanda {oid} tem total zerado com itens"

    def test_fechamento_em_massa_nao_corrompe_estoque(self, loader):
        """
        85% das 1.300 comandas fechadas — estoques nunca negativos,
        total de saídas deve bater com a diferença de estoque.
        """
        random.seed(13)
        pids = self._criar_produtos(loader)
        estoque_antes = {pid: self.ESTOQUE_INICIAL for pid in pids}

        order_ids = []
        for c in range(self.NUM_CLIENTES):
            for _ in range(self.PEDIDOS_POR_CLI):
                oid = loader.add_order(f"Cliente_{c:04d}")
                order_ids.append(oid)
                n_itens = random.randint(self.ITENS_MIN, self.ITENS_MAX)
                for pid in random.sample(pids, n_itens):
                    qtd = random.randint(1, 3)
                    loader.add_order_item(oid, pid, qtd, 5.0)

        # Fechar 85% das comandas
        n_fechar = int(len(order_ids) * self.TAXA_FECHAMENTO)
        a_fechar = random.sample(order_ids, n_fechar)
        for oid in a_fechar:
            loader.close_order(oid)

        # ── Verificações de integridade ──────────────────────────────────────
        orders = loader.load_orders()
        fechadas = orders[orders["status"] == "fechada"]
        abertas  = orders[orders["status"] == "aberta"]

        assert len(fechadas) == n_fechar
        assert len(abertas)  == len(order_ids) - n_fechar

        # Estoque nunca negativo
        prods = loader.load_products()
        for pid in pids:
            stock = int(prods[prods["id"] == pid].iloc[0]["current_stock"])
            assert stock >= 0, f"Produto {pid} ficou com estoque negativo: {stock}"

        # Consistência: saídas registradas batem com queda de estoque
        movs = loader.load_movements()
        for pid in pids:
            saidas = movs[(movs["product_id"] == pid) & (movs["movement_type"] == "EXIT")]
            total_saida = int(saidas["quantity"].sum()) if len(saidas) > 0 else 0
            stock_atual = int(prods[prods["id"] == pid].iloc[0]["current_stock"])
            assert estoque_antes[pid] - total_saida == stock_atual, (
                f"Produto {pid}: esperado {estoque_antes[pid] - total_saida}, "
                f"obtido {stock_atual}"
            )

    def test_totais_das_fechadas_batem_com_soma_dos_itens(self, loader):
        """Para toda comanda fechada, total == soma exata dos subtotais."""
        random.seed(99)
        pids = self._criar_produtos(loader)

        order_ids = []
        for c in range(self.NUM_CLIENTES):
            for _ in range(self.PEDIDOS_POR_CLI):
                oid = loader.add_order(f"C{c}")
                order_ids.append(oid)
                for pid in random.sample(pids, random.randint(2, 6)):
                    preco = float(random.randint(1, 20))
                    loader.add_order_item(oid, pid, random.randint(1, 5), preco)

        # Fechar todas
        for oid in order_ids:
            loader.close_order(oid)

        orders = loader.load_orders()
        items  = loader.load_order_items()

        for oid in order_ids:
            total_salvo = float(orders[orders["id"] == oid].iloc[0]["total"])
            itens_comanda = items[items["order_id"] == oid]
            total_calculado = float(itens_comanda["subtotal"].sum())
            assert total_salvo == pytest.approx(total_calculado, rel=1e-5), (
                f"Comanda {oid}: total salvo={total_salvo} != calculado={total_calculado}"
            )

    def test_multiplos_produtos_populares_com_alta_demanda(self, loader):
        """
        5 produtos 'hit' com 1.000 unidades — todos pedidos por quase todo cliente.
        Verifica que nenhum vai negativo e as quantidades batem.
        """
        random.seed(55)
        # 5 produtos hit com estoque alto
        hits = [loader.add_product(f"Hit_{i}", "bebida", 2.0, 5.0, 0, 1000) for i in range(5)]
        # 35 produtos normais
        normais = [loader.add_product(f"Normal_{i}", "snack", 1.0, 3.0, 0, self.ESTOQUE_INICIAL) for i in range(35)]
        todos = hits + normais

        order_ids = []
        for c in range(self.NUM_CLIENTES):
            oid = loader.add_order(f"C{c}")
            order_ids.append(oid)
            # Sempre adiciona pelo menos 1 hit
            loader.add_order_item(oid, random.choice(hits), 1, 5.0)
            # Mais itens normais
            for pid in random.sample(normais, random.randint(2, 5)):
                loader.add_order_item(oid, pid, random.randint(1, 2), 3.0)

        # Fecha todos
        for oid in order_ids:
            loader.close_order(oid)

        prods = loader.load_products()
        for pid in todos:
            stock = int(prods[prods["id"] == pid].iloc[0]["current_stock"])
            assert stock >= 0, f"Produto {pid} com estoque negativo: {stock}"

    def test_sistema_suporta_reaberturas_e_cancelamentos(self, loader):
        """
        Simula clientes que mudam de ideia:
        - Abre comanda → adiciona itens → exclui (cancelamento)
        - Abre de novo → adiciona → fecha
        Estoque final deve ser consistente.
        """
        random.seed(21)
        pids = self._criar_produtos(loader)

        canceladas = 0
        fechadas_ids = []

        for c in range(300):  # 300 clientes com possibilidade de cancelamento
            oid = loader.add_order(f"Cliente_{c}")
            for pid in random.sample(pids, random.randint(2, 5)):
                loader.add_order_item(oid, pid, random.randint(1, 3), 5.0)

            if random.random() < 0.2:  # 20% cancela
                loader.delete_order(oid)
                canceladas += 1
                # Reabre nova comanda
                oid2 = loader.add_order(f"Cliente_{c}_retry")
                for pid in random.sample(pids, 2):
                    loader.add_order_item(oid2, pid, 1, 5.0)
                loader.close_order(oid2)
                fechadas_ids.append(oid2)
            else:
                loader.close_order(oid)
                fechadas_ids.append(oid)

        # Estoque nunca negativo
        prods = loader.load_products()
        for pid in pids:
            stock = int(prods[prods["id"] == pid].iloc[0]["current_stock"])
            assert stock >= 0, f"Produto {pid} negativo após cancelamentos: {stock}"

        # Todas as comandas fechadas devem ter status=fechada
        orders = loader.load_orders()
        for oid in fechadas_ids:
            row = orders[orders["id"] == oid]
            if len(row) > 0:
                assert row.iloc[0]["status"] == "fechada"

    def test_relatorio_diario_com_650_clientes(self, loader, qt_app):
        """ReportsController deve agregar corretamente um dia inteiro de 650 clientes."""
        from desktop.controllers.reports_controller import ReportsController
        random.seed(77)
        pids = self._criar_produtos(loader)

        order_ids = []
        for c in range(self.NUM_CLIENTES):
            oid = loader.add_order(f"C{c}")
            order_ids.append(oid)
            for pid in random.sample(pids, random.randint(2, 5)):
                preco = float(pids.index(pid) + 1) * 2
                loader.add_order_item(oid, pid, random.randint(1, 3), preco)
            loader.close_order(oid)

        ctrl = ReportsController()
        ctrl.data_loader = loader
        relatorio = ctrl.get_daily_report()

        assert relatorio["total_orders"] == self.NUM_CLIENTES
        assert relatorio["total_revenue"] > 0
        assert len(relatorio["by_category"]) > 0
        assert len(relatorio["by_product"]) > 0
        # Os 5 mais vendidos devem aparecer
        assert len(relatorio["by_product"]) <= self.NUM_PRODUTOS
        # Receita total deve bater com soma das comandas
        orders = loader.load_orders()
        receita_esperada = float(orders[orders["status"] == "fechada"]["total"].sum())
        assert relatorio["total_revenue"] == pytest.approx(receita_esperada, rel=1e-4)
