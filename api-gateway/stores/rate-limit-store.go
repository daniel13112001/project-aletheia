package stores

import (
	"github.com/redis/go-redis/v9"
	"context"
	"time"
)

type RateLimitStore interface{
	Incr(ctx context.Context, key string) (int64, error)
	Expire(ctx context.Context, key string, ttl time.Duration) error
	SetVar(ctx context.Context, key string, value string, ttl time.Duration) error
	GetVar(ctx context.Context, key string) (string, error)
}


type RedisRateLimitStore struct{
	client *redis.Client 
}

func NewRedisRateLimitStore(client *redis.Client) *RedisRateLimitStore {
	return &RedisRateLimitStore{client: client}
}

func (r *RedisRateLimitStore) Incr(ctx context.Context, key string) (int64, error) {
	return r.client.Incr(ctx, key).Result()
}

func (r *RedisRateLimitStore) Expire(ctx context.Context, key string, ttl time.Duration) error{
	return r.client.Expire(ctx, key, ttl).Err()
}

func (r *RedisRateLimitStore) SetVar(ctx context.Context, key, value string, ttl time.Duration) error {
	return r.client.Set(ctx, key, value, ttl).Err()
}

func (r *RedisRateLimitStore) GetVar(ctx context.Context, key string) (string, error) {
	return r.client.Get(ctx, key).Result()
}



