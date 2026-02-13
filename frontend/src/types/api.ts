export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface MessageResponse {
  message: string;
}

export interface User {
  id: string;
  email: string;
  role: "worker" | "employer" | "admin";
  first_name: string | null;
  last_name: string | null;
  phone: string | null;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface CompanyBrief {
  id: string;
  company_name: string;
  company_slug: string;
  logo_url: string | null;
  is_verified: boolean;
}

export interface CategoryBrief {
  id: string;
  name: string;
  slug: string;
  icon: string | null;
}

export interface LanguageRequirement {
  lang: string;
  level: string;
}

export interface JobOffer {
  id: string;
  title: string;
  description: string;
  canton: string;
  city: string | null;
  contract_type: string;
  salary_min: number | null;
  salary_max: number | null;
  salary_type: string;
  salary_currency: string;
  experience_min: number;
  work_permit_required: string | null;
  work_permit_sponsored: boolean;
  is_remote: string;
  languages_required: LanguageRequirement[];
  apply_via: string;
  external_url: string | null;
  status: string;
  views_count: number;
  is_featured: boolean;
  published_at: string | null;
  expires_at: string | null;
  created_at: string;
  employer: CompanyBrief | null;
  category: CategoryBrief | null;
}

export interface JobListItem {
  id: string;
  title: string;
  canton: string;
  city: string | null;
  contract_type: string;
  salary_min: number | null;
  salary_max: number | null;
  salary_type: string;
  salary_currency: string;
  is_remote: string;
  is_featured: boolean;
  published_at: string | null;
  employer: CompanyBrief | null;
  category: CategoryBrief | null;
}

export interface Application {
  id: string;
  job_offer_id: string;
  status: string;
  cover_letter: string | null;
  created_at: string;
  updated_at: string;
  job_title: string | null;
  company_name: string | null;
}

export interface WorkerProfile {
  id: string;
  user_id: string;
  canton: string | null;
  work_permit: string | null;
  experience_years: number;
  bio: string | null;
  languages: LanguageRequirement[];
  skills: string[];
  desired_salary_min: number | null;
  desired_salary_max: number | null;
  available_from: string | null;
  industry: string | null;
  has_cv: boolean;
  cv_filename: string | null;
  first_name: string | null;
  last_name: string | null;
  email: string | null;
  phone: string | null;
  created_at: string;
}

export interface EmployerProfile {
  id: string;
  user_id: string;
  company_name: string;
  company_slug: string;
  description: string | null;
  logo_url: string | null;
  website: string | null;
  industry: string | null;
  canton: string | null;
  city: string | null;
  address: string | null;
  uid_number: string | null;
  company_size: string | null;
  is_verified: boolean;
  created_at: string;
}

export interface QuotaInfo {
  plan_type: string;
  monthly_limit: number;
  used_count: number;
  remaining: number;
  period_start: string;
  period_end: string;
  days_until_reset: number;
  has_custom_limit: boolean;
}

export interface Canton {
  value: string;
  label: string;
}

export interface EmployerDashboard {
  active_jobs: number;
  total_applications: number;
  new_applications: number;
  quota_used: number;
  quota_limit: number;
  quota_reset_date: string | null;
}

export interface Candidate {
  id: string;
  worker_id: string;
  status: string;
  cover_letter: string | null;
  created_at: string;
  worker_name: string | null;
  worker_email: string | null;
  has_cv: boolean;
  employer_notes: string | null;
}

export interface AdminDashboard {
  total_users: number;
  total_workers: number;
  total_employers: number;
  total_jobs: number;
  active_jobs: number;
  pending_jobs: number;
  total_applications: number;
}

export interface AdminCategory {
  id: string;
  name: string;
  slug: string;
  icon: string | null;
  sort_order: number;
  is_active: boolean;
  parent_id: string | null;
}

export interface SystemSetting {
  id: string;
  key: string;
  value: string;
  value_type: string;
  description: string | null;
}

export interface CVInfo {
  id: string;
  original_filename: string;
  mime_type: string;
  extraction_status: "pending" | "completed" | "failed";
  extracted_name: string | null;
  extracted_email: string | null;
  extracted_phone: string | null;
  extracted_languages: { lang: string; level: string }[] | null;
}

export interface AdminCVItem {
  id: string;
  user_id: string;
  user_name: string | null;
  user_email: string | null;
  original_filename: string;
  mime_type: string;
  file_size: number;
  is_active: boolean;
  extraction_status: string;
  extracted_name: string | null;
  extracted_email: string | null;
  extracted_phone: string | null;
  extracted_languages: { lang: string; level: string }[] | null;
  created_at: string | null;
}

export interface CVStats {
  total: number;
  active: number;
  extracted: number;
  failed: number;
  pending: number;
}

// --- Admin Trends ---

export interface DailyStats {
  date: string;
  new_users: number;
  new_jobs: number;
  new_applications: number;
}

export interface PeriodComparison {
  current: number;
  previous: number;
  pct_change: number;
}

export interface TrendComparisons {
  users: { "7d": PeriodComparison; "14d": PeriodComparison; "30d": PeriodComparison };
  jobs: { "7d": PeriodComparison; "14d": PeriodComparison; "30d": PeriodComparison };
  applications: { "7d": PeriodComparison; "14d": PeriodComparison; "30d": PeriodComparison };
}

export interface TrendsResponse {
  daily: DailyStats[];
  comparisons: TrendComparisons;
  total_views: number;
}

// --- CV Analysis ---

export interface CVAnalysis {
  strengths: string[];
  weaknesses: string[];
  tips: string[];
  score: number;
}
