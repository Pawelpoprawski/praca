import api from "@/services/api";

const STORAGE_KEY = "viewed_jobs";
const MAX_LOCAL_ITEMS = 10;

export interface ViewedJobEntry {
  id: string;
  viewedAt: string;
}

/**
 * Get recently viewed job IDs from localStorage.
 */
export function getViewedJobs(): ViewedJobEntry[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as ViewedJobEntry[];
  } catch {
    return [];
  }
}

/**
 * Get just the IDs of recently viewed jobs.
 */
export function getViewedJobIds(): string[] {
  return getViewedJobs().map((e) => e.id);
}

/**
 * Track a job view: save to localStorage and POST to API if authenticated.
 */
export function trackJobView(jobId: string, isAuthenticated: boolean): void {
  // 1. localStorage (for all users)
  saveToLocalStorage(jobId);

  // 2. API (for authenticated users only, fire-and-forget)
  if (isAuthenticated) {
    api.post(`/jobs/${jobId}/view`).catch(() => {
      // Silently ignore errors
    });
  }
}

function saveToLocalStorage(jobId: string): void {
  if (typeof window === "undefined") return;
  try {
    const entries = getViewedJobs();
    // Remove existing entry for this job (to move it to top)
    const filtered = entries.filter((e) => e.id !== jobId);
    // Add to beginning
    filtered.unshift({ id: jobId, viewedAt: new Date().toISOString() });
    // Trim to max size
    const trimmed = filtered.slice(0, MAX_LOCAL_ITEMS);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
  } catch {
    // localStorage might be full or unavailable
  }
}
