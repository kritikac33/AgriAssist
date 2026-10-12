import { useState, useEffect } from 'react';
import { RoleRoute } from '../components/RoleRoute';
import { PageLayout } from '../components/PageLayout';
import { Button } from '../components/Button';
import { Card } from '../components/Card';
import { ErrorMessage } from '../components/ErrorMessage';
import { Loading } from '../components/Loading';
import { EmptyState } from '../components/EmptyState';
import farmAPI from '../api/farm';
import cropAPI from '../api/crop';
import type { FarmResponse, CropResponse, FarmCreate, CropCreate } from '../types';
import { formatError } from '../utils/errorFormatter';

const CROP_TYPES = [
  'rice', 'wheat', 'cotton', 'tomato', 'sugarcane', 'soybean', 'onion',
  'grape', 'maize', 'groundnut', 'chilli', 'potato', 'banana', 'mango', 'turmeric'
];

function FarmsAndCropsContent() {
  const [farms, setFarms] = useState<FarmResponse[]>([]);
  const [crops, setCrops] = useState<CropResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showFarmForm, setShowFarmForm] = useState(false);
  const [showCropForm, setShowCropForm] = useState(false);

  // Farm form state
  const [farmForm, setFarmForm] = useState<FarmCreate>({
    name: '',
    location: '',
    latitude: null,
    longitude: null,
    area_hectares: null,
    soil_type: '',
  });

  // Crop form state
  const [cropForm, setCropForm] = useState<CropCreate>({
    farm_id: 0,
    name: '',
    variety: '',
    planting_date: '',
    expected_harvest_date: '',
    area_hectares: null,
    status: 'active',
  });

  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [farmsRes, cropsRes] = await Promise.all([
        farmAPI.getFarms(),
        cropAPI.getCrops(),
      ]);
      setFarms(farmsRes.data);
      setCrops(cropsRes.data);
    } catch (err) {
      setError(formatError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleAddFarm = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      await farmAPI.createFarm(farmForm);
      setShowFarmForm(false);
      setFarmForm({
        name: '',
        location: '',
        latitude: null,
        longitude: null,
        area_hectares: null,
        soil_type: '',
      });
      await fetchData();
    } catch (err) {
      setError(formatError(err));
    } finally {
      setSubmitting(false);
    }
  };

  const handleAddCrop = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      await cropAPI.createCrop(cropForm);
      setShowCropForm(false);
      setCropForm({
        farm_id: 0,
        name: '',
        variety: '',
        planting_date: '',
        expected_harvest_date: '',
        area_hectares: null,
        status: 'active',
      });
      await fetchData();
    } catch (err) {
      setError(formatError(err));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <PageLayout title="My Farms & Crops">
        <Loading size="lg" />
      </PageLayout>
    );
  }

  // Sort farms by creation order
  const sortedFarms = [...farms].sort((a, b) => a.id - b.id);

  return (
    <PageLayout title="My Farms & Crops">
      {error && <ErrorMessage message={error} onDismiss={() => setError(null)} />}

      {/* Add Farm Button */}
      <div className="mb-6">
        <Button onClick={() => setShowFarmForm(!showFarmForm)}>
          {showFarmForm ? 'Cancel' : '+ Add New Farm'}
        </Button>
      </div>

      {/* Add Farm Form */}
      {showFarmForm && (
        <Card className="p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Add New Farm</h3>
          <form onSubmit={handleAddFarm} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="farm-name" className="block text-sm font-medium text-gray-700 mb-1">
                  Farm Name *
                </label>
                <input
                  type="text"
                  id="farm-name"
                  value={farmForm.name}
                  onChange={(e) => setFarmForm({ ...farmForm, name: e.target.value })}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div>
                <label htmlFor="farm-location" className="block text-sm font-medium text-gray-700 mb-1">
                  Location
                </label>
                <input
                  type="text"
                  id="farm-location"
                  value={farmForm.location || ''}
                  onChange={(e) => setFarmForm({ ...farmForm, location: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div>
                <label htmlFor="farm-latitude" className="block text-sm font-medium text-gray-700 mb-1">
                  Latitude
                </label>
                <input
                  type="number"
                  step="any"
                  id="farm-latitude"
                  value={farmForm.latitude || ''}
                  onChange={(e) => setFarmForm({ ...farmForm, latitude: e.target.value ? Number(e.target.value) : null })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div>
                <label htmlFor="farm-longitude" className="block text-sm font-medium text-gray-700 mb-1">
                  Longitude
                </label>
                <input
                  type="number"
                  step="any"
                  id="farm-longitude"
                  value={farmForm.longitude || ''}
                  onChange={(e) => setFarmForm({ ...farmForm, longitude: e.target.value ? Number(e.target.value) : null })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div>
                <label htmlFor="farm-area" className="block text-sm font-medium text-gray-700 mb-1">
                  Area (hectares)
                </label>
                <input
                  type="number"
                  step="any"
                  id="farm-area"
                  value={farmForm.area_hectares || ''}
                  onChange={(e) => setFarmForm({ ...farmForm, area_hectares: e.target.value ? Number(e.target.value) : null })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div>
                <label htmlFor="farm-soil" className="block text-sm font-medium text-gray-700 mb-1">
                  Soil Type
                </label>
                <input
                  type="text"
                  id="farm-soil"
                  value={farmForm.soil_type || ''}
                  onChange={(e) => setFarmForm({ ...farmForm, soil_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
            </div>

            <div className="flex space-x-3">
              <Button type="submit" loading={submitting}>
                Add Farm
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={() => setShowFarmForm(false)}
              >
                Cancel
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* Farms List */}
      {sortedFarms.length === 0 ? (
        <EmptyState
          icon="🌾"
          title="No farms yet"
          description="Add your first farm to get started with managing your crops."
        />
      ) : (
        <div className="space-y-6">
          {sortedFarms.map((farm, index) => {
            const farmCrops = crops.filter((c) => c.farm_id === farm.id);
            return (
              <Card key={farm.id} className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-xl font-semibold text-gray-900">
                      Farm #{index + 1} — {farm.name}
                    </h3>
                    {farm.location && (
                      <p className="text-gray-600 text-sm mt-1">📍 {farm.location}</p>
                    )}
                  </div>
                  <Button
                    size="sm"
                    onClick={() => {
                      setCropForm({ ...cropForm, farm_id: farm.id });
                      setShowCropForm(true);
                    }}
                  >
                    + Add Crop
                  </Button>
                </div>

                {/* Farm Details */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 text-sm">
                  {farm.area_hectares && (
                    <div>
                      <span className="text-gray-500">Area:</span>{' '}
                      <span className="font-medium">{farm.area_hectares} ha</span>
                    </div>
                  )}
                  {farm.soil_type && (
                    <div>
                      <span className="text-gray-500">Soil:</span>{' '}
                      <span className="font-medium">{farm.soil_type}</span>
                    </div>
                  )}
                  {farm.latitude && farm.longitude && (
                    <div>
                      <span className="text-gray-500">Coordinates:</span>{' '}
                      <span className="font-medium">
                        {farm.latitude}, {farm.longitude}
                      </span>
                    </div>
                  )}
                </div>

                {/* Add Crop Form for this farm */}
                {showCropForm && cropForm.farm_id === farm.id && (
                  <div className="bg-gray-50 rounded-lg p-4 mb-4">
                    <h4 className="text-md font-semibold text-gray-900 mb-3">Add Crop to {farm.name}</h4>
                    <form onSubmit={handleAddCrop} className="space-y-3">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div>
                          <label htmlFor="crop-name" className="block text-sm font-medium text-gray-700 mb-1">
                            Crop Type *
                          </label>
                          <select
                            id="crop-name"
                            value={cropForm.name}
                            onChange={(e) => setCropForm({ ...cropForm, name: e.target.value })}
                            required
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                          >
                            <option value="">Select crop type</option>
                            {CROP_TYPES.map((type) => (
                              <option key={type} value={type}>
                                {type.charAt(0).toUpperCase() + type.slice(1)}
                              </option>
                            ))}
                          </select>
                        </div>

                        <div>
                          <label htmlFor="crop-variety" className="block text-sm font-medium text-gray-700 mb-1">
                            Variety
                          </label>
                          <input
                            type="text"
                            id="crop-variety"
                            value={cropForm.variety || ''}
                            onChange={(e) => setCropForm({ ...cropForm, variety: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                          />
                        </div>

                        <div>
                          <label htmlFor="crop-planting" className="block text-sm font-medium text-gray-700 mb-1">
                            Planting Date
                          </label>
                          <input
                            type="date"
                            id="crop-planting"
                            value={cropForm.planting_date || ''}
                            onChange={(e) => setCropForm({ ...cropForm, planting_date: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                          />
                        </div>

                        <div>
                          <label htmlFor="crop-harvest" className="block text-sm font-medium text-gray-700 mb-1">
                            Expected Harvest Date
                          </label>
                          <input
                            type="date"
                            id="crop-harvest"
                            value={cropForm.expected_harvest_date || ''}
                            onChange={(e) => setCropForm({ ...cropForm, expected_harvest_date: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                          />
                        </div>

                        <div>
                          <label htmlFor="crop-area" className="block text-sm font-medium text-gray-700 mb-1">
                            Area (hectares)
                          </label>
                          <input
                            type="number"
                            step="any"
                            id="crop-area"
                            value={cropForm.area_hectares || ''}
                            onChange={(e) => setCropForm({ ...cropForm, area_hectares: e.target.value ? Number(e.target.value) : null })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                          />
                        </div>

                        <div>
                          <label htmlFor="crop-status" className="block text-sm font-medium text-gray-700 mb-1">
                            Status
                          </label>
                          <select
                            id="crop-status"
                            value={cropForm.status}
                            onChange={(e) => setCropForm({ ...cropForm, status: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                          >
                            <option value="active">Active</option>
                            <option value="harvested">Harvested</option>
                            <option value="planned">Planned</option>
                          </select>
                        </div>
                      </div>

                      <div className="flex space-x-3">
                        <Button type="submit" size="sm" loading={submitting}>
                          Add Crop
                        </Button>
                        <Button
                          type="button"
                          size="sm"
                          variant="secondary"
                          onClick={() => setShowCropForm(false)}
                        >
                          Cancel
                        </Button>
                      </div>
                    </form>
                  </div>
                )}

                {/* Crops List */}
                {farmCrops.length === 0 ? (
                  <p className="text-gray-500 text-sm">No crops added yet.</p>
                ) : (
                  <div className="space-y-2">
                    {farmCrops.map((crop) => (
                      <div
                        key={crop.id}
                        className="bg-green-50 border border-green-200 rounded-lg p-3 flex items-center justify-between"
                      >
                        <div>
                          <span className="font-medium text-gray-900">
                            {crop.name.charAt(0).toUpperCase() + crop.name.slice(1)}
                          </span>
                          {crop.variety && <span className="text-gray-600 ml-2">({crop.variety})</span>}
                          <span className="ml-2 text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                            {crop.status}
                          </span>
                        </div>
                        {crop.area_hectares && (
                          <span className="text-sm text-gray-600">{crop.area_hectares} ha</span>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </PageLayout>
  );
}

export default function FarmsAndCrops() {
  return (
    <RoleRoute allowedRoles={['farmer']}>
      <FarmsAndCropsContent />
    </RoleRoute>
  );
}
