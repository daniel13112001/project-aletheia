package main

import (
	"log"
	"net/http"
	"os"

	"github.com/joho/godotenv"
	"github.com/redis/go-redis/v9"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"github.com/daniel13112001/api-gateway/db"
	"github.com/daniel13112001/api-gateway/handlers"
	"github.com/daniel13112001/api-gateway/stores"
	"github.com/daniel13112001/api-gateway/gen/vectorsearch"
)
func main() {
	_ = godotenv.Load(".env.local")

	pg, err := db.NewPostgresDB(os.Getenv("DATABASE_URL"))
	if err != nil {
		log.Fatal(err)
	}
	_ = stores.NewPostgresMetadataStore(pg)

	redisClient := redis.NewClient(&redis.Options{
		Addr: "localhost:6379",
	})
	_ = stores.NewRedisRateLimitStore(redisClient)

	conn, err := grpc.Dial(
		"localhost:50051",
		grpc.WithTransportCredentials(insecure.NewCredentials()),
	)
	if err != nil {
		log.Fatal(err)
	}
	defer conn.Close()

	vectorClient := vectorsearch.NewVectorSearchServiceClient(conn)
	metadataStore := stores.NewPostgresMetadataStore(pg)
	rateLimiter := stores.NewRedisRateLimitStore(redisClient)

	h := &handlers.Handler{
		VectorClient: vectorClient,
		Metadata:     metadataStore,
		RateLimiter: rateLimiter,
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/health", h.Health)
	mux.HandleFunc("/search", h.GetSimilarClaims)
	mux.HandleFunc("/login", h.Login)
	mux.HandleFunc("/claims", h.CreateCommunityClaim)

	log.Fatal(http.ListenAndServe(":8080", mux))
}
