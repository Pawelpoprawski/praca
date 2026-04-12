"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, MessageSquare, Send } from "lucide-react";
import api from "@/services/api";
import { useAuthStore } from "@/store/authStore";
import { formatDate } from "@/lib/utils";
import ReviewStars from "./ReviewStars";
import type { ReviewListResponse } from "@/types/api";

interface Props {
  companySlug: string;
}

export default function ReviewSection({ companySlug }: Props) {
  const queryClient = useQueryClient();
  const { user, isAuthenticated } = useAuthStore();
  const [page, setPage] = useState(1);

  // Review form state
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");
  const [formError, setFormError] = useState("");
  const [showForm, setShowForm] = useState(false);

  const { data: reviewsData, isLoading } = useQuery({
    queryKey: ["company-reviews", companySlug, page],
    queryFn: () =>
      api
        .get<ReviewListResponse>(`/companies/${companySlug}/reviews`, {
          params: { page, per_page: 10 },
        })
        .then((r) => r.data),
  });

  const createReview = useMutation({
    mutationFn: (payload: { rating: number; comment: string }) =>
      api.post(`/companies/${companySlug}/reviews`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["company-reviews", companySlug],
      });
      setRating(0);
      setComment("");
      setShowForm(false);
      setFormError("");
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail;
      if (typeof detail === "string") {
        setFormError(detail);
      } else {
        setFormError("Nie udalo sie dodac recenzji. Sprobuj ponownie.");
      }
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError("");

    if (rating === 0) {
      setFormError("Wybierz ocene (1-5 gwiazdek)");
      return;
    }
    if (comment.trim().length < 10) {
      setFormError("Komentarz musi miec co najmniej 10 znakow");
      return;
    }

    createReview.mutate({ rating, comment: comment.trim() });
  };

  const isWorker = isAuthenticated && user?.role === "worker";

  return (
    <div className="mt-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <MessageSquare className="w-5 h-5" />
        Recenzje
        {reviewsData && reviewsData.total_reviews > 0 && (
          <span className="text-sm font-normal text-gray-500">
            ({reviewsData.total_reviews})
          </span>
        )}
      </h2>

      {/* Average rating summary */}
      {reviewsData && reviewsData.avg_rating !== null && (
        <div className="bg-white border rounded-lg p-4 mb-4 flex items-center gap-4">
          <div className="text-3xl font-bold text-gray-900">
            {reviewsData.avg_rating.toFixed(1)}
          </div>
          <div>
            <ReviewStars rating={Math.round(reviewsData.avg_rating)} size="md" />
            <p className="text-sm text-gray-500 mt-0.5">
              {reviewsData.total_reviews}{" "}
              {reviewsData.total_reviews === 1
                ? "recenzja"
                : reviewsData.total_reviews < 5
                  ? "recenzje"
                  : "recenzji"}
            </p>
          </div>
        </div>
      )}

      {/* Add review button / form */}
      {isWorker && !showForm && (
        <button
          onClick={() => setShowForm(true)}
          className="mb-4 px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 transition-colors flex items-center gap-2"
        >
          <Send className="w-4 h-4" />
          Napisz recenzje
        </button>
      )}

      {isWorker && showForm && (
        <form
          onSubmit={handleSubmit}
          className="bg-white border rounded-lg p-5 mb-4"
        >
          <h3 className="font-medium text-gray-900 mb-3">Twoja recenzja</h3>

          <div className="mb-3">
            <label className="block text-sm text-gray-600 mb-1">Ocena</label>
            <ReviewStars
              rating={rating}
              size="lg"
              interactive
              onChange={setRating}
            />
          </div>

          <div className="mb-3">
            <label className="block text-sm text-gray-600 mb-1">
              Komentarz (min. 10 znakow)
            </label>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              rows={4}
              maxLength={2000}
              placeholder="Podziel sie swoim doswiadczeniem z ta firma..."
              className="w-full px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-red-500 resize-none"
            />
            <p className="text-xs text-gray-400 mt-1">
              {comment.length}/2000 znakow
            </p>
          </div>

          {formError && (
            <p className="text-sm text-red-600 mb-3">{formError}</p>
          )}

          <div className="flex gap-2">
            <button
              type="submit"
              disabled={createReview.isPending}
              className="px-4 py-2 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
            >
              {createReview.isPending ? "Wysylanie..." : "Wyslij recenzje"}
            </button>
            <button
              type="button"
              onClick={() => {
                setShowForm(false);
                setFormError("");
                setRating(0);
                setComment("");
              }}
              className="px-4 py-2 border text-sm rounded-lg hover:bg-gray-50 transition-colors"
            >
              Anuluj
            </button>
          </div>

          <p className="text-xs text-gray-400 mt-3">
            Recenzja zostanie opublikowana po zatwierdzeniu przez moderatora.
          </p>
        </form>
      )}

      {!isAuthenticated && (
        <p className="text-sm text-gray-500 mb-4">
          <a href="/login" className="text-red-600 hover:underline">
            Zaloguj sie
          </a>{" "}
          jako pracownik, aby dodac recenzje.
        </p>
      )}

      {/* Reviews list */}
      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="animate-pulse h-24 bg-gray-100 rounded-lg" />
          ))}
        </div>
      ) : reviewsData?.data && reviewsData.data.length > 0 ? (
        <>
          <div className="space-y-3">
            {reviewsData.data.map((review) => (
              <div
                key={review.id}
                className="bg-white border rounded-lg p-4"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <span className="font-medium text-gray-900 text-sm">
                      {review.worker_name}
                    </span>
                    <ReviewStars rating={review.rating} size="sm" />
                  </div>
                  <span className="text-xs text-gray-400">
                    {formatDate(review.created_at)}
                  </span>
                </div>
                <p className="text-sm text-gray-700 whitespace-pre-line">
                  {review.comment}
                </p>
              </div>
            ))}
          </div>

          {reviewsData.pages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <p className="text-sm text-gray-500">
                Strona {reviewsData.page} z {reviewsData.pages}
              </p>
              <div className="flex gap-1">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="p-2 border rounded-lg hover:bg-gray-50 disabled:opacity-30"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  onClick={() =>
                    setPage((p) => Math.min(reviewsData.pages, p + 1))
                  }
                  disabled={page >= reviewsData.pages}
                  className="p-2 border rounded-lg hover:bg-gray-50 disabled:opacity-30"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="bg-white border rounded-lg px-5 py-8 text-center">
          <p className="text-gray-500">
            Ta firma nie ma jeszcze recenzji
          </p>
        </div>
      )}
    </div>
  );
}
