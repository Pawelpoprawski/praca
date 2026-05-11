"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Save } from "lucide-react";
import api from "@/services/api";
import type { SystemSetting } from "@/types/api";

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const [editKey, setEditKey] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [message, setMessage] = useState({ type: "", text: "" });

  const { data: settings, isLoading } = useQuery({
    queryKey: ["admin-settings"],
    queryFn: () => api.get<SystemSetting[]>("/admin/settings").then((r) => r.data),
  });

  const updateMutation = useMutation({
    mutationFn: ({ key, value }: { key: string; value: string }) =>
      api.put("/admin/settings", null, { params: { key, value } }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-settings"] });
      setEditKey(null);
      setMessage({ type: "success", text: "Ustawienie zaktualizowane" });
      setTimeout(() => setMessage({ type: "", text: "" }), 3000);
    },
    onError: (err: any) => {
      setMessage({ type: "error", text: err.response?.data?.detail || "Błąd" });
    },
  });

  if (isLoading) {
    return <div className="animate-pulse h-64 bg-gray-100 rounded-lg" />;
  }

  return (
    <div>
      <h1 className="text-xl sm:text-2xl font-bold font-display text-[#0D2240] mb-6">Ustawienia systemowe</h1>

      {message.text && (
        <div
          className={`px-4 py-3 rounded-lg mb-4 text-sm flex items-center gap-2 border ${
            message.type === "success"
              ? "bg-green-50 border-green-200 text-green-700"
              : "bg-[#FFF0F3] border-[#FFC2CD] text-[#B8001F]"
          }`}
          role={message.type === "error" ? "alert" : "status"}
        >
          <span className="flex-shrink-0">{message.type === "success" ? "✓" : "⚠"}</span>
          {message.text}
        </div>
      )}

      <div className="bg-white border rounded-lg divide-y">
        {settings?.map((setting) => (
          <div key={setting.id} className="px-4 sm:px-5 py-4">
            <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
              <div className="min-w-0 flex-1">
                <p className="font-medium text-gray-900 text-sm break-words">
                  {setting.key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                </p>
                {setting.description && (
                  <p className="text-xs text-gray-500 mt-0.5 break-words">{setting.description}</p>
                )}
                <p className="text-xs text-gray-400 mt-0.5 break-all">Klucz: {setting.key}</p>
              </div>

              {editKey === setting.key ? (
                <div className="flex gap-2 items-center flex-wrap sm:flex-nowrap">
                  <input
                    type={setting.value_type === "int" ? "number" : "text"}
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    className="w-40 px-3 py-1.5 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-[#E1002A]/20"
                  />
                  <button
                    onClick={() => updateMutation.mutate({ key: setting.key, value: editValue })}
                    disabled={updateMutation.isPending}
                    className="p-1.5 text-green-600 hover:bg-green-50 rounded-lg"
                  >
                    <Save className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setEditKey(null)}
                    className="px-3 py-1 text-xs border rounded-lg hover:bg-gray-50"
                  >
                    Anuluj
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-3">
                  <span className="text-sm font-mono bg-gray-50 px-2 py-1 rounded">
                    {setting.value}
                  </span>
                  <button
                    onClick={() => {
                      setEditKey(setting.key);
                      setEditValue(setting.value);
                    }}
                    className="px-3 py-1 text-xs border rounded-lg hover:bg-gray-50 font-medium"
                  >
                    Edytuj
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
