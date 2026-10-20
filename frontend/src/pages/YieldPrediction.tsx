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
  const [yieldInputs, setYieldInputs] = useState({ ph_level: '', nitrogen: '', phosphorus: '', potassium: '', soil_moisture_percent: '', rainfall_mm: '', irrigation_mm: '', temperature_c: '' });
  const [predictions, setPredictions] = useState<YieldPredictionResponse[]>([]);
  const [history, setHistory] = useState<YieldPredictionResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [loadingData, setLoadingData] = useState(false);


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
            const [predictionData, historyData] = await Promise.all([
              yieldAPI.getPredictions(userFarms.data[0].id, farmCrops.data[0].id),
              yieldAPI.getHistory(farmCrops.data[0].id),
            ]);
            setPredictions(predictionData.data);
            setHistory(historyData.data);
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
        const [predictionData, historyData] = await Promise.all([
          yieldAPI.getPredictions(farmId, farmCrops.data[0].id),
          yieldAPI.getHistory(farmCrops.data[0].id),
        ]);
        setPredictions(predictionData.data);
        setHistory(historyData.data);
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
      const created = await yieldAPI.createPrediction({
        farm_id: selectedFarmId,
        crop_id: cropId,
        land_size_acres: landSizeAcres,
        planting_date: plantingDate,
        ...Object.fromEntries(Object.entries(yieldInputs).map(([key, value]) => [key, value === '' ? undefined : Number(value)])),
      });
      setPredictions((current) => [created.data, ...current.filter((item) => item.id !== created.data.id)]);
      const historyData = await yieldAPI.getHistory(cropId);
      setHistory(historyData.data);
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
        <p className="text-gray-600 mt-1">Estimate production from crop and area; results are indicative and not a validated ML forecast</p>
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

              <details className="rounded-lg border border-gray-200 p-4">
                <summary className="cursor-pointer font-medium text-gray-800">Optional soil and weather inputs</summary>
                <p className="text-xs text-gray-500 mt-1">Leave blank to use the latest soil test and available weather estimate.</p>
                <div className="grid grid-cols-2 gap-3 mt-3">
                  {([['ph_level', 'Soil pH', '0', '14', '0.1'], ['nitrogen', 'Nitrogen (mg/kg)', '0', '', '1'], ['phosphorus', 'Phosphorus (mg/kg)', '0', '', '1'], ['potassium', 'Potassium (mg/kg)', '0', '', '1'], ['soil_moisture_percent', 'Moisture (%)', '0', '100', '1'], ['rainfall_mm', 'Rainfall (mm)', '0', '', '1'], ['irrigation_mm', 'Irrigation (mm)', '0', '', '1'], ['temperature_c', 'Temperature (C)', '-10', '60', '0.1']] as const).map(([key, label, min, max, step]) => <label key={key} className="text-sm text-gray-700">{label}<input type="number" min={min} max={max || undefined} step={step} value={yieldInputs[key]} onChange={(e) => setYieldInputs((current) => ({ ...current, [key]: e.target.value }))} className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg" /></label>)}
                </div>
              </details>
              <button
                type="submit"
                disabled={loading || landSizeAcres <= 0 || !plantingDate}
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
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Estimated range (tonnes total)</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Expected yield (t/ha) · production (t)</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Confidence</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Harvest Window</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Version</th>
                    </tr>
                  </thead>
                  <tbody>
                    {predictions.map((pred, index) => (
                      <tr key={pred.id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        <td className="px-4 py-3 text-sm">
                          {(Number(pred.predicted_yield_low) * 0.1).toFixed(2)} - {(Number(pred.predicted_yield_high) * 0.1).toFixed(2)} t total
                        </td>
                        <td className="px-4 py-3 text-sm font-medium">{((Number(pred.predicted_yield_expected) * 0.1) / (Number(pred.land_size_acres) * 0.404686)).toFixed(2)} t/ha · {(Number(pred.predicted_yield_expected) * 0.1).toFixed(2)} t</td>
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
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Prediction History</h2>
          <p className="text-sm text-gray-600 mb-4">The current fallback estimates crop-specific baseline quintals per acre, adjusted for planting season and available weather. This is not a validated ML forecast; results are planning estimates.</p>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-primary-50 border-b border-primary-200">
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Date</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Expected Yield</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Confidence</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Version</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Saved inputs</th>
                </tr>
              </thead>
              <tbody>
                {history.map((pred, index) => (
                  <tr key={pred.id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="px-4 py-3 text-sm">{pred.created_at.split('T')[0]}</td>
                    <td className="px-4 py-3 text-sm font-medium">{(Number(pred.predicted_yield_expected) * 0.1).toFixed(2)} t total</td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${getConfidenceColor(pred.confidence_label)}`}>
                        {pred.confidence_label}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm">v{pred.version}</td>
                    <td className="px-4 py-3 text-xs text-gray-600">{pred.input_snapshot ? `${String(pred.input_snapshot.land_size_acres)} acres · pH ${String(pred.input_snapshot.ph_level ?? 'n/a')} · rain ${String(pred.input_snapshot.rainfall_mm ?? 'n/a')} mm · ${String(pred.model_version || 'saved estimator')}` : `${pred.land_size_acres} acres · earlier record (input snapshot unavailable)`}</td>
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
