// User Types
export type UserRole = 'farmer' | 'buyer' | 'officer' | 'admin';

export interface UserCreate {
  email: string;
  full_name: string;
  phone?: string | null;
  role: UserRole;
  password: string;
}

export interface UserResponse {
  email: string;
  full_name: string;
  phone?: string | null;
  role: UserRole;
  id: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

// Farm Types
export interface FarmCreate {
  name: string;
  location?: string | null;
  latitude?: number | string | null;
  longitude?: number | string | null;
  area_hectares?: number | string | null;
  soil_type?: string | null;
}

export interface FarmResponse {
  name: string;
  location?: string | null;
  latitude?: string | null;
  longitude?: string | null;
  area_hectares?: string | null;
  soil_type?: string | null;
  id: number;
  owner_id: number;
  created_at: string;
  updated_at: string;
}

// Crop Types
export interface CropCreate {
  farm_id: number;
  name: string;
  variety?: string | null;
  planting_date?: string | null;
  expected_harvest_date?: string | null;
  area_hectares?: number | string | null;
  status?: string;
}

export interface CropResponse {
  farm_id: number;
  name: string;
  variety?: string | null;
  planting_date?: string | null;
  expected_harvest_date?: string | null;
  area_hectares?: string | null;
  status: string;
  id: number;
  created_at: string;
  updated_at: string;
}

// Disease Diagnosis Types
export interface DiagnosisCreate {
  crop_id: number;
  file: File;
  consent?: boolean;
}

export interface DiagnosisResponse {
  crop_id: number;
  disease_name?: string | null;
  confidence_score?: string | null;
  symptoms?: string | null;
  recommended_action?: string | null;
  image_path?: string | null;
  consent_record_id?: number | null;
  id: number;
  diagnosed_at: string;
  created_at: string;
  updated_at: string;
}

export interface TreatmentDetail {
  treatment_type: string;
  description: string;
  is_organic: boolean;
}

export interface DiagnosisWithTreatment extends DiagnosisResponse {
  low_confidence: boolean;
  treatments: TreatmentDetail[];
  disclaimer: string;
}

// Soil Health Types
export interface SoilRecordCreate {
  farm_id: number;
  ph_level?: number | string | null;
  nitrogen?: number | string | null;
  phosphorus?: number | string | null;
  potassium?: number | string | null;
  organic_matter?: number | string | null;
  moisture?: number | string | null;
  source?: string;
}

export interface SoilRecordResponse {
  farm_id: number;
  ph_level?: string | null;
  nitrogen?: string | null;
  phosphorus?: string | null;
  potassium?: string | null;
  organic_matter?: string | null;
  moisture?: string | null;
  source: string;
  id: number;
  test_date: string;
  created_at: string;
  updated_at: string;
}

export interface SoilAnalysis {
  ph_status: string;
  ph_explanation: string;
  nitrogen_status: string;
  nitrogen_explanation: string;
  phosphorus_status: string;
  phosphorus_explanation: string;
  potassium_status: string;
  potassium_explanation: string;
  organic_matter_status?: string;
  organic_matter_explanation?: string;
  moisture_status?: string;
  moisture_explanation?: string;
}

// Irrigation Types
export interface IrrigationScheduleCreate {
  farm_id: number;
  crop_id?: number | null;
  area_hectares?: number | string | null;
  soil_type?: string | null;
  crop_stage?: string | null;
  soil_moisture_percent?: number | string | null;
  rainfall_mm?: number | string | null;
  temperature_c?: number | string | null;
  scheduled_date: string;
  duration_hours?: number | string | null;
  water_amount_liters?: number | string | null;
  status?: string;
  notes?: string | null;
}

export interface IrrigationScheduleResponse {
  farm_id: number;
  crop_id?: number | null;
  area_hectares?: string | null;
  soil_type?: string | null;
  crop_stage?: string | null;
  soil_moisture_percent?: string | null;
  rainfall_mm?: string | null;
  temperature_c?: string | null;
  weather_source?: string | null;
  scheduled_date: string;
  duration_hours?: string | null;
  water_amount_liters?: string | null;
  status: string;
  notes?: string | null;
  id: number;
  created_at: string;
  updated_at: string;
}

export interface IrrigationScheduleUpdate {
  scheduled_date?: string | null;
  duration_hours?: number | string | null;
  water_amount_liters?: number | string | null;
  status?: string | null;
  notes?: string | null;
}

// Yield Prediction Types
export interface YieldPredictionCreate {
  farm_id: number;
  crop_id: number;
  land_size_acres: number | string;
  planting_date: string;
  ph_level?: number | string | null;
  nitrogen?: number | string | null;
  phosphorus?: number | string | null;
  potassium?: number | string | null;
  soil_moisture_percent?: number | string | null;
  rainfall_mm?: number | string | null;
  irrigation_mm?: number | string | null;
  temperature_c?: number | string | null;
}

export interface YieldPredictionResponse {
  farm_id: number;
  crop_id: number;
  land_size_acres: string;
  planting_date: string;
  id: number;
  predicted_yield_low: string;
  predicted_yield_expected: string;
  predicted_yield_high: string;
  confidence_label: string;
  harvest_window_start?: string | null;
  harvest_window_end?: string | null;
  version: number;
  input_snapshot?: Record<string, unknown> | null;
  model_version?: string | null;
  created_at: string;
}

// Alerts Types
export interface OutbreakAlertCreate {
  disease_name: string;
  region_description: string;
  center_latitude: number | string;
  center_longitude: number | string;
  radius_km: number | string;
  severity?: string;
  preventive_measures?: string | null;
}

export interface OutbreakAlertResponse {
  disease_name: string;
  region_description: string;
  center_latitude: string;
  center_longitude: string;
  radius_km: string;
  severity: string;
  preventive_measures?: string | null;
  id: number;
  case_count: number;
  is_active: boolean;
  retracted_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface OutbreakAlertListResponse {
  id: number;
  disease_name: string;
  region_description: string;
  severity: string;
  case_count: number;
  is_active: boolean;
  created_at: string;
}

// Marketplace Types
export interface ListingCreate {
  crop_name: string;
  quantity_quintals: number | string;
  price_per_quintal: number | string;
  unit?: string;
  location?: string | null;
  latitude?: number | string | null;
  longitude?: number | string | null;
  description?: string | null;
  file?: File | null;
}

export interface ListingResponse {
  crop_name: string;
  quantity_quintals: string;
  price_per_quintal: string;
  unit: string;
  location?: string | null;
  latitude?: string | null;
  longitude?: string | null;
  description?: string | null;
  id: number;
  seller_id: number;
  status: string;
  photo_path?: string | null;
  market_price_benchmark?: string | null;
  price_label?: 'below' | 'near' | 'above' | null;
  market_price_updated?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ListingUpdate {
  status?: string | null;
  price_per_quintal?: number | string | null;
  quantity_quintals?: number | string | null;
  description?: string | null;
}

export interface MessageCreate {
  content: string;
}

export interface MessageResponse {
  content: string;
  id: number;
  listing_id: number;
  sender_id: number;
  created_at: string;
}

// Transaction Types
export interface TransactionCreate {
  listing_id?: number | null;
  buyer_id?: number | null;
  seller_id?: number | null;
  quantity_quintals: number | string;
  total_amount: number | string;
  razorpay_order_id?: string | null;
  razorpay_payment_id?: string | null;
  status?: string;
}

export interface TransactionResponse {
  listing_id?: number | null;
  buyer_id?: number | null;
  seller_id?: number | null;
  quantity_quintals: string;
  total_amount: string;
  razorpay_order_id?: string | null;
  razorpay_payment_id?: string | null;
  status: string;
  id: number;
  transaction_date: string;
  created_at: string;
  updated_at: string;
}

export interface TransactionUpdate {
  status: string;
}

// Finance Types
export interface FinanceEntryCreate {
  farm_id: number;
  entry_type: string;
  category: string;
  amount: number | string;
  date: string;
  notes?: string | null;
}

export interface FinanceEntryResponse {
  farm_id: number;
  entry_type: string;
  category: string;
  amount: string;
  date: string;
  notes?: string | null;
  id: number;
  created_at: string;
  updated_at: string;
}

export interface FinanceSummaryResponse {
  farm_id: number;
  total_income: string;
  total_expenses: string;
  net_profit: string;
  category_breakdown: Record<string, unknown>;
  monthly_breakdown: Record<string, unknown>;
}

// Schemes Types
export interface SchemeMatchRequest {
  farm_id: number;
  crop_name?: string | null;
  state?: string | null;
}

export interface SchemeMatchResponse {
  scheme_id: number;
  scheme_name: string;
  eligibility_reason: string;
  benefits?: string | null;
  application_link?: string | null;
  deadline?: string | null;
}

export interface SchemeResponse {
  name: string;
  description?: string | null;
  eligibility_criteria?: string | null;
  min_land_hectares?: string | null;
  max_land_hectares?: string | null;
  eligible_crops?: string | null;
  eligible_states?: string | null;
  benefits?: string | null;
  application_link?: string | null;
  deadline?: string | null;
  id: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Admin Types
export interface AdminDashboardResponse {
  total_users: number;
  users_by_role: Record<string, unknown>;
  total_diagnoses: number;
  low_confidence_diagnoses: number;
  top_diseases: unknown[];
  active_alerts: number;
  total_listings: number;
  open_listings: number;
  closed_listings: number;
  total_transaction_volume: string;
  total_farms: number;
}

export interface SystemConfigResponse {
  id: number;
  config_key: string;
  config_value?: string | null;
  description?: string | null;
  updated_at: string;
}

export interface SystemConfigUpdate {
  config_value: string;
  description?: string | null;
}

export interface AuditLogResponse {
  id: number;
  user_id?: number | null;
  action: string;
  entity_type?: string | null;
  entity_id?: number | null;
  details?: string | null;
  ip_address?: string | null;
  created_at: string;
}

// Error Types
export interface ValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
  input?: unknown;
}

export interface HTTPValidationError {
  detail: ValidationError[];
}
