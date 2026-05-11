"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Plus, Edit, Check, X } from "lucide-react";
import api from "@/services/api";
import type { AdminCategory } from "@/types/api";

export default function CategoriesPage() {
  const queryClient = useQueryClient();
  const [newName, setNewName] = useState("");
  const [newIcon, setNewIcon] = useState("");
  const [editId, setEditId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editIcon, setEditIcon] = useState("");
  const [message, setMessage] = useState({ type: "", text: "" });

  const { data: categories, isLoading } = useQuery({
    queryKey: ["admin-categories"],
    queryFn: () => api.get<AdminCategory[]>("/admin/categories").then((r) => r.data),
  });

  const createMutation = useMutation({
    mutationFn: () =>
      api.post("/admin/categories", null, { params: { name: newName, icon: newIcon || undefined } }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-categories"] });
      setNewName("");
      setNewIcon("");
      setMessage({ type: "success", text: "Kategoria dodana" });
      setTimeout(() => setMessage({ type: "", text: "" }), 3000);
    },
    onError: (err: any) => {
      setMessage({ type: "error", text: err.response?.data?.detail || "Błąd" });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, name, icon }: { id: string; name: string; icon: string }) =>
      api.put(`/admin/categories/${id}`, null, { params: { name, icon: icon || undefined } }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-categories"] });
      setEditId(null);
      setMessage({ type: "success", text: "Kategoria zaktualizowana" });
      setTimeout(() => setMessage({ type: "", text: "" }), 3000);
    },
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, isActive }: { id: string; isActive: boolean }) =>
      api.put(`/admin/categories/${id}`, null, { params: { is_active: isActive } }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-categories"] }),
  });

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;
    createMutation.mutate();
  };

  return (
    <div>
      <h1 className="text-xl sm:text-2xl font-bold font-display text-[#0D2240] mb-6">Kategorie</h1>

      {message.text && (
        <div className={`px-4 py-3 rounded-lg mb-4 text-sm ${
          message.type === "success" ? "bg-green-50 text-green-700" : "bg-[#FFF0F3] text-[#E1002A]"
        }`}>
          {message.text}
        </div>
      )}

      {/* Add new */}
      <form onSubmit={handleCreate} className="bg-white border rounded-lg p-3 sm:p-4 mb-6 flex flex-col sm:flex-row gap-3 sm:items-end">
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-1">Nowa kategoria</label>
          <input type="text" value={newName} onChange={(e) => setNewName(e.target.value)}
            placeholder="Nazwa kategorii"
            className="w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-[#E1002A]/20" />
        </div>
        <div className="sm:w-32">
          <label className="block text-sm font-medium text-gray-700 mb-1">Ikona</label>
          <input type="text" value={newIcon} onChange={(e) => setNewIcon(e.target.value)}
            placeholder="np. wrench"
            className="w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-[#E1002A]/20" />
        </div>
        <button type="submit" disabled={createMutation.isPending || !newName.trim()}
          className="px-4 py-2 bg-[#E1002A] text-white text-sm rounded-lg hover:bg-[#B8001F] disabled:opacity-50 flex items-center justify-center gap-1 w-full sm:w-auto">
          <Plus className="w-4 h-4" /> Dodaj
        </button>
      </form>

      {/* List */}
      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="animate-pulse h-12 bg-gray-100 rounded-lg" />
          ))}
        </div>
      ) : (
        <div className="bg-white border rounded-lg divide-y">
          {categories?.map((cat) => (
            <div key={cat.id} className="px-3 sm:px-4 py-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              {editId === cat.id ? (
                <div className="flex flex-col sm:flex-row gap-2 flex-1">
                  <input type="text" value={editName} onChange={(e) => setEditName(e.target.value)}
                    className="flex-1 px-3 py-1.5 border rounded-lg text-sm outline-none" />
                  <input type="text" value={editIcon} onChange={(e) => setEditIcon(e.target.value)}
                    placeholder="Ikona" className="w-28 px-3 py-1.5 border rounded-lg text-sm outline-none" />
                  <button onClick={() => updateMutation.mutate({ id: cat.id, name: editName, icon: editIcon })}
                    className="p-1.5 text-green-600 hover:bg-green-50 rounded-lg">
                    <Check className="w-4 h-4" />
                  </button>
                  <button onClick={() => setEditId(null)}
                    className="p-1.5 text-gray-400 hover:bg-gray-50 rounded-lg">
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <>
                  <div className="flex items-center gap-3">
                    <span className={`font-medium ${cat.is_active ? "text-gray-900" : "text-gray-400 line-through"}`}>
                      {cat.name}
                    </span>
                    {cat.icon && <span className="text-xs text-gray-400">{cat.icon}</span>}
                    <span className="text-xs text-gray-400">({cat.slug})</span>
                  </div>
                  <div className="flex gap-1">
                    <button onClick={() => { setEditId(cat.id); setEditName(cat.name); setEditIcon(cat.icon || ""); }}
                      className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-lg">
                      <Edit className="w-4 h-4" />
                    </button>
                    <button onClick={() => toggleMutation.mutate({ id: cat.id, isActive: !cat.is_active })}
                      className={`px-3 py-1 text-xs rounded-lg border font-medium ${
                        cat.is_active ? "text-[#E1002A] border-[#FFC2CD] hover:bg-[#FFF0F3]" : "text-green-600 border-green-200 hover:bg-green-50"
                      }`}>
                      {cat.is_active ? "Wyłącz" : "Włącz"}
                    </button>
                  </div>
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
