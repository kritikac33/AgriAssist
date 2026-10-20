import { useEffect, useState } from 'react';
import { transactionsAPI, type Transaction } from '../api/transactions';
import { useAuth } from '../contexts/AuthContext';
import { formatError } from '../utils/errorFormatter';
export default function FarmerOrders() {
  const { user } = useAuth(); const [orders, setOrders] = useState<Transaction[]>([]); const [error, setError] = useState('');
  const load = () => transactionsAPI.getTransactions().then((rows) => setOrders(rows.filter((row) => row.seller_id === user?.id))).catch((e) => setError(formatError(e)));
  useEffect(() => { void load(); }, [user?.id]);
  const next = (o: Transaction) => o.fulfillment_status === 'confirmed' ? (o.delivery_method === 'pickup' ? 'ready_for_pickup' : 'processing') : o.fulfillment_status === 'processing' ? 'shipped' : ['shipped','ready_for_pickup'].includes(o.fulfillment_status || '') ? 'delivered' : null;
  const update = async (o: Transaction) => { const status = next(o); if (!status) return; try { await transactionsAPI.updateFulfillment(o.id, status); await load(); } catch (e) { setError(formatError(e)); } };
  return <div className="space-y-4"><h1 className="text-3xl font-bold">Buyer orders</h1><p className="text-gray-600">Update fulfilment as each paid order moves through your workflow.</p>{error && <p role="alert" className="rounded bg-red-50 p-3 text-red-800">{error}</p>}{orders.map((o) => <article key={o.id} className="flex flex-wrap items-center justify-between gap-3 rounded-lg border bg-white p-4"><div><b>Order AA-{String(o.id).padStart(6,'0')} · {o.crop_name_snapshot || 'Crop'}</b><p className="text-sm">{o.quantity_quintals} quintals · ₹{Number(o.total_amount).toFixed(2)} · {o.delivery_method || 'pickup'}</p><p className="text-sm capitalize">Payment: {o.status} · Fulfilment: {(o.fulfillment_status || o.status).replaceAll('_',' ')}</p>{o.cancellation_requested_at && <p className="text-sm text-amber-800">Buyer cancellation requested: {o.cancellation_reason}</p>}</div>{next(o) && o.status !== 'initiated' && <button onClick={() => void update(o)} className="rounded bg-primary-600 px-3 py-2 text-white">Mark {next(o)?.replaceAll('_',' ')}</button>}</article>)}{!orders.length && <p className="rounded border bg-white p-6 text-gray-600">No orders found.</p>}</div>;
}
