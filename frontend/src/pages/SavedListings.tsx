import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { buyerAPI } from '../api/buyer';
import { formatError } from '../utils/errorFormatter';

export default function SavedListings() {
  const [saved, setSaved] = useState<any[]>([]);
  const [error, setError] = useState('');
  const load = async () => setSaved(await buyerAPI.saved());
  useEffect(() => { load().catch((e) => setError(formatError(e))); }, []);
  const remove = async (id: number) => { try { await buyerAPI.unsave(id); await load(); } catch (e) { setError(formatError(e)); } };
  return <div className="space-y-5"><div><h1 className="text-3xl font-bold">Saved Listings</h1><p className="text-gray-600">Your saved produce listings.</p></div>{error && <p role="alert" className="rounded bg-red-50 p-3 text-red-800">{error}</p>}{!saved.length ? <div className="rounded-lg border bg-white p-8 text-center text-gray-600">No saved listings yet. <Link className="text-primary-700 underline" to="/marketplace">Browse crops</Link>.</div> : <div className="grid gap-4 md:grid-cols-2">{saved.map((row) => <article key={row.id} className="rounded-lg border bg-white p-5"><h2 className="text-lg font-semibold">{row.listing?.crop_name || 'Listing unavailable'}</h2><p className="text-sm text-gray-600">{row.listing?.seller_name} · {row.listing?.location || 'Location not provided'}</p><p className="my-2">{row.available ? `₹${row.listing.price_per_quintal}/quintal · ${row.listing.quantity_quintals} quintals available` : 'This listing is no longer available.'}</p><div className="flex gap-2"><Link to="/marketplace" className="rounded bg-primary-600 px-3 py-2 text-white">View marketplace</Link><button onClick={() => void remove(row.listing.id)} className="rounded border px-3 py-2">Remove saved</button></div></article>)}</div>}</div>;
}
