from PySide6.QtCore import QObject, Signal
from backend.utils.data_loader import DataLoader
from datetime import datetime, timedelta
import pandas as pd


class ReportsController(QObject):
    def __init__(self):
        super().__init__()
        self.data_loader = DataLoader()

    def get_daily_report(self, date=None):
        """Retorna dados do relatório para uma data específica (padrão: hoje)."""
        if date is None:
            date = datetime.now().date()

        orders_df = self.data_loader.load_orders()
        items_df = self.data_loader.load_order_items()
        products_df = self.data_loader.load_products()

        # Converter created_at para datetime
        if len(orders_df) > 0:
            orders_df['created_at'] = pd.to_datetime(orders_df['created_at'])

        # Filtrar comandas fechadas do dia
        day_start = pd.Timestamp(date)
        day_end = day_start + pd.Timedelta(days=1)

        closed_orders = orders_df[
            (orders_df['status'] == 'fechada') &
            (orders_df['created_at'] >= day_start) &
            (orders_df['created_at'] < day_end)
        ] if len(orders_df) > 0 else pd.DataFrame()

        # Se não há comandas fechadas, retornar zeroes
        if len(closed_orders) == 0:
            return {
                'date': date.strftime('%d/%m/%Y'),
                'total_orders': 0,
                'total_revenue': 0.0,
                'by_category': {},
                'by_product': [],
                'order_list': []
            }

        closed_order_ids = closed_orders['id'].tolist()

        # Filtrar itens das comandas fechadas do dia
        day_items = items_df[items_df['order_id'].isin(closed_order_ids)] if len(items_df) > 0 else pd.DataFrame()

        # Mapear products
        products_map = {}
        categories_map = {}
        for _, p in products_df.iterrows():
            products_map[p['id']] = p['name']
            categories_map[p['id']] = p['category']

        # ── Totais por categoria ──
        by_category = {}
        if len(day_items) > 0:
            for _, item in day_items.iterrows():
                cat = categories_map.get(item['product_id'], 'desconhecido')
                if cat not in by_category:
                    by_category[cat] = {'quantity': 0, 'revenue': 0.0}
                by_category[cat]['quantity'] += int(item['quantity'])
                by_category[cat]['revenue'] += float(item['subtotal'])

        # ── Totais por produto ──
        by_product = []
        if len(day_items) > 0:
            grouped = day_items.groupby('product_id').agg(
                total_qty=('quantity', 'sum'),
                total_rev=('subtotal', 'sum')
            ).reset_index()
            for _, row in grouped.iterrows():
                by_product.append({
                    'product_id': int(row['product_id']),
                    'product_name': products_map.get(row['product_id'], 'Desconhecido'),
                    'category': categories_map.get(row['product_id'], 'desconhecido'),
                    'quantity': int(row['total_qty']),
                    'revenue': float(row['total_rev'])
                })
            by_product.sort(key=lambda x: x['revenue'], reverse=True)

        # ── Lista de comandas do dia ──
        order_list = []
        for _, order in closed_orders.iterrows():
            order_list.append({
                'id': int(order['id']),
                'customer_name': order['customer_name'],
                'total': float(order['total']),
                'created_at': order['created_at'].strftime('%H:%M')
            })

        total_revenue = float(closed_orders['total'].sum())

        return {
            'date': date.strftime('%d/%m/%Y'),
            'total_orders': len(closed_orders),
            'total_revenue': total_revenue,
            'by_category': by_category,
            'by_product': by_product,
            'order_list': order_list
        }

    def get_available_dates(self):
        """Retorna lista de datas que têm comandas fechadas."""
        orders_df = self.data_loader.load_orders()
        if len(orders_df) == 0:
            return []
        orders_df['created_at'] = pd.to_datetime(orders_df['created_at'])
        closed = orders_df[orders_df['status'] == 'fechada']
        if len(closed) == 0:
            return []
        dates = closed['created_at'].dt.date.unique()
        return sorted(dates, reverse=True)

    def get_available_months(self):
        """Retorna lista de (year, month) com comandas fechadas, ordenada desc."""
        orders_df = self.data_loader.load_orders()
        if len(orders_df) == 0:
            return []
        orders_df['created_at'] = pd.to_datetime(orders_df['created_at'])
        closed = orders_df[orders_df['status'] == 'fechada']
        if len(closed) == 0:
            return []
        periods = closed['created_at'].dt.to_period('M').unique()
        return sorted([(p.year, p.month) for p in periods], reverse=True)

    def get_monthly_tops(self, year, month):
        """Retorna produtos e clientes agrupados do mês (sem ordenação — a UI ordena)."""
        orders_df = self.data_loader.load_orders()
        items_df  = self.data_loader.load_order_items()
        products_df = self.data_loader.load_products()

        empty = {'top_products': [], 'top_customers': []}

        if len(orders_df) == 0:
            return empty

        orders_df['created_at'] = pd.to_datetime(orders_df['created_at'])

        closed = orders_df[
            (orders_df['status'] == 'fechada') &
            (orders_df['created_at'].dt.year  == year) &
            (orders_df['created_at'].dt.month == month)
        ]

        if len(closed) == 0:
            return empty

        closed_ids = closed['id'].tolist()
        month_items = items_df[items_df['order_id'].isin(closed_ids)] if len(items_df) > 0 else pd.DataFrame()

        products_map = {p['id']: p['name'] for _, p in products_df.iterrows()}

        # ── Top produtos por receita ──
        top_products = []
        if len(month_items) > 0:
            grouped = (
                month_items.groupby('product_id')
                .agg(total_qty=('quantity', 'sum'), total_rev=('subtotal', 'sum'))
                .reset_index()
            )
            for _, row in grouped.iterrows():
                top_products.append({
                    'product_name': products_map.get(row['product_id'], 'Desconhecido'),
                    'quantity':     int(row['total_qty']),
                    'revenue':      float(row['total_rev']),
                })

        # ── Top clientes por total gasto ──
        top_customers = (
            closed.groupby('customer_name')
            .agg(total_spent=('total', 'sum'), total_orders=('id', 'count'))
            .reset_index()
        )
        top_customers_list = [
            {
                'customer_name': row['customer_name'],
                'total_orders':  int(row['total_orders']),
                'total_spent':   float(row['total_spent']),
            }
            for _, row in top_customers.iterrows()
        ]

        return {'top_products': top_products, 'top_customers': top_customers_list}