package handlers

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"time"

	"github.com/daniel13112001/api-gateway/gen/vectorsearch"
	"github.com/daniel13112001/api-gateway/stores"
)

type Handler struct {
	VectorClient vectorsearch.VectorSearchServiceClient
	Metadata     stores.MetadataStore
	RateLimiter  stores.RateLimitStore
}

func (h *Handler) rateLimit(
	ctx context.Context,
	key string,
	limit int64,
	window time.Duration,
) error {

	count, err := h.RateLimiter.Incr(ctx, key)
	if err != nil {
		return err
	}

	if count == 1 {
		// first request → set TTL
		if err := h.RateLimiter.Expire(ctx, key, window); err != nil {
			return err
		}
	}

	if count > limit {
		return fmt.Errorf("rate limit exceeded")
	}

	return nil
}

func (h *Handler) GetSimilarClaims(w http.ResponseWriter, r *http.Request) {

	ip := r.RemoteAddr // optionally sanitize later
	ctx := r.Context()

	key := fmt.Sprintf("rl:search:%s", ip)

	if err := h.rateLimit(ctx, key, 5, time.Minute); err != nil {
		http.Error(w, "Too many requests. Max is 5 requests per minute", http.StatusTooManyRequests)
		return
	}

	query := r.URL.Query().Get("q")
	if query == "" {
		http.Error(w, "missing query parameter: q", http.StatusBadRequest)
		return
	}

	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	// 1️⃣ Vector search
	resp, err := h.VectorClient.Search(ctx, &vectorsearch.SearchRequest{
		Query: query,
		K:     1,
	})
	if err != nil {
		http.Error(w, "vector search failed", http.StatusBadGateway)
		return
	}
	// TODO: Print logs
	log.Printf("gRPC results count: %d", len(resp.Results))
	for _, r := range resp.Results {
		log.Printf("uid=%s score=%f", r.Uid, r.Score)
	}
	// End of print logs

	// 2️⃣ Collect UIDs
	uids := make([]string, 0, len(resp.Results))
	for _, r := range resp.Results {
		uids = append(uids, r.Uid)
	}

	// 3️⃣ Fetch metadata
	claims, err := h.Metadata.Get(ctx, uids)
	if err != nil {
		log.Printf("metadata lookup failed for uids=%v: %v", uids, err)
		http.Error(w, "metadata lookup failed", http.StatusInternalServerError)
		return
	}

	// 4️⃣ Return JSON
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(claims)
}

func (h *Handler) CreateCommunityClaim(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusNotImplemented)
	fmt.Fprintln(w, "CreateCommunityClaim: not implemented")
}

func (h *Handler) Health(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	fmt.Fprintln(w, "ok")
}

func (h *Handler) Login(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusNotImplemented)
	fmt.Fprintln(w, "Login: not implemented")
}
