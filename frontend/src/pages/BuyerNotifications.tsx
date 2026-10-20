import { useEffect, useState } from 'react';
import { buyerAPI } from '../api/buyer';
import { formatError } from '../utils/errorFormatter';
export default function BuyerNotifications() {
  const [rows, setRows] = useState<any[]>([]); const [error, setError] = useState('');
  const load = () => buyerAPI.notifications().then(setRows).catch((e) => setError(formatError(e)));
  useEffect(() => { void load(); }, []);
  const read = async (id: number) => { try { await buyerAPI.markNotificationRead(id); await load(); } catch (e) { setError(formatError(e)); } };
  return <div className="space-y-4"><h1 className="text-3xl font-bold">Notifications</h1>{error && <p role="alert" className="rounded bg-red-50 p-3 text-red-800">{error}</p>}{!rows.length && <p className="rounded border bg-white p-6 text-gray-600">No notifications yet.</p>}{rows.map((n) => <article key={n.id} className={`rounded-lg border bg-white p-4 ${n.is_read ? 'opacity-70' : 'border-primary-300'}`}><div className="flex justify-between gap-3"><div><h2 className="font-semibold">{n.subject}</h2><p>{n.content}</p><time className="text-xs text-gray-500">{new Date(n.created_at || n.sent_at).toLocaleString()}</time></div>{!n.is_read && <button onClick={() => void read(n.id)} className="self-start rounded border px-3 py-1">Mark read</button>}</div></article>)}</div>;
}
