import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageLayout } from '../components/PageLayout';
import { FarmCropSelector } from '../components/FarmCropSelector';
import { Button } from '../components/Button';
import { Card } from '../components/Card';
import { ErrorMessage } from '../components/ErrorMessage';
import { Loading } from '../components/Loading';
import { EmptyState } from '../components/EmptyState';
import diseaseAPI from '../api/disease';
import type { DiagnosisWithTreatment } from '../types';
import { formatError } from '../utils/errorFormatter';

function DiseaseScanContent() {
  const navigate = useNavigate();
  const [farmId, setFarmId] = useState<number | null>(null);
  const [cropId, setCropId] = useState<number | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [consent, setConsent] = useState(false);
  const [diagnosis, setDiagnosis] = useState<DiagnosisWithTreatment | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);
      
      // Create preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result as string);
      };
      reader.readAsDataURL(selectedFile);
    }
  };

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!cropId || !file) {
      setError('Please select a crop and upload an image');
      return;
    }

    setLoading(true);
    setError(null);
    setDiagnosis(null);

    try {
      const response = await diseaseAPI.createDiagnosis(cropId, file, consent);
      setDiagnosis(response.data);
    } catch (err) {
      setError(formatError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setPreview(null);
    setConsent(false);
    setDiagnosis(null);
    setError(null);
  };

  return (
    <PageLayout title="Disease Scan">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Column - Input Form */}
        <div>
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Scan Crop for Disease</h3>
            
            {error && <ErrorMessage message={error} onDismiss={() => setError(null)} />}

            <form onSubmit={handleScan} className="space-y-6">
              <FarmCropSelector
                farmId={farmId}
                cropId={cropId}
                onFarmChange={setFarmId}
                onCropChange={setCropId}
                disabled={loading}
              />

              <div>
                <label htmlFor="image-upload" className="block text-sm font-medium text-gray-700 mb-2">
                  Upload Leaf Image *
                </label>
                <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-lg hover:border-primary-500 transition-colors">
                  <div className="space-y-1 text-center">
                    {preview ? (
                      <div className="relative">
                        <img
                          src={preview}
                          alt="Preview"
                          className="max-h-64 mx-auto rounded-lg"
                        />
                        <button
                          type="button"
                          onClick={handleReset}
                          className="mt-2 text-sm text-red-600 hover:text-red-700"
                        >
                          Remove image
                        </button>
                      </div>
                    ) : (
                      <>
                        <svg
                          className="mx-auto h-12 w-12 text-gray-400"
                          stroke="currentColor"
                          fill="none"
                          viewBox="0 0 48 48"
                        >
                          <path
                            d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                            strokeWidth={2}
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                        </svg>
                        <div className="flex text-sm text-gray-600">
                          <label
                            htmlFor="image-upload"
                            className="relative cursor-pointer bg-white rounded-md font-medium text-primary-600 hover:text-primary-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-primary-500"
                          >
                            <span>Upload a file</span>
                            <input
                              id="image-upload"
                              type="file"
                              accept="image/*"
                              onChange={handleFileChange}
                              className="sr-only"
                              required
                            />
                          </label>
                          <p className="pl-1">or drag and drop</p>
                        </div>
                        <p className="text-xs text-gray-500">PNG, JPG, GIF up to 10MB</p>
                      </>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex items-start">
                <div className="flex items-center h-5">
                  <input
                    id="consent"
                    type="checkbox"
                    checked={consent}
                    onChange={(e) => setConsent(e.target.checked)}
                    className="focus:ring-primary-500 h-4 w-4 text-primary-600 border-gray-300 rounded"
                  />
                </div>
                <div className="ml-3 text-sm">
                  <label htmlFor="consent" className="font-medium text-gray-700">
                    Consent to reuse image
                  </label>
                  <p className="text-gray-500">
                    Allow this image to be used for training the disease detection model (optional)
                  </p>
                </div>
              </div>

              <div className="flex space-x-3">
                <Button type="submit" loading={loading} disabled={!cropId || !file}>
                  Scan for Disease
                </Button>
                {diagnosis && (
                  <Button type="button" variant="secondary" onClick={handleReset}>
                    New Scan
                  </Button>
                )}
              </div>
            </form>
          </Card>

          <div className="mt-6">
            <Button variant="outline" onClick={() => navigate('/disease-history')}>
              View Scan History
            </Button>
          </div>
        </div>

        {/* Right Column - Results */}
        <div>
          {loading && (
            <Card className="p-6">
              <Loading size="lg" />
              <p className="text-center text-gray-600 mt-4">Analyzing image...</p>
            </Card>
          )}

          {diagnosis && (
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Diagnosis Results</h3>

              {diagnosis.low_confidence && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <span className="text-yellow-500 text-xl">⚠️</span>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm text-yellow-800 font-medium">
                        Low Confidence Detection
                      </p>
                      <p className="text-sm text-yellow-700 mt-1">
                        The AI model is not confident in this diagnosis. Please consult with a local agricultural expert for confirmation.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <span className="text-sm text-gray-500">Disease:</span>
                  <p className="text-xl font-semibold text-gray-900">
                    {diagnosis.disease_name || 'No disease detected'}
                  </p>
                </div>

                {diagnosis.confidence_score && (
                  <div>
                    <span className="text-sm text-gray-500">Confidence Score:</span>
                    <p className="text-lg font-medium text-gray-900">
                      {parseFloat(diagnosis.confidence_score).toFixed(2)}%
                    </p>
                  </div>
                )}

                {diagnosis.symptoms && (
                  <div>
                    <span className="text-sm text-gray-500">Symptoms:</span>
                    <p className="text-gray-900">{diagnosis.symptoms}</p>
                  </div>
                )}

                {diagnosis.recommended_action && (
                  <div>
                    <span className="text-sm text-gray-500">Recommended Action:</span>
                    <p className="text-gray-900">{diagnosis.recommended_action}</p>
                  </div>
                )}

                {diagnosis.treatments && diagnosis.treatments.length > 0 && (
                  <div>
                    <span className="text-sm text-gray-500 block mb-2">Treatments:</span>
                    <div className="space-y-2">
                      {diagnosis.treatments.map((treatment, index) => (
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

                {diagnosis.disclaimer && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <p className="text-sm text-blue-800">
                      <span className="font-medium">Disclaimer:</span> {diagnosis.disclaimer}
                    </p>
                  </div>
                )}
              </div>
            </Card>
          )}

          {!loading && !diagnosis && (
            <Card className="p-6">
              <EmptyState
                icon="🔬"
                title="No diagnosis yet"
                description="Upload a crop image to get an AI-powered disease diagnosis."
              />
            </Card>
          )}
        </div>
      </div>
    </PageLayout>
  );
}

export default function DiseaseScan() {
  return <DiseaseScanContent />;
}
