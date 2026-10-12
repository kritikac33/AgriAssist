import { useState, useEffect } from 'react';
import { alertsAPI, type OutbreakAlert } from '../api/alerts';
import { useAuth } from '../contexts/AuthContext';
import { formatError } from '../utils/errorFormatter';

export default function Alerts() {
  const { user } = useAuth();
  const [alerts, setAlerts] = useState<OutbreakAlert[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [newAlert, setNewAlert] = useState({
    disease_name: '',
    region_description: '',
    center_latitude: 18.52,
    center_longitude: 73.85,
    radius_km: 50,
    severity: 'medium' as 'low' | 'medium' | 'high',
    case_count: 0,
    preventive_measures: '',
  });

  useEffect(() => {
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    try {
      const data = await alertsAPI.getAlerts(18.52, 73.85);
      setAlerts(data);
    } catch (err: any) {
      setError(formatError(err) || 'Failed to fetch alerts');
    }
  };

  const handleCreateAlert = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await alertsAPI.createAlert({
        ...newAlert,
        center_latitude: String(newAlert.center_latitude),
        center_longitude: String(newAlert.center_longitude),
        radius_km: String(newAlert.radius_km),
        preventive_measures: newAlert.preventive_measures || undefined,
      });
      setNewAlert({
        disease_name: '',
        region_description: '',
        center_latitude: 18.52,
        center_longitude: 73.85,
        radius_km: 50,
        severity: 'medium',
        case_count: 0,
        preventive_measures: '',
      });
      await fetchAlerts();
    } catch (err: any) {
      setError(formatError(err) || 'Failed to create alert');
    } finally {
      setLoading(false);
    }
  };

  const handleRetractAlert = async (id: number) => {
    try {
      await alertsAPI.retractAlert(id);
      await fetchAlerts();
    } catch (err: any) {
      setError(formatError(err) || 'Failed to retract alert');
    }
  };

  const getSeverityColor = (severity: string) => {
    if (severity === 'high') return 'bg-red-100 text-red-800';
    if (severity === 'medium') return 'bg-amber-100 text-amber-800';
    if (severity === 'low') return 'bg-green-100 text-green-800';
    return 'bg-gray-100 text-gray-800';
  };

  return (
    <>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <span className="text-4xl">🚨</span>
          Pest Outbreak Alerts
        </h1>
        <p className="text-gray-600 mt-1">View alerts near your location or create new alerts (officer only)</p>
      </div>

      {user?.role === 'officer' && (
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Create New Alert</h2>
          <form onSubmit={handleCreateAlert} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Disease Name</label>
              <input
                type="text"
                value={newAlert.disease_name}
                onChange={(e) => setNewAlert({ ...newAlert, disease_name: e.target.value })}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Region Description</label>
              <input
                type="text"
                value={newAlert.region_description}
                onChange={(e) => setNewAlert({ ...newAlert, region_description: e.target.value })}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Latitude</label>
                <input
                  type="number"
                  step="0.0001"
                  value={newAlert.center_latitude}
                  onChange={(e) => setNewAlert({ ...newAlert, center_latitude: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Longitude</label>
                <input
                  type="number"
                  step="0.0001"
                  value={newAlert.center_longitude}
                  onChange={(e) => setNewAlert({ ...newAlert, center_longitude: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Radius (km)</label>
                <input
                  type="number"
                  value={newAlert.radius_km}
                  onChange={(e) => setNewAlert({ ...newAlert, radius_km: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Severity</label>
                <select
                  value={newAlert.severity}
                  onChange={(e) => setNewAlert({ ...newAlert, severity: e.target.value as 'low' | 'medium' | 'high' })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Case Count</label>
              <input
                type="number"
                value={newAlert.case_count}
                onChange={(e) => setNewAlert({ ...newAlert, case_count: Number(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Preventive Measures (comma-separated)</label>
              <textarea
                value={newAlert.preventive_measures}
                onChange={(e) => setNewAlert({ ...newAlert, preventive_measures: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent min-h-[80px]"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-primary-600 hover:bg-primary-700 text-white font-medium py-2.5 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Creating...' : 'Create Alert'}
            </button>
          </form>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Active Alerts</h2>
        {alerts.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No active alerts in your area.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {alerts.map((alert) => (
              <div key={alert.id} className={`p-5 rounded-lg border ${alert.is_active ? 'bg-amber-50 border-amber-200' : 'bg-gray-50 border-gray-200'}`}>
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">{alert.disease_name}</h3>
                    <div className="space-y-1 text-sm">
                      <p><span className="font-medium">Region:</span> {alert.region_description}</p>
                      <p className="flex items-center gap-2">
                        <span className="font-medium">Severity:</span>
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${getSeverityColor(alert.severity)}`}>
                          {alert.severity}
                        </span>
                      </p>
                      <p><span className="font-medium">Case Count:</span> {alert.case_count}</p>
                      <p><span className="font-medium">Radius:</span> {Number(alert.radius_km)} km</p>
                      <p><span className="font-medium">Created:</span> {alert.created_at}</p>
                      {alert.retracted_at && <p><span className="font-medium">Retracted:</span> {alert.retracted_at}</p>}
                    </div>
                  </div>
                  {user?.role === 'officer' && alert.is_active && (
                    <button
                      onClick={() => handleRetractAlert(alert.id)}
                      className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                    >
                      Retract
                    </button>
                  )}
                </div>
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <p className="font-medium text-sm text-gray-900 mb-2">Preventive Measures:</p>
                  <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                    {alert.preventive_measures ? alert.preventive_measures.split(', ').map((measure, index) => (
                      <li key={index}>{measure}</li>
                    )) : <li className="text-gray-400">No preventive measures specified</li>}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
