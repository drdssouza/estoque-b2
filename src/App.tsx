import { Routes, Route, Navigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import Products from './pages/Products';
import Orders from './pages/Orders';
import OrderDetail from './pages/OrderDetail';
import Customers from './pages/Customers';
import Movements from './pages/Movements';
import Reports from './pages/Reports';
import Settings from './pages/Settings';
import { initDb } from './lib/db';
import { Package } from 'lucide-react';

export default function App() {
  const [dbReady, setDbReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    initDb()
      .then(() => setDbReady(true))
      .catch((e) => setError(String(e)));
  }, []);

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen bg-bg">
        <div className="text-center max-w-md px-6">
          <div className="w-14 h-14 rounded-2xl bg-danger-subtle border border-danger/20 flex items-center justify-center mx-auto mb-4">
            <Package size={24} className="text-danger" />
          </div>
          <p className="text-base font-semibold text-white mb-2">
            Erro ao inicializar banco de dados
          </p>
          <p className="text-sm text-muted">{error}</p>
        </div>
      </div>
    );
  }

  if (!dbReady) {
    return (
      <div className="flex items-center justify-center h-screen bg-bg">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-muted">Inicializando Controle B2...</p>
        </div>
      </div>
    );
  }

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/products" element={<Products />} />
        <Route path="/orders" element={<Orders />} />
        <Route path="/orders/:id" element={<OrderDetail />} />
        <Route path="/customers" element={<Customers />} />
        <Route path="/movements" element={<Movements />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Layout>
  );
}
