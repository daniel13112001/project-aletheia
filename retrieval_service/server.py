import grpc
from concurrent import futures
import signal
import sys
from dotenv import load_dotenv
from openai import OpenAI
import os
from ingestion.VectorStores.faiss_vector_store import FaissVectorStore
from ingestion.MetadataStores.in_memory_metadata_store import InMemoryMetadataStore
from . import vector_search_pb2
from . import vector_search_pb2_grpc
from pathlib import Path

class VectorSearchServicer(
    vector_search_pb2_grpc.VectorSearchServiceServicer
):
    def Search(self, request, context):

        query = request.query
        k = request.k or 3

        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not set")
      
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        #TODO: Make this path dynamic
        vector_store = FaissVectorStore.load("/Users/danielyakubu/Documents/Projects/project-aletheia/artifacts/faiss")
        print("FAISS index size:", vector_store.index.ntotal)

        print("Query:", request.query, "k:", request.k)
        print("FAISS ntotal:", vector_store.index.ntotal)

        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=query,
            encoding_format="float",
        )

        query_embedding = response.data[0].embedding
        ids, scores = vector_store.query(query_embedding, k)

        return vector_search_pb2.SearchResponse(
        results=[
            vector_search_pb2.SearchResult(uid=str(uid), score=float(score))
            for uid, score in zip(ids, scores)
        ]
)




def serve():
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10)
    )

    vector_search_pb2_grpc.add_VectorSearchServiceServicer_to_server(
        VectorSearchServicer(),
        server,
    )

    server.add_insecure_port("[::]:50051")
    server.start()
    print("VectorSearch gRPC server running on :50051")

    # Graceful shutdown
    signal.signal(signal.SIGTERM, lambda *_: server.stop(0))
    signal.signal(signal.SIGINT, lambda *_: server.stop(0))

    server.wait_for_termination()


if __name__ == "__main__":
    serve()
