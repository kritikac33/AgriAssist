import { useState, useEffect } from 'react';
import { marketplaceAPI, type Listing, type Message } from '../api/marketplace';
import { transactionsAPI, type Transaction } from '../api/transactions';
import { useAuth } from '../contexts/AuthContext';
import { formatError } from '../utils/errorFormatter';

declare global {
  interface Window {
    Razorpay: any;
  }
}

export default function Marketplace() {
  const { user } = useAuth();
  const [listings, setListings] = useState<Listing[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [selectedListing, setSelectedListing] = useState<Listing | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [filter, setFilter] = useState({ crop: '', min_price: '', max_price: '' });

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
    fetchTransactions();
  }, []);

  const fetchListings = async () => {
    try {
      const params: any = {};
      if (filter.crop) params.crop = filter.crop;
      if (filter.min_price) params.min_price = Number(filter.min_price);
      if (filter.max_price) params.max_price = Number(filter.max_price);
      const data = await marketplaceAPI.getListings(params);
      setListings(data);
    } catch (err: any) {
      setError(formatError(err) || 'Failed to fetch listings');
    }
  };

  const fetchTransactions = async () => {
    try {
      const data = await transactionsAPI.getTransactions();
      setTransactions(data);
    } catch (err: any) {
      console.error('Failed to fetch transactions');
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
    try {
      const msgs = await marketplaceAPI.getMessages(listing.id);
      setMessages(msgs);
    } catch (err) {
      console.error('Failed to fetch messages');
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedListing || !newMessage.trim()) return;

    try {
      await marketplaceAPI.sendMessage(selectedListing.id, newMessage);
      setNewMessage('');
      const msgs = await marketplaceAPI.getMessages(selectedListing.id);
      setMessages(msgs);
    } catch (err: any) {
      setError(formatError(err) || 'Failed to send message');
    }
  };

  const handleBuyNow = async (listing: Listing) => {
    if (!user || user.role !== 'buyer') {
      setError('Only buyers can purchase');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const transaction = await transactionsAPI.createTransaction(listing.id);

      if (!window.Razorpay) {
        const script = document.createElement('script');
        script.src = 'https://checkout.razorpay.com/v1/checkout.js';
        script.async = true;
        script.onload = () => openRazorpay(transaction, listing);
        document.body.appendChild(script);
      } else {
        openRazorpay(transaction, listing);
      }
    } catch (err: any) {
      setError(formatError(err) || 'Failed to initiate transaction');
      setLoading(false);
    }
  };

  const openRazorpay = (transaction: Transaction, listing: Listing) => {
    const options = {
      key: 'rzp_test_DEMO_KEY',
      amount: Number(listing.quantity_quintals) * Number(listing.price_per_quintal) * 100,
      currency: 'INR',
      name: 'AgriAssist',
      description: `Purchase ${listing.crop_name}`,
      order_id: transaction.razorpay_order_id,
      handler: async (_response: any) => {
        try {
          const verified = await transactionsAPI.verifyTransaction(transaction.id);
          if (verified.status === 'completed') {
            alert('Payment successful!');
            await fetchTransactions();
            await fetchListings();
          }
        } catch (err) {
          setError('Payment verification failed');
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
      setError('Payment failed');
      setLoading(false);
    });
  };

  const getPriceBadgeColor = (label: string | null) => {
    if (!label) return 'bg-gray-100 text-gray-800';
    if (label === 'below') return 'bg-green-100 text-green-800';
    if (label === 'near') return 'bg-blue-100 text-blue-800';
    if (label === 'above') return 'bg-red-100 text-red-800';
    return 'bg-gray-100 text-gray-800';
  };

  const getStatusColor = (status: string) => {
    if (status === 'completed') return 'bg-green-100 text-green-800';
    if (status === 'pending') return 'bg-amber-100 text-amber-800';
    if (status === 'failed') return 'bg-red-100 text-red-800';
    if (status === 'cancelled') return 'bg-gray-100 text-gray-800';
    return 'bg-gray-100 text-gray-800';
  };

  return (
    <>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <span className="text-4xl">🛒</span>
          Marketplace
        </h1>
        <p className="text-gray-600 mt-1">Browse crops, buy with Razorpay, or list your produce</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

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
        <div className="flex gap-4 mb-4">
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
          <button
            onClick={fetchListings}
            className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
          >
            Apply Filter
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200 mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Available Listings</h2>
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
                  <p><span className="font-medium">Location:</span> {listing.location}</p>
                  {listing.price_label && (
                    <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${getPriceBadgeColor(listing.price_label)}`}>
                      {listing.price_label.toUpperCase()} MARKET PRICE
                    </span>
                  )}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleViewListing(listing)}
                    className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg font-medium transition-colors"
                  >
                    View Details
                  </button>
                  {user?.role === 'buyer' && listing.status === 'open' && (
                    <button
                      onClick={() => handleBuyNow(listing)}
                      disabled={loading}
                      className="flex-1 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Buy Now
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
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
            <p><span className="font-medium">Status:</span> {selectedListing.status}</p>
            {selectedListing.market_price_benchmark && (
              <p><span className="font-medium">Market Price Benchmark:</span> ₹{selectedListing.market_price_benchmark}/quintal</p>
            )}
          </div>

          <h3 className="text-lg font-semibold text-gray-900 mb-2">Messages</h3>
          <div className="bg-gray-50 rounded-lg p-4 min-h-[150px] max-h-[300px] overflow-y-auto mb-4">
            {messages.length === 0 ? (
              <p className="text-gray-500 text-center">No messages yet.</p>
            ) : (
              messages.map((msg) => (
                <div key={msg.id} className="bg-white p-3 rounded mb-2 shadow-sm">
                  <small className="text-gray-500">{msg.created_at}</small>
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

      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Your Transactions</h2>
        {transactions.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No transactions yet.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-primary-50 border-b border-primary-200">
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">ID</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Listing ID</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Amount</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Status</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Date</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((txn, index) => (
                  <tr key={txn.id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="px-4 py-3 text-sm">{txn.id}</td>
                    <td className="px-4 py-3 text-sm">{txn.listing_id}</td>
                    <td className="px-4 py-3 text-sm font-medium">₹{Number(txn.total_amount).toFixed(2)}</td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(txn.status)}`}>
                        {txn.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm">{txn.created_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-lg p-6 mt-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Razorpay Test Card Numbers</h3>
        <div className="space-y-1 text-sm text-gray-700">
          <p><span className="font-medium">Success:</span> 4111 1111 1111 1111 (any expiry, any CVV)</p>
          <p><span className="font-medium">Failure:</span> 4111 1111 1111 1111 (expires this month)</p>
          <p><span className="font-medium">Netbanking:</span> Select any bank from the list</p>
        </div>
      </div>
    </>
  );
}
