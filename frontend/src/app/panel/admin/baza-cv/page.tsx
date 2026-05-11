"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Search, Download, ChevronLeft, ChevronRight,
  Calendar, Eye, FileDown,
  Users, Filter,
} from "lucide-react";
import api from "@/services/api";
import type { PaginatedResponse, CVDatabaseListItem, CVDatabaseDetail } from "@/types/api";

const CANTON_LABELS: Record<string, string> = {
  AG: "Argovia", AI: "Appenzell I.Rh.", AR: "Appenzell A.Rh.", BE: "Berno",
  BL: "Bazylea-okręg", BS: "Bazylea-miasto", FR: "Fryburg", GE: "Genewa",
  GL: "Glarus", GR: "Gryzonia", JU: "Jura", LU: "Lucerna",
  NE: "Neuchâtel", NW: "Nidwalden", OW: "Obwalden", SG: "St. Gallen",
  SH: "Szafuza", SO: "Solura", SZ: "Schwyz", TG: "Turgowia",
  TI: "Ticino", UR: "Uri", VD: "Vaud", VS: "Valais",
  ZG: "Zug", ZH: "Zurych",
};

interface ExtractedExp { position?: string; company?: string; period?: string }
interface ExtractedEdu { degree?: string; institution?: string; year?: string }

function ExtractedDataView({ data }: { data: Record<string, unknown> }) {
  const experience = Array.isArray(data.experience) ? (data.experience as ExtractedExp[]) : [];
  const education = Array.isArray(data.education) ? (data.education as ExtractedEdu[]) : [];
  const skills = Array.isArray(data.skills) ? (data.skills as string[]) : [];

  return (
    <div className="bg-gray-50 rounded-lg p-3 text-xs">
      {experience.length > 0 && (
        <div className="mb-2">
          <p className="font-semibold text-gray-700 mb-1">Doświadczenie:</p>
          {experience.map((exp, i) => (
            <p key={i} className="text-gray-600">
              {exp.position} @ {exp.company} ({exp.period})
            </p>
          ))}
        </div>
      )}
      {education.length > 0 && (
        <div className="mb-2">
          <p className="font-semibold text-gray-700 mb-1">Wykształcenie:</p>
          {education.map((edu, i) => (
            <p key={i} className="text-gray-600">
              {edu.degree} - {edu.institution} ({edu.year})
            </p>
          ))}
        </div>
      )}
      {skills.length > 0 && (
        <div>
          <p className="font-semibold text-gray-700 mb-1">Umiejętności:</p>
          <p className="text-gray-600">{skills.join(", ")}</p>
        </div>
      )}
      {experience.length === 0 && education.length === 0 && skills.length === 0 && (
        <p className="text-gray-400">Brak wyekstrahowanych danych</p>
      )}
    </div>
  );
}

