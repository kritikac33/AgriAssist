import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { financeAPI, type FinanceEntry, type FinanceSummary } from '../api/finance';
import farmAPI from '../api/farm';
import type { FarmResponse } from '../types';
import { formatError } from '../utils/errorFormatter';
import { getFarmLabel } from '../utils/farmLabeler';

export default function Finance() {
  const navigate = useNavigate();
  const [farms, setFarms] = useState<FarmResponse[]>([]);
  const [selectedFarmId, setSelectedFarmId] = useState<number | null>(null);
  const [entries, setEntries] = useState<FinanceEntry[]>([]);
  const [summary, setSummary] = useState<FinanceSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [loadingData, setLoadingData] = useState(false);

  const [newEntry, setNewEntry] = useState({
    farm_id: 0,
    entry_type: 'income' as 'income' | 'expense',
    amount: 0,
    category: '',
    notes: '',
    date: new Date().toISOString().split('T')[0],
  });

  useEffect(() => {
    const fetchData = async () => {
      setLoadingData(true);
      try {
        const userFarms = await farmAPI.getFarms();
        setFarms(userFarms.data);
        if (userFarms.data.length > 0) {
          setSelectedFarmId(userFarms.data[0].id);
          setNewEntry({ ...newEntry, farm_id: userFarms.data[0].id });
          await fetchEntries(userFarms.data[0].id);
          await fetchSummary(userFarms.data[0].id);
        }
      } catch (err) {
        console.error('Failed to fetch farms:', err);
      } finally {
        setLoadingData(false);
      }
    };
    fetchData();
  }, []);

  const handleFarmChange = async (farmId: number) => {
    setSelectedFarmId(farmId);
    setNewEntry({ ...newEntry, farm_id: farmId });
    await fetchEntries(farmId);
    await fetchSummary(farmId);
  };

  const fetchEntries = async (farmId: number) => {
    try {
      const data = await financeAPI.getEntries({ farm_id: farmId });
      setEntries(data);
    } catch (err: any) {
      setError(formatError(err) || 'Failed to fetch entries');
    }
  };

  const fetchSummary = async (farmId: number) => {
    try {
      const data = await financeAPI.getSummary(farmId);
      setSummary(data);
    } catch (err: any) {
      console.error('Failed to fetch summary');
    }
  };

  const handleAddEntry = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFarmId) {
      setError('Please select a farm');
      return;
    }
    setLoading(true);
    setError('');

    try {
      await financeAPI.createEntry({ ...newEntry, farm_id: selectedFarmId, amount: String(newEntry.amount) });
      setNewEntry({
        farm_id: selectedFarmId,
        entry_type: 'income',
        amount: 0,
        category: '',
        notes: '',
        date: new Date().toISOString().split('T')[0],
      });
      await fetchEntries(selectedFarmId);
      await fetchSummary(selectedFarmId);
    } catch (err: any) {
      setError(formatError(err) || 'Failed to add entry');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <span className="text-4xl">💰</span>
          Finance Tracker
        </h1>
        <p className="text-gray-600 mt-1">Track your farm income and expenses</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      {loadingData ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      ) : farms.length === 0 ? (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-6 text-center">
          <p className="text-amber-800 mb-4">You have no farms yet. Add your first farm to get started!</p>
          <button
            onClick={() => navigate('/dashboard')}
            className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg"
          >
            Go to Dashboard to Add Farm
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Select Farm</h2>
            <select
              value={selectedFarmId || ''}
              onChange={(e) => handleFarmChange(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              {farms.map((farm) => (
                <option key={farm.id} value={farm.id}>
                  {getFarmLabel(farm, farms)}
                </option>
              ))}
            </select>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Add Entry</h2>
            <form onSubmit={handleAddEntry} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                <select
                  value={newEntry.entry_type}
                  onChange={(e) => setNewEntry({ ...newEntry, entry_type: e.target.value as 'income' | 'expense' })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  <option value="income">Income</option>
                  <option value="expense">Expense</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Amount (₹)</label>
                <input
                  type="number"
                  value={newEntry.amount}
                  onChange={(e) => setNewEntry({ ...newEntry, amount: Number(e.target.value) })}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                <input
                  type="text"
                  value={newEntry.category}
                  onChange={(e) => setNewEntry({ ...newEntry, category: e.target.value })}
                  placeholder="e.g., Seeds, Fertilizer, Crop Sale"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                <input
                  type="text"
                  value={newEntry.notes}
                  onChange={(e) => setNewEntry({ ...newEntry, notes: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Date</label>
                <input
                  type="date"
                  value={newEntry.date}
                  onChange={(e) => setNewEntry({ ...newEntry, date: e.target.value })}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-primary-600 hover:bg-primary-700 text-white font-medium py-2.5 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Adding...' : 'Add Entry'}
              </button>
            </form>
          </div>
        </div>
      )}

      {summary && (
        <div className="mt-6 bg-primary-50 rounded-lg p-6 border border-primary-200">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Financial Summary</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white rounded-lg p-5 shadow-sm">
              <h3 className="text-sm font-medium text-gray-600 mb-1">Total Income</h3>
              <p className="text-2xl font-bold text-green-600">₹{Number(summary.total_income).toFixed(2)}</p>
            </div>
            <div className="bg-white rounded-lg p-5 shadow-sm">
              <h3 className="text-sm font-medium text-gray-600 mb-1">Total Expenses</h3>
              <p className="text-2xl font-bold text-red-600">₹{Number(summary.total_expenses).toFixed(2)}</p>
            </div>
            <div className="bg-white rounded-lg p-5 shadow-sm">
              <h3 className="text-sm font-medium text-gray-600 mb-1">Net Profit</h3>
              <p className={`text-2xl font-bold ${Number(summary.net_profit) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                ₹{Number(summary.net_profit).toFixed(2)}
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="mt-6 bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Transaction History</h2>
        {entries.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No entries found. Add one above.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-primary-50 border-b border-primary-200">
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Date</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Type</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Category</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Notes</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Amount</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((entry, index) => (
                  <tr key={entry.id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="px-4 py-3 text-sm">{entry.date.split('T')[0]}</td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${entry.entry_type === 'income' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                        {entry.entry_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm">{entry.category}</td>
                    <td className="px-4 py-3 text-sm text-gray-500">{entry.notes || '-'}</td>
                    <td className={`px-4 py-3 text-sm font-bold ${entry.entry_type === 'income' ? 'text-green-600' : 'text-red-600'}`}>
                      {entry.entry_type === 'income' ? '+' : '-'}₹{Number(entry.amount).toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
