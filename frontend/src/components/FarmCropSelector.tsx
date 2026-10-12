import { useState, useEffect } from 'react';
import farmAPI from '../api/farm';
import cropAPI from '../api/crop';
import type { FarmResponse, CropResponse } from '../types';
import { Loading } from './Loading';
import { formatApiError } from '../utils/error';

interface FarmCropSelectorProps {
  farmId: number | null;
  cropId: number | null;
  onFarmChange: (farmId: number | null) => void;
  onCropChange: (cropId: number | null) => void;
  includeCrop?: boolean;
  disabled?: boolean;
}

export function FarmCropSelector({
  farmId,
  cropId,
  onFarmChange,
  onCropChange,
  includeCrop = true,
  disabled = false,
}: FarmCropSelectorProps) {
  const [farms, setFarms] = useState<FarmResponse[]>([]);
  const [crops, setCrops] = useState<CropResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchFarms();
  }, []);

  useEffect(() => {
    if (farmId && includeCrop) {
      fetchCrops(farmId);
    } else {
      setCrops([]);
      onCropChange(null);
    }
  }, [farmId, includeCrop]);

  const fetchFarms = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await farmAPI.getFarms();
      setFarms(response.data);
      
      // Auto-select first farm if available and none selected
      if (response.data.length > 0 && !farmId) {
        onFarmChange(response.data[0].id);
      }
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  };

  const fetchCrops = async (selectedFarmId: number) => {
    try {
      const response = await cropAPI.getCrops(selectedFarmId);
      setCrops(response.data);
      
      // Auto-select first crop if available and none selected
      if (response.data.length > 0 && !cropId) {
        onCropChange(response.data[0].id);
      }
    } catch (err) {
      setError(formatApiError(err));
    }
  };

  if (loading) {
    return <Loading />;
  }

  if (error) {
    return (
      <div className="text-red-600 text-sm">{error}</div>
    );
  }

  if (farms.length === 0) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <p className="text-yellow-800 text-sm mb-2">
          You don't have any farms yet.
        </p>
        <a
          href="/farms-and-crops"
          className="text-primary-600 hover:text-primary-700 font-medium text-sm"
        >
          Add your first farm →
        </a>
      </div>
    );
  }

  // Sort farms by creation order (by id) for numbering
  const sortedFarms = [...farms].sort((a, b) => a.id - b.id);

  return (
    <div className="space-y-4">
      <div>
        <label htmlFor="farm-select" className="block text-sm font-medium text-gray-700 mb-1">
          Farm
        </label>
        <select
          id="farm-select"
          value={farmId || ''}
          onChange={(e) => onFarmChange(e.target.value ? Number(e.target.value) : null)}
          disabled={disabled}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
        >
          <option value="">Select a farm</option>
          {sortedFarms.map((farm, index) => (
            <option key={farm.id} value={farm.id}>
              Farm #{index + 1} — {farm.name}
            </option>
          ))}
        </select>
      </div>

      {includeCrop && farmId && (
        <div>
          <label htmlFor="crop-select" className="block text-sm font-medium text-gray-700 mb-1">
            Crop
          </label>
          <select
            id="crop-select"
            value={cropId || ''}
            onChange={(e) => onCropChange(e.target.value ? Number(e.target.value) : null)}
            disabled={disabled}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            <option value="">Select a crop</option>
            {crops.map((crop) => (
              <option key={crop.id} value={crop.id}>
                {crop.name} {crop.variety ? `(${crop.variety})` : ''}
              </option>
            ))}
          </select>
          {crops.length === 0 && (
            <p className="text-sm text-gray-500 mt-1">
              No crops found for this farm. Add crops in the Farms & Crops page.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
