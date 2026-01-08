package main

import (
	"context"
	"fmt"
	"log"
	"time"

	pb "github.com/daniel13112001/api-gateway/gen"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"github.com/daniel13112001/api-gateway/stores"
)

func main() {

	store, err := stores.NewInMemoryMetadataStore("/Users/danielyakubu/Documents/Projects/project-aletheia/artifacts/metadata.jsonl")

	if err != nil {
	log.Fatalf("failed to load metadata store: %v", err)
}

	fmt.Println("API Gateway test")

	// 1️⃣ Connect to Python gRPC server
	conn, err := grpc.Dial(
		"localhost:50051",
		grpc.WithTransportCredentials(insecure.NewCredentials()),
	)
	if err != nil {
		log.Fatalf("failed to connect: %v", err)
	}
	defer conn.Close()

	// 2️⃣ Create client
	client := pb.NewVectorSearchServiceClient(conn)

	// 3️⃣ Call the service
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	resp, err := client.Search(ctx, &pb.SearchRequest{
		Query: "Our highway system is racist",
		K: 5,
	})
	if err != nil {
		log.Fatalf("Search failed: %v", err)
	}

	// 4️⃣ Print result
	fmt.Println("Response:", resp.Results)


	uids := make([]string, 0, len(resp.Results))

	for _, r := range resp.Results {
		uids = append(uids, r.Uid)
	}

	metadatas := store.Get(uids)

	for _, m := range metadatas {
    	fmt.Println(m.Statement)
}
}
