"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Heart } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/services/api";
import { useAuthStore } from "@/store/authStore";
import type { SavedJobCheck } from "@/types/api";
import { cn } from "@/lib/utils";

interface SaveJobButtonProps {
  jobId: string;
  className?: string;
  size?: "sm" | "md";
}

export default function SaveJobButton({ jobId, className, size = "md" }: SaveJobButtonProps) {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const queryClient = useQueryClient();
  const [animating, setAnimating] = useState(false);

  const isWorker = isAuthenticated && user?.role === "worker";

  const { data: savedCheck } = useQuery({
    queryKey: ["saved-job-check", jobId],
    queryFn: () =>
      api.get<SavedJobCheck>(`/worker/saved-jobs/check/${jobId}`).then((r) => r.data),
    enabled: isWorker,
    staleTime: 30_000,
  });

  const toggleMutation = useMutation({
    mutationFn: () => api.post(`/worker/saved-jobs/${jobId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["saved-job-check", jobId] });
      queryClient.invalidateQueries({ queryKey: ["saved-jobs"] });
      setAnimating(true);
      setTimeout(() => setAnimating(false), 300);
    },
  });

  const isSaved = savedCheck?.is_saved ?? false;

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (!isAuthenticated) {
      router.push("/login");
      return;
    }
    if (user?.role !== "worker") {
      return;
    }
    toggleMutation.mutate();
  };

  const iconSize = size === "sm" ? "w-4 h-4" : "w-5 h-5";
  const btnSize = size === "sm" ? "p-1.5" : "p-2";

  return (
    <button
      onClick={handleClick}
      disabled={toggleMutation.isPending}
      title={isSaved ? "Usuń z ulubionych" : "Zapisz ofertę"}
      aria-label={isSaved ? "Usuń z ulubionych" : "Zapisz ofertę"}
      className={cn(
        "rounded-full transition-all duration-200 hover:scale-110 active:scale-95 disabled:opacity-50",
        btnSize,
        isSaved
          ? "text-red-500 hover:text-[#E1002A] bg-[#FFF0F3] hover:bg-[#FFE0E6]"
          : "text-gray-400 hover:text-red-500 bg-gray-50 hover:bg-[#FFF0F3]",
        animating && "scale-125",
        className,
      )}
    >
      <Heart
        className={cn(
          iconSize,
          "transition-all duration-200",
          isSaved && "fill-current",
        )}
      />
    </button>
  );
}
