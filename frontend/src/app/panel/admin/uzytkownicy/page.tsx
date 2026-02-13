"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Search, UserCheck, UserX, ChevronLeft, ChevronRight } from "lucide-react";
import api from "@/services/api";
import { formatDate } from "@/lib/utils";
import type { User, PaginatedResponse } from "@/types/api";

const ROLE_LABELS: Record<string, { label: string; color: string }> = {
  worker: { label: "Pracownik", color: "bg-blue-100 text-blue-800" },
  employer: { label: "Pracodawca", color: "bg-purple-100 text-purple-800" },
  admin: { label: "Admin", color: "bg-red-100 text-red-800" },
};

export default function UsersPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [role, setRole] = useState("");
  const [search, setSearch] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["admin-users", page, role, searchQuery],
    queryFn: () =>
      api.get<PaginatedResponse<User>>("/admin/users", {
        params: {
          page, per_page: 20,
          ...(role && { role }),
          ...(searchQuery && { q: searchQuery }),
        },
      }).then((r) => r.data),
  });

  const toggleMutation = useMutation({
    mutationFn: ({ userId, isActive }: { userId: string; isActive: boolean }) =>
      api.put(`/admin/users/${userId}/status`, null, { params: { is_active: isActive } }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-users"] }),
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearchQuery(search);
    setPage(1);
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Użytkownicy</h1>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3 mb-4">
        <form onSubmit={handleSearch} className="flex-1 flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input type="text" value={search} onChange={(e) => setSearch(e.target.value)}
              placeholder="Szukaj po email lub nazwisku..."
              className="w-full pl-10 pr-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-red-500" />
          </div>
          <button type="submit" className="px-4 py-2 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700">
            Szukaj
          </button>
        </form>
        <div className="flex gap-2">
          {[
            { value: "", label: "Wszyscy" },
            { value: "worker", label: "Pracownicy" },
            { value: "employer", label: "Pracodawcy" },
            { value: "admin", label: "Admini" },
          ].map((f) => (
            <button key={f.value} onClick={() => { setRole(f.value); setPage(1); }}
              className={`px-3 py-1.5 text-sm rounded-lg border font-medium ${
                role === f.value ? "bg-red-50 border-red-200 text-red-700" : "bg-white hover:bg-gray-50 text-gray-600"
              }`}>
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="animate-pulse h-14 bg-gray-100 rounded-lg" />
          ))}
        </div>
      ) : data?.data && data.data.length > 0 ? (
        <>
          <div className="bg-white border rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-gray-500">Użytkownik</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-500">Rola</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-500">Status</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-500">Dołączył</th>
                  <th className="text-right px-4 py-3 font-medium text-gray-500">Akcje</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {data.data.map((user) => {
                  const roleInfo = ROLE_LABELS[user.role] || { label: user.role, color: "bg-gray-100 text-gray-800" };
                  return (
                    <tr key={user.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <p className="font-medium text-gray-900">
                          {user.first_name} {user.last_name}
                        </p>
                        <p className="text-gray-500 text-xs">{user.email}</p>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`text-xs px-2 py-0.5 rounded font-medium ${roleInfo.color}`}>
                          {roleInfo.label}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`text-xs px-2 py-0.5 rounded font-medium ${
                          user.is_active ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                        }`}>
                          {user.is_active ? "Aktywny" : "Nieaktywny"}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-500">{formatDate(user.created_at)}</td>
                      <td className="px-4 py-3 text-right">
                        {user.role !== "admin" && (
                          <button
                            onClick={() => toggleMutation.mutate({ userId: user.id, isActive: !user.is_active })}
                            disabled={toggleMutation.isPending}
                            className={`p-1.5 rounded-lg ${
                              user.is_active
                                ? "text-red-600 hover:bg-red-50"
                                : "text-green-600 hover:bg-green-50"
                            }`}
                            title={user.is_active ? "Dezaktywuj" : "Aktywuj"}
                          >
                            {user.is_active ? <UserX className="w-4 h-4" /> : <UserCheck className="w-4 h-4" />}
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {data.pages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <p className="text-sm text-gray-500">Strona {data.page} z {data.pages} ({data.total} użytkowników)</p>
              <div className="flex gap-1">
                <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1}
                  className="p-2 border rounded-lg hover:bg-gray-50 disabled:opacity-30">
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button onClick={() => setPage((p) => Math.min(data.pages, p + 1))} disabled={page >= data.pages}
                  className="p-2 border rounded-lg hover:bg-gray-50 disabled:opacity-30">
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="bg-white border rounded-lg px-5 py-12 text-center">
          <p className="text-gray-500">Brak użytkowników</p>
        </div>
      )}
    </div>
  );
}
