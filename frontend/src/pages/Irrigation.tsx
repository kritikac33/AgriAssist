import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import irrigationAPI from '../api/irrigation';
import farmAPI from '../api/farm';
import cropAPI from '../api/crop';
import type { IrrigationScheduleResponse, FarmResponse, CropResponse } from '../types';
import { formatError } from '../utils/errorFormatter';
import { getFarmLabel } from '../utils/farmLabeler';

export default function Irrigation() {
  const navigate = useNavigate();
  const [farms, setFarms] = useState<FarmResponse[]>([]);
  const [crops, setCrops] = useState<CropResponse[]>([]);
  const [selectedFarmId, setSelectedFarmId] = useState<number | null>(null);
  const [cropId, setCropId] = useState<number | null>(null);
  const [schedules, setSchedules] = useState<IrrigationScheduleResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [loadingData, setLoadingData] = useState(false);

  const fetchSchedules = async () => {
    if (!selectedFarmId) return;
    try {
      const data = await irrigationAPI.getSchedules(selectedFarmId);
      setSchedules(data.data);
    } catch (err: any) {
      setError(formatError(err) || 'Failed to fetch schedules');
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
          await fetchSchedules();
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
      await fetchSchedules();
    } catch (err) {
      console.error('Failed to fetch crops:', err);
      setCrops([]);
      setCropId(null);
    }
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFarmId || !cropId) {
      setError('Please select a farm and crop');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await irrigationAPI.createSchedule({
        farm_id: selectedFarmId,
        scheduled_date: new Date().toISOString().split('T')[0],
        water_amount_liters: 1000,
        status: 'pending',
      });
      await fetchSchedules();
    } catch (err: any) {
      setError(formatError(err) || 'Failed to generate schedule');
    } finally {
      setLoading(false);
    }
  };

  const handleRecalculate = async (id: number) => {
    try {
      await irrigationAPI.recalculateSchedule(id);
      await fetchSchedules();
    } catch (err: any) {
      setError(formatError(err) || 'Failed to recalculate');
    }
  };

  const handlePostpone = async (id: number, days: number) => {
    try {
      await irrigationAPI.postponeSchedule(id, days);
      await fetchSchedules();
    } catch (err: any) {
      setError(formatError(err) || 'Failed to postpone');
    }
  };

  const getStatusColor = (status: string) => {
    if (status === 'completed') return 'bg-green-100 text-green-800';
    if (status === 'postponed') return 'bg-amber-100 text-amber-800';
    if (status === 'pending') return 'bg-blue-100 text-blue-800';
    if (status === 'cancelled') return 'bg-red-100 text-red-800';
    return 'bg-gray-100 text-gray-800';
  };

  return (
    <>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <span className="text-4xl">💧</span>
          Irrigation Schedule
        </h1>
        <p className="text-gray-600 mt-1">Generate weather-driven irrigation schedules for your crops</p>
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
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Generate Schedule</h2>
            <form onSubmit={handleGenerate} className="space-y-4">
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

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-primary-600 hover:bg-primary-700 text-white font-medium py-2.5 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Generating...' : 'Generate Schedule'}
              </button>
            </form>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Irrigation Schedule</h2>
            {schedules.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p>No schedules found. Generate one above.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="bg-primary-50 border-b border-primary-200">
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Date</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Water (L)</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Status</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {schedules.map((schedule, index) => (
                      <tr key={schedule.id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        <td className="px-4 py-3 text-sm">{schedule.scheduled_date}</td>
                        <td className="px-4 py-3 text-sm">{schedule.water_amount_liters}</td>
                        <td className="px-4 py-3 text-sm">
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(schedule.status)}`}>
                            {schedule.status}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm">
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleRecalculate(schedule.id)}
                              className="text-primary-600 hover:text-primary-700 text-xs font-medium px-2 py-1 border border-primary-300 rounded hover:bg-primary-50"
                            >
                              Recalculate
                            </button>
                            <button
                              onClick={() => handlePostpone(schedule.id, 1)}
                              className="text-amber-600 hover:text-amber-700 text-xs font-medium px-2 py-1 border border-amber-300 rounded hover:bg-amber-50"
                            >
                              Postpone 1 Day
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}
