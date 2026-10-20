import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { marketplaceAPI, type Listing, type Message } from '../api/marketplace';
import { transactionsAPI, type Transaction } from '../api/transactions';
import { useAuth } from '../contexts/AuthContext';
import { formatError } from '../utils/errorFormatter';
import { buyerAPI } from '../api/buyer';

declare global {
  interface Window {
    Razorpay: any;
  }
}

export default function Marketplace() {
  const [searchParams] = useSearchParams();
  const { user } = useAuth();
  const [listings, setListings] = useState<Listing[]>([]);
  const [selectedListing, setSelectedListing] = useState<Listing | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [messageError, setMessageError] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [filter, setFilter] = useState({ crop: searchParams.get('crop') || '', min_price: '', max_price: '', min_quantity: '', seller: '', sort_by: 'newest' });
  const [purchaseQuantity, setPurchaseQuantity] = useState(1);
  const [offset, setOffset] = useState(0);

  const [newListing, setNewListing] = useState({
    crop_name: '',
    quantity_quintals: 0,
    price_per_quintal: 0,
    unit: 'quintal',
    location: '',
    latitude: 18.52,
    longitude: 73.85,
  });

  useEffect(() => {
    fetchListings();
  }, []);

  const fetchListings = async (append = false) => {
    try {
      const params: any = {};
      if (filter.crop) params.crop = filter.crop;
      if (filter.min_price) params.min_price = Number(filter.min_price);
      if (filter.max_price) params.max_price = Number(filter.max_price);
      if (filter.min_quantity) params.min_quantity = Number(filter.min_quantity);
      if (filter.seller) params.seller = filter.seller;
      params.sort_by = filter.sort_by;
      params.limit = 24;
      params.offset = append ? offset + 24 : 0;
      const data = await marketplaceAPI.getListings(params);
      setListings((current) => append ? [...current, ...data] : data);
      setOffset(append ? offset + 24 : 0);
    } catch (err: any) {
      setError(formatError(err) || 'Failed to fetch listings');
    }
  };



  const handleCreateListing = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await marketplaceAPI.createListing({
        ...newListing,
        quantity_quintals: String(newListing.quantity_quintals),
        price_per_quintal: String(newListing.price_per_quintal),
        latitude: String(newListing.latitude),
        longitude: String(newListing.longitude),
      });
      setNewListing({
        crop_name: '',
        quantity_quintals: 0,
        price_per_quintal: 0,
        unit: 'quintal',
        location: '',
        latitude: 18.52,
        longitude: 73.85,
      });
      await fetchListings();
    } catch (err: any) {
      setError(formatError(err) || 'Failed to create listing');
    } finally {
      setLoading(false);
    }
  };

  const handleViewListing = async (listing: Listing) => {
    setSelectedListing(listing);
    setPurchaseQuantity(1);
    setMessages([]);
    setMessagesLoading(true);
    setMessageError('');
    try {
      const msgs = await marketplaceAPI.getMessages(listing.id);
      setMessages(msgs);
    } catch (err: any) {
      setMessageError(formatError(err) || 'Could not load this conversation. Please try again.');
    } finally {
      setMessagesLoading(false);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedListing || !newMessage.trim()) return;

    try {
      await marketplaceAPI.sendMessage(selectedListing.id, newMessage);
      setNewMessage('');
      setMessageError('');
      const msgs = await marketplaceAPI.getMessages(selectedListing.id);
      setMessages(msgs);
    } catch (err: any) {
      setMessageError(formatError(err) || 'Failed to send message');
    }
  };

  const handleBuyNow = async (listing: Listing) => {
    if (!user || user.role !== 'buyer') {
      setError('Only buyers can purchase');
      return;
    }

    if (!import.meta.env.VITE_RAZORPAY_KEY_ID) {
      setError('Online payment is not configured. Please use the listing message thread to contact the farmer.');
      return;
    }

    setLoading(true);
    setError('');

    let createdTransactionId: number | null = null;
    try {
      const transaction = await transactionsAPI.createTransaction(listing.id, purchaseQuantity);
      createdTransactionId = transaction.id;
      if (!transaction.razorpay_order_id || transaction.razorpay_order_id.startsWith('order_mock_')) {
        setError('Payment service is in demo mode. No payment was started; contact the farmer in this listing thread.');
        setLoading(false);
        return;
      }

      if (!window.Razorpay) {
        const script = document.createElement('script');
        script.src = 'https://checkout.razorpay.com/v1/checkout.js';
        script.async = true;
        script.onload = () => openRazorpay(transaction, listing);
        script.onerror = () => { void transactionsAPI.cancelUnpaid(transaction.id).catch(() => undefined); setError('Could not load payment checkout. The unpaid order was cancelled.'); setLoading(false); };
        document.body.appendChild(script);
      } else {
        openRazorpay(transaction, listing);
      }
    } catch (err: any) {
      if (createdTransactionId !== null) await transactionsAPI.cancelUnpaid(createdTransactionId).catch(() => undefined);
      setError(formatError(err) || 'Failed to initiate transaction');
      setLoading(false);
    }
  };

  const handleAddToCart = async (listing: Listing, quantity = 1) => {
    try {
      await buyerAPI.addToCart(listing.id, quantity);
      setError('');
      setSuccess(`${quantity} quintal(s) of ${listing.crop_name} added to your cart.`);
    } catch (err: any) {
      setError(formatError(err) || 'Could not add this listing to cart');
    }
  };

  const handleSaveListing = async (listing: Listing) => {
    try {
      await buyerAPI.save(listing.id);
      setError('');
      setSuccess(`${listing.crop_name} saved to your listings.`);
    } catch (err: any) {
      setError(formatError(err) || 'Could not save this listing');
    }
  };

  const openRazorpay = (transaction: Transaction, listing: Listing) => {
    const options = {
      key: transaction.razorpay_key_id,
      amount: Number(transaction.total_amount) * 100,
      currency: 'INR',
      name: 'AgriAssist',
      description: `Purchase ${listing.crop_name}`,
      order_id: transaction.razorpay_order_id,
      handler: async (payment: any) => {
        try {
          const verified = await transactionsAPI.verifyTransaction(transaction.id, {
            razorpay_order_id: payment.razorpay_order_id,
            razorpay_payment_id: payment.razorpay_payment_id,
            razorpay_signature: payment.razorpay_signature,
          });
          if (verified.status === 'confirmed') {
            setSuccess('Payment confirmed by the server.');
            await fetchListings();
          } else {
            setError(`Payment status: ${verified.status}`);
          }
        } catch (err: any) {
          setError(formatError(err) || 'Payment verification failed; confirmation was not received from the server.');
        }
        setLoading(false);
      },
      prefill: {
        name: user?.full_name,
        email: user?.email,
      },
      theme: {
        color: '#3399cc',
      },
    };

    const rzp = new window.Razorpay(options);
    rzp.open();
    rzp.on('payment.failed', () => {
      void transactionsAPI.cancelUnpaid(transaction.id).catch(() => undefined);
      setError('Payment failed. The unpaid order was cancelled and its quantity released.');
      setLoading(false);
    });
  };

  return (
    <>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <span className="text-4xl" aria-hidden="true">🛒</span>
          Marketplace
        </h1>
        <p className="text-gray-600 mt-1">Browse crops, buy with Razorpay, or list your produce</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}
      {success && <div role="status" className="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-lg mb-6">{success}</div>}

      {user?.role === 'farmer' && (
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Create Listing</h2>
          <form onSubmit={handleCreateListing} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Crop Name</label>
                <input
                  type="text"
                  value={newListing.crop_name}
                  onChange={(e) => setNewListing({ ...newListing, crop_name: e.target.value })}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Quantity (quintals)</label>
                <input
                  type="number"
                  value={newListing.quantity_quintals}
                  onChange={(e) => setNewListing({ ...newListing, quantity_quintals: Number(e.target.value) })}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Price per Quintal (₹)</label>
                <input
                  type="number"
                  value={newListing.price_per_quintal}
                  onChange={(e) => setNewListing({ ...newListing, price_per_quintal: Number(e.target.value) })}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
                <input
                  type="text"
                  value={newListing.location}
                  onChange={(e) => setNewListing({ ...newListing, location: e.target.value })}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-primary-600 hover:bg-primary-700 text-white font-medium py-2.5 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Creating...' : 'Create Listing'}
            </button>
          </form>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200 mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Filter Listings</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-4">
          <input
            type="text"
            placeholder="Crop name"
            value={filter.crop}
            onChange={(e) => setFilter({ ...filter, crop: e.target.value })}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
          <input
            type="number"
            placeholder="Min price"
            value={filter.min_price}
            onChange={(e) => setFilter({ ...filter, min_price: e.target.value })}
            className="w-32 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
          <input
            type="number"
            placeholder="Max price"
            value={filter.max_price}
            onChange={(e) => setFilter({ ...filter, max_price: e.target.value })}
            className="w-32 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
          {user?.role === 'buyer' && <input type="text" placeholder="Seller name" value={filter.seller} onChange={(e) => setFilter({ ...filter, seller: e.target.value })} className="px-3 py-2 border border-gray-300 rounded-lg" />}
          <input type="number" min="0" placeholder="Minimum quantity (qtl)" value={filter.min_quantity} onChange={(e) => setFilter({ ...filter, min_quantity: e.target.value })} className="px-3 py-2 border border-gray-300 rounded-lg" />
          <select aria-label="Sort listings" value={filter.sort_by} onChange={(e) => setFilter({ ...filter, sort_by: e.target.value })} className="px-3 py-2 border border-gray-300 rounded-lg"><option value="newest">Newest</option><option value="price_asc">Price: low to high</option><option value="price_desc">Price: high to low</option><option value="quantity">Quantity available</option></select>
          <button
            onClick={() => void fetchListings()}
            className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
          >
            Apply Filter
          </button>
          <button onClick={() => { const clean = { crop: '', min_price: '', max_price: '', min_quantity: '', seller: '', sort_by: 'newest' }; setFilter(clean); setOffset(0); marketplaceAPI.getListings({ sort_by: 'newest', limit: 24, offset: 0 }).then(setListings).catch((err) => setError(formatError(err))); }} className="px-4 py-2 border rounded-lg text-gray-700">Clear all</button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200 mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Available Listings ({listings.length} shown)</h2>
        {listings.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No listings found.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {listings.map((listing) => (
              <div key={listing.id} className="border border-gray-200 rounded-lg p-5 hover:shadow-md transition-shadow">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{listing.crop_name}</h3>
                <div className="space-y-1 text-sm text-gray-600 mb-4">
                  <p><span className="font-medium">Quantity:</span> {listing.quantity_quintals} quintals</p>
                  <p><span className="font-medium">Price:</span> ₹{listing.price_per_quintal}/quintal</p>
                  <p><span className="font-medium">Total:</span> ₹{(Number(listing.quantity_quintals) * Number(listing.price_per_quintal)).toFixed(2)}</p>
                  <p><span className="font-medium">Location:</span> {listing.location || 'Not provided'}</p>
                  <p><span className="font-medium">Seller:</span> {listing.seller_name || 'Farmer'}</p>
                  <p className="text-xs text-gray-500">Listed {new Date(listing.created_at).toLocaleDateString()} · Available</p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleViewListing(listing)}
                    className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg font-medium transition-colors"
                  >
                    View Listing
                  </button>
                  {user?.role === 'buyer' && <button onClick={() => void handleAddToCart(listing)} className="flex-1 bg-primary-600 text-white px-3 py-2 rounded-lg">Add to Cart</button>}
                  {user?.role === 'buyer' && <button onClick={() => void handleSaveListing(listing)} aria-label={`Save ${listing.crop_name}`} className="px-3 py-2 border border-primary-300 rounded-lg">♡</button>}
                </div>
              </div>
            ))}
          </div>
        )}
        {listings.length >= 24 && <button onClick={() => void fetchListings(true)} className="mt-5 rounded border px-4 py-2">Load more</button>}
      </div>

      {selectedListing && (
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200 mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Listing Details</h2>
            <button
              onClick={() => setSelectedListing(null)}
              className="text-gray-500 hover:text-gray-700"
            >
              Close
            </button>
          </div>
          <div className="space-y-2 text-sm text-gray-600 mb-4">
            <p><span className="font-medium">Crop:</span> {selectedListing.crop_name}</p>
            <p><span className="font-medium">Quantity:</span> {selectedListing.quantity_quintals} quintals</p>
            <p><span className="font-medium">Price:</span> ₹{selectedListing.price_per_quintal}/quintal</p>
            <p><span className="font-medium">Seller:</span> {selectedListing.seller_name || 'Farmer'}</p>
            <label className="block">Quantity to buy (quintals)<input type="number" min="0.01" max={Number(selectedListing.quantity_quintals)} step="0.01" value={purchaseQuantity} onChange={(e) => setPurchaseQuantity(Number(e.target.value))} className="mt-1 block w-full max-w-xs px-3 py-2 border rounded-lg" /></label>
            <p>Subtotal: ₹{(purchaseQuantity * Number(selectedListing.price_per_quintal)).toFixed(2)}</p>
            {user?.role === 'buyer' && <button onClick={() => void handleAddToCart(selectedListing, purchaseQuantity)} disabled={purchaseQuantity <= 0 || purchaseQuantity > Number(selectedListing.quantity_quintals)} className="bg-primary-600 text-white px-4 py-2 rounded-lg disabled:opacity-50">Add selected quantity to Cart</button>}
            {selectedListing.description && <p><span className="font-medium">Description:</span> {selectedListing.description}</p>}
            <p><span className="font-medium">Status:</span> {selectedListing.status}</p>
          </div>

          <div className="flex items-center justify-between mb-2"><h3 className="text-lg font-semibold text-gray-900">Messages</h3>{user?.role === 'buyer' && selectedListing.status === 'open' && <button onClick={() => setNewMessage('Hello, I am interested in this listing. Can we discuss availability and payment?')} className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg">Contact Farmer / Discuss Payment</button>} {user?.role === 'buyer' && selectedListing.status === 'open' && import.meta.env.VITE_RAZORPAY_KEY_ID && <button onClick={() => handleBuyNow(selectedListing)} disabled={loading || purchaseQuantity <= 0 || purchaseQuantity > Number(selectedListing.quantity_quintals)} className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg disabled:opacity-50">Buy Now</button>}</div>
          {messageError && <p className="mb-2 rounded bg-red-50 p-3 text-sm text-red-800">{messageError}</p>}
          <div className="bg-gray-50 rounded-lg p-4 min-h-[150px] max-h-[300px] overflow-y-auto mb-4">
            {messagesLoading ? <p className="text-gray-500 text-center">Loading conversation…</p> : messages.length === 0 ? (
              <p className="text-gray-500 text-center">No messages yet.</p>
            ) : (
              messages.map((msg) => (
                <div key={msg.id} className="bg-white p-3 rounded mb-2 shadow-sm">
                  <small className="text-gray-500">{msg.sender_id === user?.id ? 'You' : msg.sender_name || 'Farmer / buyer'} · {new Date(msg.created_at).toLocaleString()}</small>
                  <p>{msg.content}</p>
                </div>
              ))
            )}
          </div>
          <form onSubmit={handleSendMessage} className="flex gap-2">
            <input
              type="text"
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              placeholder="Type a message..."
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
            <button
              type="submit"
              className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
            >
              Send
            </button>
          </form>
        </div>
      )}


    </>
  );
}