function ScoreBadge({ score }: { score: number | null }) {
  if (score == null) return <span className="text-gray-400 text-sm">-</span>;
  const color =
    score <= 3 ? "bg-[#FFE0E6] text-[#B8001F]" :
    score <= 6 ? "bg-yellow-100 text-yellow-700" :
    "bg-green-100 text-green-700";
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${color}`}>
      {score}/10
    </span>
  );
}

export default function AdminCVDatabasePage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [canton, setCanton] = useState("");
  const [language, setLanguage] = useState("");
  const [minScore, setMinScore] = useState("");
  const [extractionStatus, setExtractionStatus] = useState("");
  const [categorySlug, setCategorySlug] = useState("");
  const [matchReady, setMatchReady] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["admin-cv-database", page, search, canton, language, minScore, extractionStatus, categorySlug, matchReady],
    queryFn: () =>
      api.get<PaginatedResponse<CVDatabaseListItem>>("/admin/cv-database", {
        params: {
          page,
          per_page: 20,
          ...(search && { q: search }),
          ...(canton && { canton }),
          ...(language && { language }),
          ...(minScore && { min_score: parseInt(minScore) }),
          ...(extractionStatus && { extraction_status: extractionStatus }),
          ...(categorySlug && { category_slug: categorySlug }),
          ...(matchReady !== "" && { match_ready: matchReady === "true" }),
        },
      }).then((r) => r.data),
  });

  const { data: detail } = useQuery({
    queryKey: ["admin-cv-database-detail", selectedId],
    queryFn: () =>
      api.get<CVDatabaseDetail>(`/admin/cv-database/${selectedId}`).then((r) => r.data),
    enabled: !!selectedId,
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch(searchInput);
    setPage(1);
  };

  const handleExport = async () => {
    try {
      const response = await api.get("/admin/cv-database-export", {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = `baza_cv_${new Date().toISOString().split("T")[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      // error handling
    }
  };

  const [downloadError, setDownloadError] = useState<string | null>(null);

  const handleDownloadCV = async (entryId: string, name: string | null) => {
    setDownloadError(null);
    try {
      const response = await api.get(`/admin/cv-database/${entryId}/download`, {
        responseType: "blob",
      });

      // Check if we got an error response disguised as blob
      if (response.data.type === "application/json") {
        const text = await response.data.text();
        const err = JSON.parse(text);
        setDownloadError(err.detail || "Nie udało się pobrać pliku CV");
        return;
      }

      const contentType = response.headers["content-type"] || "application/octet-stream";
      const url = window.URL.createObjectURL(new Blob([response.data], { type: contentType }));
      const a = document.createElement("a");
      a.href = url;
      const ext = contentType.includes("pdf") ? ".pdf" : ".docx";
      a.download = `CV_${(name || "kandydat").replace(/\s+/g, "_")}${ext}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: Blob } };
      if (axiosErr.response?.data instanceof Blob) {
        try {
          const text = await axiosErr.response.data.text();
          const parsed = JSON.parse(text);
          setDownloadError(parsed.detail || "Nie udało się pobrać pliku CV");
        } catch {
          setDownloadError("Nie udało się pobrać pliku CV");
        }
      } else {
        setDownloadError("Nie udało się pobrać pliku CV. Sprawdź czy plik istnieje.");
      }
    }
  };

  return (
    <div>
      {/* Download error banner */}
      {downloadError && (
        <div className="mb-4 bg-[#FFF0F3] border border-[#FFC2CD] text-[#B8001F] px-4 py-3 rounded-lg flex items-center justify-between">
          <span className="text-sm">{downloadError}</span>
          <button onClick={() => setDownloadError(null)} className="text-red-500 hover:text-[#B8001F] font-bold">&times;</button>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 sm:gap-4 mb-6">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold font-display text-[#0D2240] flex items-center gap-2">
            <Users className="w-5 h-5 sm:w-6 sm:h-6 text-blue-600" />
            Baza CV
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            {data?.total ?? 0} kandydatów w bazie
          </p>
        </div>
        <div className="flex gap-2 sm:gap-3 flex-wrap">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              showFilters ? "bg-blue-100 text-blue-700" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            <Filter className="w-4 h-4" />
            Filtry
          </button>
          <button
            onClick={handleExport}
            className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-green-700 transition-colors"
          >
            <Download className="w-4 h-4" />
            Eksport CSV
          </button>
        </div>
      </div>

      {/* Search & Filters */}
      <div className="bg-white border rounded-lg p-3 sm:p-4 mb-6">
        <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-2 sm:gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Szukaj po imieniu, emailu, preferencjach..."
              className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            />
          </div>
          <button
            type="submit"
            className="bg-blue-600 text-white px-6 py-2.5 rounded-lg text-sm font-semibold hover:bg-blue-700 transition-colors w-full sm:w-auto"
          >
            Szukaj
          </button>
        </form>

        {showFilters && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 sm:gap-4 mt-4 pt-4 border-t">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Kanton</label>
              <select
                value={canton}
                onChange={(e) => { setCanton(e.target.value); setPage(1); }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
              >
                <option value="">Wszystkie</option>
                {Object.entries(CANTON_LABELS).map(([k, v]) => (
                  <option key={k} value={k}>{v} ({k})</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Jezyk</label>
              <select
                value={language}
                onChange={(e) => { setLanguage(e.target.value); setPage(1); }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
              >
                <option value="">Wszystkie</option>
                <option value="pl">Polski</option>
                <option value="de">Niemiecki</option>
                <option value="fr">Francuski</option>
                <option value="it">Wloski</option>
                <option value="en">Angielski</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Min. ocena CV</label>
              <select
                value={minScore}
                onChange={(e) => { setMinScore(e.target.value); setPage(1); }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
              >
                <option value="">Dowolna</option>
                {[3, 5, 7, 8, 9].map((s) => (
                  <option key={s} value={s}>{s}+ /10</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Status ekstrakcji</label>
              <select
                value={extractionStatus}
                onChange={(e) => { setExtractionStatus(e.target.value); setPage(1); }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
              >
                <option value="">Wszystkie</option>
                <option value="pending">Oczekujace</option>
                <option value="processing">Przetwarzane</option>
                <option value="completed">Ukonczone</option>
                <option value="failed">Bledy</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Kategoria (AI)</label>
              <select
                value={categorySlug}
                onChange={(e) => { setCategorySlug(e.target.value); setPage(1); }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
              >
                <option value="">Wszystkie</option>
                <option value="budownictwo">Budownictwo</option>
                <option value="gastronomia">Gastronomia</option>
                <option value="opieka">Opieka</option>
                <option value="transport">Transport</option>
                <option value="it">IT</option>
                <option value="sprzatanie">Sprzatanie</option>
                <option value="produkcja">Produkcja</option>
                <option value="handel">Handel</option>
                <option value="finanse">Finanse</option>
                <option value="administracja">Administracja</option>
                <option value="rolnictwo">Rolnictwo</option>
                <option value="inne">Inne</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Gotowe do matchingu</label>
              <select
                value={matchReady}
                onChange={(e) => { setMatchReady(e.target.value); setPage(1); }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
              >
                <option value="">Wszystkie</option>
                <option value="true">Tak</option>
                <option value="false">Nie</option>
              </select>
            </div>
          </div>
        )}
      </div>

      <div className="flex flex-col lg:flex-row gap-4 lg:gap-6">
        {/* Table */}
        <div className="flex-1 min-w-0">
          <div className="bg-white border rounded-lg overflow-hidden overflow-x-auto">
            {isLoading ? (
              <div className="p-8 text-center text-gray-500">Ładowanie...</div>
            ) : data?.data && data.data.length > 0 ? (
              <table className="w-full text-sm min-w-[700px]">
                <thead>
                  <tr className="bg-gray-50 border-b">
                    <th className="text-left px-4 py-3 font-semibold text-gray-600">Kandydat</th>
                    <th className="text-left px-4 py-3 font-semibold text-gray-600">Szukana praca</th>
                    <th className="text-left px-4 py-3 font-semibold text-gray-600">Dostępność</th>
                    <th className="text-center px-4 py-3 font-semibold text-gray-600">Ocena</th>
                    <th className="text-center px-4 py-3 font-semibold text-gray-600">Akcje</th>
                  </tr>
                </thead>
                <tbody>
                  {data.data.map((entry) => (
                    <tr
                      key={entry.id}
                      className={`border-b hover:bg-blue-50/30 cursor-pointer transition-colors ${
                        selectedId === entry.id ? "bg-blue-50" : ""
                      }`}
                      onClick={() => setSelectedId(entry.id)}
                    >
                      <td className="px-4 py-3">
                        <p className="font-semibold text-gray-900">
                          {entry.full_name || "Brak danych"}
                        </p>
                        <p className="text-xs text-gray-500">{entry.email}</p>
                      </td>
                      <td className="px-4 py-3">
                        <p className="text-gray-700 line-clamp-2 max-w-xs">
                          {entry.job_preferences || "-"}
                        </p>
                      </td>
                      <td className="px-4 py-3">
                        {entry.available_from ? (
                          <span className="flex items-center gap-1 text-gray-600">
                            <Calendar className="w-3.5 h-3.5" />
                            {new Date(entry.available_from).toLocaleDateString("pl-PL")}
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <ScoreBadge score={entry.overall_score} />
                      </td>
                      <td className="px-4 py-3 text-center">
                        <div className="flex items-center justify-center gap-2">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedId(entry.id);
                            }}
                            className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors"
                            title="Szczegóły"
                          >
                            <Eye className="w-4 h-4 text-gray-500" />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDownloadCV(entry.id, entry.full_name);
                            }}
                            className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors"
                            title="Pobierz CV"
                          >
                            <FileDown className="w-4 h-4 text-gray-500" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="p-8 text-center text-gray-500">
                <Users className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                <p className="font-medium">Brak kandydatów w bazie</p>
                <p className="text-sm">Kandydaci pojawią się po przesłaniu CV z analizy AI.</p>
              </div>
            )}
          </div>

          {/* Pagination */}
          {data && data.pages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <p className="text-sm text-gray-500">
                Strona {data.page} z {data.pages} ({data.total} wyników)
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage(Math.max(1, page - 1))}
                  disabled={page <= 1}
                  className="p-2 border rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setPage(Math.min(data.pages, page + 1))}
                  disabled={page >= data.pages}
                  className="p-2 border rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Detail Panel */}
        {selectedId && detail && (
          <div className="lg:w-96 bg-white border rounded-lg p-4 sm:p-5 lg:sticky lg:top-4 max-h-[600px] lg:max-h-[calc(100vh-120px)] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-gray-900">Szczegóły kandydata</h3>
              <button
                onClick={() => setSelectedId(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                &times;
              </button>
            </div>

            <div className="space-y-4">
              {/* Name & Contact */}
              <div>
                <p className="text-lg font-bold text-gray-900">{detail.full_name || "Brak danych"}</p>
                {detail.email && <p className="text-sm text-gray-600">{detail.email}</p>}
                {detail.phone && <p className="text-sm text-gray-600">{detail.phone}</p>}
              </div>

              {/* Score */}
              {detail.overall_score != null && (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-500">Ocena CV:</span>
                  <ScoreBadge score={detail.overall_score} />
                </div>
              )}

              {/* Job preferences */}
              {detail.job_preferences && (
                <div>
                  <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Szukana praca</p>
                  <p className="text-sm text-gray-700">{detail.job_preferences}</p>
                </div>
              )}

              {/* Available from */}
              {detail.available_from && (
                <div className="flex items-center gap-2 text-sm">
                  <Calendar className="w-4 h-4 text-gray-400" />
                  <span className="text-gray-600">
                    Dostępny od: {new Date(detail.available_from).toLocaleDateString("pl-PL")}
                  </span>
                </div>
              )}

              {/* Cantons */}
              {detail.preferred_cantons && detail.preferred_cantons.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Kantony</p>
                  <div className="flex flex-wrap gap-1.5">
                    {detail.preferred_cantons.map((c) => (
                      <span key={c} className="bg-blue-50 text-blue-700 text-xs px-2 py-1 rounded-md font-medium">
                        {CANTON_LABELS[c] || c}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Salary */}
              {(detail.expected_salary_min || detail.expected_salary_max) && (
                <div>
                  <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Wynagrodzenie (CHF/mies.)</p>
                  <p className="text-sm text-gray-700">
                    {detail.expected_salary_min && detail.expected_salary_max
                      ? `${detail.expected_salary_min.toLocaleString("pl-PL")} - ${detail.expected_salary_max.toLocaleString("pl-PL")} CHF`
                      : detail.expected_salary_min
                        ? `od ${detail.expected_salary_min.toLocaleString("pl-PL")} CHF`
                        : `do ${detail.expected_salary_max!.toLocaleString("pl-PL")} CHF`
                    }
                  </p>
                </div>
              )}

              {/* Work mode */}
              {detail.work_mode && (
                <div>
                  <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Tryb pracy</p>
                  <p className="text-sm text-gray-700">
                    {{ onsite: "Na miejscu", remote: "Zdalnie", hybrid: "Hybrydowo" }[detail.work_mode] || detail.work_mode}
                  </p>
                </div>
              )}

              {/* Languages */}
              {detail.languages && detail.languages.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Języki</p>
                  <div className="space-y-1">
                    {detail.languages.map((l, i) => (
                      <div key={i} className="flex items-center justify-between text-sm">
                        <span className="text-gray-700">{l.language}</span>
                        <span className="text-gray-500 font-medium">{l.level}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Driving license & car */}
              {(detail.driving_license || detail.has_car) && (
                <div>
                  <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Transport</p>
                  {detail.driving_license && (
                    <p className="text-sm text-gray-700">Prawo jazdy: Kat. {detail.driving_license}</p>
                  )}
                  <p className="text-sm text-gray-700">
                    Samochód: {detail.has_car ? "Tak" : "Nie"}
                  </p>
                </div>
              )}

              {/* Additional notes */}
              {detail.additional_notes && (
                <div>
                  <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Uwagi</p>
                  <p className="text-sm text-gray-700">{detail.additional_notes}</p>
                </div>
              )}

              {/* Extracted data */}
              {detail.extracted_data && (
                <div>
                  <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Dane z CV (AI)</p>
                  <ExtractedDataView data={detail.extracted_data} />
                </div>
              )}

              {/* Download button */}
              <button
                onClick={() => handleDownloadCV(detail.id, detail.full_name)}
                className="w-full flex items-center justify-center gap-2 bg-blue-600 text-white py-2.5 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
              >
                <FileDown className="w-4 h-4" />
                Pobierz CV
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
