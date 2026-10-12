import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { schemesAPI, type SchemeMatch, type Scheme } from '../api/schemes';
import farmAPI from '../api/farm';
import type { FarmResponse } from '../types';
import { formatError } from '../utils/errorFormatter';
import { getFarmLabel } from '../utils/farmLabeler';

export default function Schemes() {
  const navigate = useNavigate();
  const [farms, setFarms] = useState<FarmResponse[]>([]);
  const [selectedFarmId, setSelectedFarmId] = useState<number | null>(null);
  const [cropName, setCropName] = useState('');
  const [state, setState] = useState('');
  const [matches, setMatches] = useState<SchemeMatch[]>([]);
  const [allSchemes, setAllSchemes] = useState<Scheme[]>([]);
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
        }
      } catch (err) {
        console.error('Failed to fetch farms:', err);
      } finally {
        setLoadingData(false);
      }
    };
    fetchData();
    fetchAllSchemes();
  }, []);

  const fetchAllSchemes = async () => {
    try {
      const data = await schemesAPI.getSchemes();
      setAllSchemes(data);
      setError('');
    } catch (err: any) {
      setError(formatError(err) || 'Failed to fetch schemes');
    }
  };

  const handleCheckEligibility = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFarmId) {
      setError('Please select a farm');
      return;
    }
    setLoading(true);
    setError('');
    setMatches([]);

    try {
      const data = await schemesAPI.getMatches(selectedFarmId, cropName, state);
      setMatches(data);
    } catch (err: any) {
      setError(formatError(err) || 'Failed to check eligibility');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <span className="text-4xl">🏛️</span>
          Government Schemes
        </h1>
        <p className="text-gray-600 mt-1">Check eligibility for agricultural government schemes</p>
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
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Check Eligibility</h2>
          <form onSubmit={handleCheckEligibility} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Farm</label>
              <select
                value={selectedFarmId || ''}
                onChange={(e) => setSelectedFarmId(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                {farms.map((farm) => (
                  <option key={farm.id} value={farm.id}>
                    {getFarmLabel(farm, farms)}
                  </option>
                ))}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Crop Name (optional)</label>
                <input
                  type="text"
                  value={cropName}
                  onChange={(e) => setCropName(e.target.value)}
                  placeholder="e.g., Rice, Wheat, Cotton"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">State (optional)</label>
                <input
                  type="text"
                  value={state}
                  onChange={(e) => setState(e.target.value)}
                  placeholder="e.g., Maharashtra, Karnataka"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-primary-600 hover:bg-primary-700 text-white font-medium py-2.5 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Checking...' : 'Check Eligibility'}
            </button>
          </form>
        </div>
      )}

      {matches.length > 0 && (
        <div className="bg-green-50 rounded-lg p-6 border border-green-200 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Matched Schemes for Your Farm</h2>
          <div className="grid grid-cols-1 gap-4">
            {matches.map((match, index) => (
              <div key={index} className="bg-white rounded-lg p-5 shadow-sm border border-green-300">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{match.scheme_name}</h3>
                <div className="space-y-1 text-sm text-gray-600">
                  <p><span className="font-medium">Eligibility Reason:</span> {match.eligibility_reason}</p>
                  <p><span className="font-medium">Benefits:</span> {match.benefits || 'Not specified'}</p>
                  {match.application_link && (
                    <p><span className="font-medium">Application Link:</span> <a href={match.application_link} target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline">{match.application_link}</a></p>
                  )}
                  {match.deadline && (
                    <p><span className="font-medium">Deadline:</span> {match.deadline.split('T')[0]}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">All Available Schemes</h2>
        {allSchemes.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No schemes available.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {allSchemes.map((scheme) => (
              <div key={scheme.id} className="border border-gray-200 rounded-lg p-5 hover:shadow-md transition-shadow">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{scheme.name}</h3>
                <div className="space-y-1 text-sm text-gray-600">
                  <p><span className="font-medium">Description:</span> {scheme.description || 'Not specified'}</p>
                  <p><span className="font-medium">Eligibility Criteria:</span> {scheme.eligibility_criteria || 'Not specified'}</p>
                  <p><span className="font-medium">Benefits:</span> {scheme.benefits || 'Not specified'}</p>
                  {scheme.application_link && (
                    <p><span className="font-medium">Application Link:</span> <a href={scheme.application_link} target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline">{scheme.application_link}</a></p>
                  )}
                  {scheme.deadline && (
                    <p><span className="font-medium">Deadline:</span> {scheme.deadline.split('T')[0]}</p>
                  )}
                  <p>
                    <span className="font-medium">Status:</span>
                    <span className={`ml-2 px-3 py-1 rounded-full text-xs font-medium ${scheme.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                      {scheme.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
