package middleware

import (
	"net/http"
	"github.com/daniel13112001/api-gateway/stores"
	"time"
	"fmt"
)


func Logging(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {

		start := time.Now()

		// Call next handler
		next.ServeHTTP(w, r)

		duration := time.Since(start)

		// Simple logging for now. TODO: Implement more sophisticated logging
		fmt.Println(
			"method=", r.Method,
			"path=", r.URL.Path,
			"remote=", r.RemoteAddr,
			"duration=", duration,
		)
	})
}

func RateLimit(r stores.RateLimitStore) func(http.Handler) http.Handler {

	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, req *http.Request) {

			ctx := req.Context()

			// 1️⃣ Get client IP
			ip := req.RemoteAddr 

			// 2️⃣ Compose key
			key := "rate:claims:" + ip

			// Increment counter in store
			count, err := r.Incr(ctx, key)
			if err != nil {
				http.Error(w, "rate limiter unavailable", http.StatusServiceUnavailable)
				return
			}

			// 4️⃣ Set expiration on first request
			if count == 1 {
				_ = r.Expire(ctx, key, time.Minute)
			}

			// 5️⃣ Block if over limit
			if count > 3 {
				http.Error(w, "too many requests", http.StatusTooManyRequests)
				return
			}

			// 6️⃣ Call next handler
			next.ServeHTTP(w, req)
		})
	}
}


func Auth(next http.Handler) http.Handler{

	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		next.ServeHTTP(w, r)
	})
	
}
