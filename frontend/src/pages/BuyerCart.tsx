import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { buyerAPI, type BuyerAddress, type CartItem } from '../api/buyer';
import { transactionsAPI } from '../api/transactions';
import { useAuth } from '../contexts/AuthContext';
import { formatError } from '../utils/errorFormatter';

declare global { interface Window { Razorpay: any } }

export default function BuyerCart() {
  const { user } = useAuth();
  const [items, setItems] = useState<CartItem[]>([]);
  const [subtotal, setSubtotal] = useState('0');
  const [error, setError] = useState('');
  const [busyId, setBusyId] = useState<number | null>(null);
  const [addresses, setAddresses] = useState<BuyerAddress[]>([]);
  const [deliveryMethod, setDeliveryMethod] = useState<'pickup' | 'delivery'>('pickup');
  const [addressId, setAddressId] = useState<number | ''>('');

  const load = async () => {
    const cart = await buyerAPI.cart();
    setItems(cart.items);
    setSubtotal(cart.subtotal);
  };
  useEffect(() => { load().catch((e) => setError(formatError(e))); buyerAPI.addresses().then((rows) => { setAddresses(rows); const preferred = rows.find((a) => a.is_default) || rows[0]; if (preferred) setAddressId(preferred.id); }).catch((e) => setError(formatError(e))); }, []);

  const setQuantity = async (item: CartItem, quantity: number) => {
    if (!Number.isFinite(quantity) || quantity <= 0) return;
    try { await buyerAPI.updateCart(item.id, quantity); await load(); }
    catch (e) { setError(formatError(e)); }
  };

  const payItem = async (item: CartItem) => {
    if (!item.listing) return;
    if (!import.meta.env.VITE_RAZORPAY_KEY_ID) { setError('Online payment is not configured. Configure Razorpay test credentials to pay online.'); return; }
    setBusyId(item.id); setError('');
    try {
      if (deliveryMethod === 'delivery' && !addressId) throw new Error('Add or select a delivery address first.');
      const transaction = await transactionsAPI.createTransaction(item.listing_id, Number(item.quantity_quintals), { delivery_method: deliveryMethod, delivery_address_id: deliveryMethod === 'delivery' ? Number(addressId) : undefined });
      if (!transaction.razorpay_order_id || !transaction.razorpay_key_id) throw new Error('Payment service is unavailable.');
      const open = () => {
        const checkout = new window.Razorpay({
          key: transaction.razorpay_key_id,
          amount: Math.round(Number(transaction.total_amount) * 100),
          currency: 'INR', name: 'AgriAssist', description: `Purchase ${item.listing?.crop_name}`,
          order_id: transaction.razorpay_order_id,
          prefill: { name: user?.full_name, email: user?.email }, theme: { color: '#166534' },
          handler: async (payment: any) => {
            try {
              const verified = await transactionsAPI.verifyTransaction(transaction.id, payment);
              if (verified.status !== 'confirmed') throw new Error('Payment was not confirmed by the server.');
              await buyerAPI.removeCartItem(item.id); await load(); setError('Payment verified and order recorded.');
            } catch (e) { setError(formatError(e)); }
            finally { setBusyId(null); }
          },
        });
        checkout.on('payment.failed', () => { void transactionsAPI.cancelUnpaid(transaction.id).catch(() => undefined); setError('Payment failed. The unpaid order was cancelled and its quantity released.'); setBusyId(null); });
        checkout.open();
      };
      if (window.Razorpay) open();
      else {
        const script = document.createElement('script'); script.src = 'https://checkout.razorpay.com/v1/checkout.js'; script.async = true;
        script.onload = open; script.onerror = () => { void transactionsAPI.cancelUnpaid(transaction.id).catch(() => undefined); setError('Could not load Razorpay Checkout. The unpaid order was cancelled.'); setBusyId(null); };
        document.body.appendChild(script);
      }
    } catch (e) { setError(formatError(e)); setBusyId(null); }
  };

  const grouped = items.reduce<Record<string, CartItem[]>>((groups, item) => {
    const seller = item.listing?.seller_name || 'Farmer account unavailable';
    (groups[seller] ||= []).push(item); return groups;
  }, {});

  return <div className="space-y-6">
    <div><h1 className="text-3xl font-bold text-gray-900">Shopping Cart</h1><p className="mt-1 text-gray-600">Items are grouped by farmer. Each listing is paid for as a separate order.</p></div>
    {error && <div role="status" className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-amber-900">{error}</div>}
    {!items.length ? <div className="rounded-lg border bg-white p-10 text-center"><p className="mb-4 text-gray-600">Your cart is empty.</p><Link to="/marketplace" className="rounded-lg bg-primary-600 px-4 py-2 text-white">Browse crops</Link></div> : <>
      <section className="grid gap-3 rounded-lg border bg-white p-4 sm:grid-cols-2"><label>Fulfilment method<select value={deliveryMethod} onChange={(e) => setDeliveryMethod(e.target.value as 'pickup' | 'delivery')} className="mt-1 block w-full rounded border p-2"><option value="pickup">Pick up from farmer</option><option value="delivery">Delivery</option></select></label>{deliveryMethod === 'delivery' && <label>Delivery address<select value={addressId} onChange={(e) => setAddressId(e.target.value ? Number(e.target.value) : '')} className="mt-1 block w-full rounded border p-2"><option value="">Select address</option>{addresses.map((a) => <option key={a.id} value={a.id}>{a.label}: {a.address_line1}, {a.city}</option>)}</select>{!addresses.length && <Link className="text-sm text-primary-700 underline" to="/addresses">Add a delivery address</Link>}</label>}</section>
      {Object.entries(grouped).map(([seller, rows]) => <section key={seller} className="rounded-lg border bg-white p-5"><h2 className="mb-4 text-lg font-semibold">From {seller}</h2><div className="space-y-4">{rows.map((item) => <div key={item.id} className="grid gap-3 border-b pb-4 sm:grid-cols-[1fr_auto]">
        <div><h3 className="font-semibold">{item.listing?.crop_name || 'Listing unavailable'}</h3><p className="text-sm text-gray-600">₹{item.listing?.price_per_quintal ?? '—'} / quintal · {item.listing?.location || 'Location not provided'}</p><p className="text-sm">Available: {item.listing?.quantity_quintals ?? '—'} quintals · Subtotal: ₹{Number(item.subtotal).toFixed(2)}</p>{!item.available && <p className="text-sm text-red-700">This listing is not currently available for purchase.</p>}</div>
        <div className="flex flex-wrap items-center gap-2"><label className="text-sm">Quantity<input aria-label={`Quantity for ${item.listing?.crop_name}`} type="number" min="0.01" max={Number(item.listing?.quantity_quintals || 0)} step="0.01" value={item.quantity_quintals} onChange={(e) => void setQuantity(item, Number(e.target.value))} className="ml-2 w-24 rounded border px-2 py-1" /></label><button onClick={() => buyerAPI.removeCartItem(item.id).then(load).catch((e) => setError(formatError(e)))} className="rounded border px-3 py-2">Remove</button><button disabled={!item.available || busyId === item.id} onClick={() => void payItem(item)} className="rounded bg-primary-600 px-3 py-2 text-white disabled:opacity-50">{busyId === item.id ? 'Processing…' : 'Checkout this item'}</button></div>
      </div>)}</div></section>)}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border bg-white p-5"><div><p className="text-sm text-gray-600">Cart subtotal (before any separately configured fees)</p><p className="text-2xl font-bold">₹{Number(subtotal).toFixed(2)}</p></div><div className="flex gap-2"><button onClick={() => window.confirm('Remove all items from your cart?') && buyerAPI.clearCart().then(load).catch((e) => setError(formatError(e)))} className="rounded border px-4 py-2">Clear cart</button><Link to="/marketplace" className="rounded bg-primary-600 px-4 py-2 text-white">Continue shopping</Link></div></div>
    </>}
  </div>;
}
