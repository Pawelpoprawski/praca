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
  car_required: boolean;
  driving_license_required: boolean;
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
  recruiter_type: string | null;
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
  recruiter_type: string | null;
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
  total_views: number;
  total_clicks: number;
  clicks_by_type: Record<string, number>;
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

// --- Employer Charts ---

export interface ApplicationOverTime {
  date: string;
  count: number;
}

export interface TopJob {
  job_title: string;
  views: number;
  applications: number;
}

export interface ApplicationStatusBreakdown {
  pending: number;
  reviewed: number;
  accepted: number;
  rejected: number;
}

export interface MonthlySummary {
  total_jobs: number;
  total_applications: number;
  active_jobs: number;
}

export interface EmployerChartsData {
  applications_over_time: ApplicationOverTime[];
  top_jobs: TopJob[];
  application_status_breakdown: ApplicationStatusBreakdown;
  monthly_summary: MonthlySummary;
}

// --- CV Analysis ---

export interface CVAnalysis {
  strengths: string[];
  weaknesses: string[];
  tips: string[];
  score: number;
}

// --- Notifications ---

export interface Notification {
  id: string;
  user_id: string;
  type: string;
  title: string;
  message: string;
  is_read: boolean;
  related_entity_type: string | null;
  related_entity_id: string | null;
  created_at: string;
}

export interface UnreadCount {
  unread_count: number;
}

// --- Saved Jobs ---

export interface SavedJob {
  id: string;
  job_offer_id: string;
  created_at: string;
  job: JobListItem | null;
}

export interface SavedJobCheck {
  is_saved: boolean;
}

// --- Reviews ---

export interface Review {
  id: string;
  employer_id: string;
  rating: number;
  comment: string;
  status: string;
  worker_name: string;
  created_at: string;
}

export interface ReviewListResponse {
  data: Review[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
  avg_rating: number | null;
  total_reviews: number;
}

export interface AdminReview {
  id: string;
  employer_id: string;
  worker_user_id: string;
  rating: number;
  comment: string;
  status: string;
  worker_name: string;
  company_name: string;
  created_at: string;
  updated_at: string;
}

// --- Job Alerts ---

export interface JobAlertFilters {
  category_id: string | null;
  canton: string | null;
  min_salary: number | null;
  max_salary: number | null;
  keywords: string | null;
  work_mode: string | null;
  permit_sponsorship: boolean | null;
}

export interface JobAlert {
  id: string;
  name: string;
  filters: JobAlertFilters;
  is_active: boolean;
  frequency: string;
  last_sent_at: string | null;
  created_at: string;
}

export interface JobAlertList {
  alerts: JobAlert[];
  count: number;
  max_alerts: number;
}

// --- CV Review (AI) ---

export interface CVReviewAnalysis {
  overall_score: number;
  summary: string;
  strengths: string[];
  improvements: string[];
  missing: string[];
  tips: string[];
}

export interface CVReviewResponse {
  id: string;
  email: string | null;
  cv_filename: string;
  cv_original_filename: string;
  overall_score: number | null;
  analysis: CVReviewAnalysis | null;
  status: string;
  previous_score: number | null;
  created_at: string | null;
}

export interface CVDatabaseListItem {
  id: string;
  full_name: string | null;
  email: string | null;
  phone: string | null;
  job_preferences: string | null;
  available_from: string | null;
  preferred_cantons: string[] | null;
  expected_salary_min: number | null;
  expected_salary_max: number | null;
  work_mode: string | null;
  languages: { language: string; level: string }[] | null;
  driving_license: string[] | null;
  has_car: boolean;
  overall_score: number | null;
  is_active: boolean;
  extraction_status: string | null;
  match_ready: boolean;
  category_slugs: string[] | null;
  skills: string[] | null;
  location: string | null;
  experience_years: number | null;
  created_at: string | null;
}

export interface CVDatabaseDetail extends CVDatabaseListItem {
  cv_text: string | null;
  cv_file_path: string | null;
  extracted_data: Record<string, unknown> | null;
  additional_notes: string | null;
  consent_given: boolean;
  cv_review_id: string | null;
  cv_file_id: string | null;
  user_id: string | null;
  updated_at: string | null;
  analysis: CVReviewAnalysis | null;
  extraction_version: number | null;
  experience_entries: { position?: string; company?: string; from?: string; to?: string; months?: number }[] | null;
  ai_keywords: string | null;
  education: { degree?: string; institution?: string; year?: string }[] | null;
}

// --- Activity Logs ---

export interface ActivityLogEntry {
  id: string;
  event_type: string;
  entity_type: string | null;
  entity_id: string | null;
  summary: string;
  details: Record<string, unknown> | null;
  created_at: string | null;
}

// --- Extraction Status ---

export interface ExtractionCVStatus {
  pending: number;
  processing: number;
  completed: number;
  failed: number;
  total: number;
}

export interface ExtractionJobStatus {
  pending: number;
  extracted: number;
  total: number;
}

export interface ExtractionStatus {
  cv: ExtractionCVStatus;
  jobs: ExtractionJobStatus;
}

export interface ExtractionTriggerResult {
  triggered: boolean;
  pending_count: number;
  message?: string;
}

// --- Admin Jobs Browser ---

export interface AdminJobBrowserItem {
  id: string;
  title: string;
  company_name: string | null;
  canton: string;
  city: string | null;
  category_name: string | null;
  category_id: string | null;
  ai_keywords: string | null;
  ai_extracted: boolean;
  source_name: string | null;
  salary_min: number | null;
  salary_max: number | null;
  salary_type: string;
  status: string;
  views_count: number;
  created_at: string | null;
}

// --- Admin Companies (Firmy) ---

export interface AdminCompanyQuota {
  id?: string;
  monthly_limit: number | null;
  used_count: number;
  custom_limit: number | null;
  plan_type: string;
  period_start: string | null;
  period_end: string | null;
}

export interface AdminCompanyListItem {
  id: string;
  company_name: string;
  company_slug: string;
  logo_url: string | null;
  is_verified: boolean;
  created_at: string | null;
  active_postings: number;
  quota: AdminCompanyQuota | null;
}

export interface AdminCompanyRecentJob {
  id: string;
  title: string;
  status: string;
  views_count: number;
  is_featured: boolean;
  created_at: string | null;
  published_at: string | null;
}

export interface AdminCompanyDetail {
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
  created_at: string | null;
  user_email: string | null;
  user_name: string | null;
  active_postings: number;
  quota: AdminCompanyQuota | null;
  recent_jobs: AdminCompanyRecentJob[];
}
