import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import soilAPI from '../api/soil';
import farmAPI from '../api/farm';
import cropAPI from '../api/crop';
import type { SoilAnalysis, FarmResponse, CropResponse } from '../types';
import { formatError } from '../utils/errorFormatter';
import { getFarmLabel } from '../utils/farmLabeler';

export default function SoilHealth() {
  const navigate = useNavigate();
  const [farms, setFarms] = useState<FarmResponse[]>([]);
  const [crops, setCrops] = useState<CropResponse[]>([]);
  const [selectedFarmId, setSelectedFarmId] = useState<number | null>(null);
  const [cropId, setCropId] = useState<number | null>(null);
  const [phLevel, setPhLevel] = useState(6.5);
  const [nitrogen, setNitrogen] = useState(50);
  const [phosphorus, setPhosphorus] = useState(30);
  const [potassium, setPotassium] = useState(40);
  const [organicMatter, setOrganicMatter] = useState(2.5);
  const [moisture, setMoisture] = useState(30);
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<SoilAnalysis | null>(null);
  const [error, setError] = useState('');
  const [loadingData, setLoadingData] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
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
    setAnalysis(null);

    try {
      const record = await soilAPI.createSoilRecord({
        farm_id: selectedFarmId,
        ph_level: phLevel,
        nitrogen,
        phosphorus,
        potassium,
        organic_matter: organicMatter,
        source: 'manual',
      });

      const crop = crops.find(c => c.id === cropId);
      const cropName = crop ? crop.name.toLowerCase() : 'tomato';
      const result = await soilAPI.analyzeSoil(record.data.id, cropName);
      setAnalysis(result.data);
    } catch (err: any) {
      setError(formatError(err) || 'Analysis failed');
    } finally {
      setLoading(false);
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
    } catch (err) {
      console.error('Failed to fetch crops:', err);
      setCrops([]);
      setCropId(null);
    }
  };

  const getStatusColor = (status: string) => {
    if (status === 'optimal') return 'bg-green-100 text-green-800';
    if (status === 'low') return 'bg-amber-100 text-amber-800';
    if (status === 'high') return 'bg-red-100 text-red-800';
    return 'bg-gray-100 text-gray-800';
  };

  return (
    <>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <span className="text-4xl">🌱</span>
          Soil Health Analysis
        </h1>
        <p className="text-gray-600 mt-1">Enter soil test results to get recommendations</p>
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
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Soil Test Data</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
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

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">pH Level</label>
                  <input
                    type="number"
                    step="0.1"
                    value={phLevel}
                    onChange={(e) => setPhLevel(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Nitrogen (mg/kg)</label>
                  <input
                    type="number"
                    value={nitrogen}
                    onChange={(e) => setNitrogen(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Phosphorus (mg/kg)</label>
                  <input
                    type="number"
                    value={phosphorus}
                    onChange={(e) => setPhosphorus(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Potassium (mg/kg)</label>
                  <input
                    type="number"
                    value={potassium}
                    onChange={(e) => setPotassium(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Organic Matter (%)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={organicMatter}
                    onChange={(e) => setOrganicMatter(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Moisture (%)</label>
                  <input
                    type="number"
                    value={moisture}
                    onChange={(e) => setMoisture(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-primary-600 hover:bg-primary-700 text-white font-medium py-2.5 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Analyzing...' : 'Analyze Soil'}
              </button>
            </form>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          {analysis && (
            <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Soil Analysis Results</h2>
              <div className="space-y-4">
                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-gray-900">pH Status</span>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(analysis.ph_status)}`}>
                      {analysis.ph_status}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">{analysis.ph_explanation}</p>
                </div>

                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-gray-900">Nitrogen Status</span>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(analysis.nitrogen_status)}`}>
                      {analysis.nitrogen_status}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">{analysis.nitrogen_explanation}</p>
                </div>

                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-gray-900">Phosphorus Status</span>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(analysis.phosphorus_status)}`}>
                      {analysis.phosphorus_status}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">{analysis.phosphorus_explanation}</p>
                </div>

                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-gray-900">Potassium Status</span>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(analysis.potassium_status)}`}>
                      {analysis.potassium_status}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">{analysis.potassium_explanation}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </>
  );
}
