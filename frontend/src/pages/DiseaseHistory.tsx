import { useState, useEffect } from 'react';
import { RoleRoute } from '../components/RoleRoute';
import { PageLayout } from '../components/PageLayout';
import { FarmCropSelector } from '../components/FarmCropSelector';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import { ErrorMessage } from '../components/ErrorMessage';
import { Loading } from '../components/Loading';
import { EmptyState } from '../components/EmptyState';
import diseaseAPI from '../api/disease';
import type { DiagnosisResponse, DiagnosisWithTreatment } from '../types';
import { formatError } from '../utils/errorFormatter';

function DiseaseHistoryContent() {
  const [farmId, setFarmId] = useState<number | null>(null);
  const [cropId, setCropId] = useState<number | null>(null);
  const [diagnoses, setDiagnoses] = useState<DiagnosisResponse[]>([]);
  const [selectedDiagnosis, setSelectedDiagnosis] = useState<DiagnosisWithTreatment | null>(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDiagnoses();
  }, [cropId]);

  const fetchDiagnoses = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await diseaseAPI.getDiagnoses(cropId || undefined);
      setDiagnoses(response.data);
    } catch (err) {
      setError(formatError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetail = async (diagnosisId: number) => {
    try {
      setDetailLoading(true);
      setError(null);
      const response = await diseaseAPI.getDiagnosis(diagnosisId);
      setSelectedDiagnosis(response.data);
    } catch (err) {
      setError(formatError(err));
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCloseDetail = () => {
    setSelectedDiagnosis(null);
  };

  if (loading) {
    return (
      <PageLayout title="Disease Scan History">
        <Loading size="lg" />
      </PageLayout>
    );
  }

  return (
    <PageLayout title="Disease Scan History">
      {error && <ErrorMessage message={error} onDismiss={() => setError(null)} />}

      {/* Filters */}
      <Card className="p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Filter Diagnoses</h3>
        <FarmCropSelector
          farmId={farmId}
          cropId={cropId}
          onFarmChange={setFarmId}
          onCropChange={setCropId}
          includeCrop={true}
        />
      </Card>

      {/* Diagnoses List */}
      {diagnoses.length === 0 ? (
        <Card className="p-6">
          <EmptyState
            icon="📋"
            title="No diagnoses found"
            description={cropId ? 'No disease scans for this crop yet.' : 'Upload crop images to get disease diagnoses.'}
          />
        </Card>
      ) : (
        <div className="space-y-4">
          {diagnoses.map((diagnosis) => (
            <Card key={diagnosis.id} className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {diagnosis.disease_name || 'No disease detected'}
                    </h3>
                    {diagnosis.confidence_score && (
                      <span className="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                        {parseFloat(diagnosis.confidence_score).toFixed(0)}% confidence
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 mb-2">
                    Diagnosed: {new Date(diagnosis.diagnosed_at).toLocaleDateString()}
                  </p>
                  {diagnosis.symptoms && (
                    <p className="text-gray-700 line-clamp-2">{diagnosis.symptoms}</p>
                  )}
                </div>
                <Button
                  size="sm"
                  onClick={() => handleViewDetail(diagnosis.id)}
                  loading={detailLoading && selectedDiagnosis?.id === diagnosis.id}
                >
                  View Details
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Detail Modal */}
      {selectedDiagnosis && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-semibold text-gray-900">Diagnosis Details</h3>
                <button
                  onClick={handleCloseDetail}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>

              {selectedDiagnosis.low_confidence && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <span className="text-yellow-500 text-xl">⚠️</span>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm text-yellow-800 font-medium">
                        Low Confidence Detection
                      </p>
                    </div>
                  </div>
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <span className="text-sm text-gray-500">Disease:</span>
                  <p className="text-xl font-semibold text-gray-900">
                    {selectedDiagnosis.disease_name || 'No disease detected'}
                  </p>
                </div>

                {selectedDiagnosis.confidence_score && (
                  <div>
                    <span className="text-sm text-gray-500">Confidence Score:</span>
                    <p className="text-lg font-medium text-gray-900">
                      {parseFloat(selectedDiagnosis.confidence_score).toFixed(2)}%
                    </p>
                  </div>
                )}

                {selectedDiagnosis.symptoms && (
                  <div>
                    <span className="text-sm text-gray-500">Symptoms:</span>
                    <p className="text-gray-900">{selectedDiagnosis.symptoms}</p>
                  </div>
                )}

                {selectedDiagnosis.recommended_action && (
                  <div>
                    <span className="text-sm text-gray-500">Recommended Action:</span>
                    <p className="text-gray-900">{selectedDiagnosis.recommended_action}</p>
                  </div>
                )}

                {selectedDiagnosis.treatments && selectedDiagnosis.treatments.length > 0 && (
                  <div>
                    <span className="text-sm text-gray-500 block mb-2">Treatments:</span>
                    <div className="space-y-2">
                      {selectedDiagnosis.treatments.map((treatment, index) => (
                        <div
                          key={index}
                          className="bg-green-50 border border-green-200 rounded-lg p-3"
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <p className="font-medium text-gray-900">{treatment.treatment_type}</p>
                              <p className="text-sm text-gray-600 mt-1">{treatment.description}</p>
                            </div>
                            {treatment.is_organic && (
                              <span className="ml-2 text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                                Organic
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {selectedDiagnosis.disclaimer && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <p className="text-sm text-blue-800">
                      <span className="font-medium">Disclaimer:</span> {selectedDiagnosis.disclaimer}
                    </p>
                  </div>
                )}

                <div className="text-sm text-gray-500 pt-4 border-t">
                  <p>Diagnosed: {new Date(selectedDiagnosis.diagnosed_at).toLocaleString()}</p>
                </div>
              </div>

              <div className="mt-6 flex justify-end">
                <Button onClick={handleCloseDetail}>Close</Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </PageLayout>
  );
}

export default function DiseaseHistory() {
  return (
    <RoleRoute allowedRoles={['farmer']}>
      <DiseaseHistoryContent />
    </RoleRoute>
  );
}
