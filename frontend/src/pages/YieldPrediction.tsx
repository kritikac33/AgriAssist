import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import yieldAPI from '../api/yield';
import farmAPI from '../api/farm';
import cropAPI from '../api/crop';
import type { YieldPredictionResponse, FarmResponse, CropResponse } from '../types';
import { formatError } from '../utils/errorFormatter';
import { getFarmLabel } from '../utils/farmLabeler';

export default function YieldPrediction() {
  const navigate = useNavigate();
  const [farms, setFarms] = useState<FarmResponse[]>([]);
  const [crops, setCrops] = useState<CropResponse[]>([]);
  const [selectedFarmId, setSelectedFarmId] = useState<number | null>(null);
  const [cropId, setCropId] = useState<number | null>(null);
  const [landSizeAcres, setLandSizeAcres] = useState(1.0);
  const [plantingDate, setPlantingDate] = useState(new Date().toISOString().split('T')[0]);
  const [predictions, setPredictions] = useState<YieldPredictionResponse[]>([]);
  const [history, setHistory] = useState<YieldPredictionResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [loadingData, setLoadingData] = useState(false);

  const fetchPredictions = async () => {
    if (!cropId) return;
    try {
      const data = await yieldAPI.getPredictions(cropId);
      setPredictions(data.data);
    } catch (err: any) {
      setError(formatError(err) || 'Failed to fetch predictions');
    }
  };

  const fetchHistory = async () => {
    if (!cropId) return;
    try {
      const data = await yieldAPI.getHistory(cropId);
      setHistory(data.data);
    } catch (err: any) {
      console.error('Failed to fetch history');
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      setLoadingData(true);
      try {
        const userFarms = await farmAPI.getFarms();
        setFarms(userFarms.data);
        if (userFarms.data.length > 0) {
          setSelectedFarmId(userFarms.data[0].id);
          const farmCrops = await cropAPI.getCrops(userFarms.data[0].id);
          setCrops(farmCrops.data);
          if (farmCrops.data.length > 0) {
            setCropId(farmCrops.data[0].id);
            await fetchPredictions();
            await fetchHistory();
          }
        }
      } catch (err) {
        console.error('Failed to fetch farms/crops:', err);
      } finally {
        setLoadingData(false);
      }
    };
    fetchData();
  }, []);

  const handleFarmChange = async (farmId: number) => {
    setSelectedFarmId(farmId);
    try {
      const farmCrops = await cropAPI.getCrops(farmId);
      setCrops(farmCrops.data);
      setCropId(farmCrops.data.length > 0 ? farmCrops.data[0].id : null);
      if (farmCrops.data.length > 0) {
        await fetchPredictions();
        await fetchHistory();
      }
    } catch (err) {
      console.error('Failed to fetch crops:', err);
      setCrops([]);
      setCropId(null);
    }
  };

  const handlePredict = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFarmId) {
      setError('Please select a farm');
      return;
    }
    if (!cropId) {
      setError('Please select a crop');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await yieldAPI.createPrediction({
        farm_id: selectedFarmId,
        crop_id: cropId,
        land_size_acres: landSizeAcres,
        planting_date: plantingDate,
      });
      await fetchPredictions();
      await fetchHistory();
    } catch (err: any) {
      setError(formatError(err) || 'Prediction failed');
    } finally {
      setLoading(false);
    }
  };

  const getConfidenceColor = (label: string) => {
    if (label === 'high') return 'bg-green-100 text-green-800';
    if (label === 'medium') return 'bg-amber-100 text-amber-800';
    if (label === 'low') return 'bg-red-100 text-red-800';
    return 'bg-gray-100 text-gray-800';
  };

  return (
    <>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <span className="text-4xl">📊</span>
          Yield Prediction
        </h1>
        <p className="text-gray-600 mt-1">Predict crop yield using ML models</p>
      </div>

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
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Generate Prediction</h2>
            <form onSubmit={handlePredict} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Farm</label>
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
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Crop</label>
                  <select
                    value={cropId || ''}
                    onChange={(e) => setCropId(Number(e.target.value))}
                    disabled={crops.length === 0}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                  >
                    {crops.length === 0 ? (
                      <option value="">No crops available</option>
                    ) : (
                      crops.map((crop) => (
                        <option key={crop.id} value={crop.id}>
                          {crop.name} {crop.variety ? `(${crop.variety})` : ''}
                        </option>
                      ))
                    )}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Land Size (acres)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={landSizeAcres}
                    onChange={(e) => setLandSizeAcres(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Planting Date</label>
                  <input
                    type="date"
                    value={plantingDate}
                    onChange={(e) => setPlantingDate(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-primary-600 hover:bg-primary-700 text-white font-medium py-2.5 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Predicting...' : 'Generate Prediction'}
              </button>
            </form>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Current Predictions</h2>
            {predictions.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p>No predictions found. Generate one above.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="bg-primary-50 border-b border-primary-200">
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Yield Range (quintals)</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Expected</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Confidence</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Harvest Window</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Version</th>
                    </tr>
                  </thead>
                  <tbody>
                    {predictions.map((pred, index) => (
                      <tr key={pred.id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        <td className="px-4 py-3 text-sm">
                          {Number(pred.predicted_yield_low).toFixed(2)} - {Number(pred.predicted_yield_high).toFixed(2)}
                        </td>
                        <td className="px-4 py-3 text-sm font-medium">{Number(pred.predicted_yield_expected).toFixed(2)}</td>
                        <td className="px-4 py-3 text-sm">
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${getConfidenceColor(pred.confidence_label)}`}>
                            {pred.confidence_label}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm">
                          {pred.harvest_window_start?.split('T')[0]} to {pred.harvest_window_end?.split('T')[0]}
                        </td>
                        <td className="px-4 py-3 text-sm">v{pred.version}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {history.length > 0 && (
        <div className="mt-6 bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Prediction History</h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-primary-50 border-b border-primary-200">
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Date</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Expected Yield</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Confidence</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Version</th>
                </tr>
              </thead>
              <tbody>
                {history.map((pred, index) => (
                  <tr key={pred.id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="px-4 py-3 text-sm">{pred.created_at.split('T')[0]}</td>
                    <td className="px-4 py-3 text-sm font-medium">{Number(pred.predicted_yield_expected).toFixed(2)}</td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${getConfidenceColor(pred.confidence_label)}`}>
                        {pred.confidence_label}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm">v{pred.version}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}
