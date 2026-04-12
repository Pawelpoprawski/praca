"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import api from "@/services/api";
import { useAuthStore } from "@/store/authStore";
import { WORK_PERMITS } from "@/lib/utils";
import type { WorkerProfile, Canton } from "@/types/api";

const profileSchema = z.object({
  first_name: z.string().min(1, "Imię jest wymagane").max(100),
  last_name: z.string().min(1, "Nazwisko jest wymagane").max(100),
  phone: z.string().max(20, "Maksymalnie 20 znaków").optional().or(z.literal("")),
  canton: z.string().optional().or(z.literal("")),
  work_permit: z.string().optional().or(z.literal("")),
  experience_years: z.number().min(0).max(50).default(0),
  bio: z.string().optional().or(z.literal("")),
  industry: z.string().optional().or(z.literal("")),
});

type ProfileFormData = z.infer<typeof profileSchema>;

export default function WorkerProfilePage() {
  const queryClient = useQueryClient();
  const updateUser = useAuthStore((s) => s.updateUser);
  const user = useAuthStore((s) => s.user);
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");

  const { data: profile, isLoading } = useQuery({
    queryKey: ["worker-profile"],
    queryFn: () => api.get<WorkerProfile>("/worker/profile").then((r) => r.data),
  });

  const { data: cantons } = useQuery({
    queryKey: ["cantons"],
    queryFn: () => api.get<Canton[]>("/jobs/cantons").then((r) => r.data),
    staleTime: 24 * 60 * 60 * 1000,
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema) as any,
    defaultValues: {
      first_name: "",
      last_name: "",
      phone: "",
      canton: "",
      work_permit: "",
      experience_years: 0,
      bio: "",
      industry: "",
    },
  });

  useEffect(() => {
    if (profile) {
      reset({
        first_name: profile.first_name || "",
        last_name: profile.last_name || "",
        phone: profile.phone || "",
        canton: profile.canton || "",
        work_permit: profile.work_permit || "",
        experience_years: profile.experience_years || 0,
        bio: profile.bio || "",
        industry: profile.industry || "",
      });
    }
  }, [profile, reset]);

  const mutation = useMutation({
    mutationFn: async (data: ProfileFormData) => {
      // Aktualizuj profil pracownika (kanton, doświadczenie, bio, itp.)
      await api.put("/worker/profile", data);
      // Aktualizuj dane użytkownika (imię, nazwisko, telefon) w auth store
      await updateUser({
        first_name: data.first_name,
        last_name: data.last_name,
        phone: data.phone || "",
      });
    },
    onSuccess: () => {
      setSuccess("Profil zaktualizowany");
      setError("");
      queryClient.invalidateQueries({ queryKey: ["worker-profile"] });
      setTimeout(() => setSuccess(""), 3000);
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || "Błąd zapisu");
      setSuccess("");
    },
  });

  const onSubmit = (data: ProfileFormData) => {
    mutation.mutate(data);
  };

  if (isLoading) {
    return <div className="animate-pulse h-96 bg-gray-100 rounded-lg" />;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Mój profil</h1>

      {success && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-4 text-sm flex items-center gap-2" role="status">
          <span className="flex-shrink-0">✓</span>
          {success}
        </div>
      )}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4 text-sm flex items-center gap-2" role="alert">
          <span className="flex-shrink-0">⚠</span>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="bg-white border rounded-lg p-6 space-y-5">
        {/* Dane osobowe */}
        <h2 className="text-lg font-semibold text-gray-800">Dane osobowe</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Imię *</label>
            <input
              type="text"
              {...register("first_name")}
              className={`w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-red-500 ${
                errors.first_name ? "border-red-500" : ""
              }`}
            />
            {errors.first_name && (
              <p className="text-red-500 text-xs mt-1">{errors.first_name.message}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nazwisko *</label>
            <input
              type="text"
              {...register("last_name")}
              className={`w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-red-500 ${
                errors.last_name ? "border-red-500" : ""
              }`}
            />
            {errors.last_name && (
              <p className="text-red-500 text-xs mt-1">{errors.last_name.message}</p>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Telefon</label>
            <input
              type="tel"
              {...register("phone")}
              className={`w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-red-500 ${
                errors.phone ? "border-red-500" : ""
              }`}
              placeholder="+41 79 123 45 67"
            />
            {errors.phone && (
              <p className="text-red-500 text-xs mt-1">{errors.phone.message}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              value={user?.email || profile?.email || ""}
              readOnly
              className="w-full px-3 py-2 border rounded-lg text-sm bg-gray-50 text-gray-500 cursor-not-allowed"
            />
            <p className="text-gray-400 text-xs mt-1">Adres email nie może być zmieniony</p>
          </div>
        </div>

        {/* Dane zawodowe */}
        <h2 className="text-lg font-semibold text-gray-800 pt-2">Dane zawodowe</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Kanton zamieszkania</label>
            <select
              {...register("canton")}
              className="w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-red-500"
            >
              <option value="">Wybierz...</option>
              {cantons?.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Pozwolenie na pracę</label>
            <select
              {...register("work_permit")}
              className="w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-red-500"
            >
              <option value="">Wybierz...</option>
              {Object.entries(WORK_PERMITS).map(([key, label]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Lata doświadczenia</label>
            <input
              type="number"
              min={0}
              max={50}
              {...register("experience_years")}
              className="w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-red-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Branża</label>
            <input
              type="text"
              {...register("industry")}
              className="w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-red-500"
              placeholder="np. Budownictwo"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">O mnie</label>
          <textarea
            rows={4}
            {...register("bio")}
            className="w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-red-500 resize-none"
            placeholder="Krótki opis doświadczenia i umiejętności..."
          />
        </div>

        <button
          type="submit"
          disabled={mutation.isPending}
          className="w-full sm:w-auto bg-red-600 text-white px-6 py-2.5 rounded-lg hover:bg-red-700 font-medium text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {mutation.isPending ? "Zapisywanie..." : "Zapisz zmiany"}
        </button>
      </form>
    </div>
  );
}
