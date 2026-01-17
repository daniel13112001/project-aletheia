package stores

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"os"
)

type ClaimMetaData struct {
	UID                   string  `json:"uid"`
	Statement             string  `json:"statement"`
	Verdict               string  `json:"verdict"`
	StatementOriginator   string  `json:"statement_originator"`
	StatementDate         string  `json:"statement_date"`
	StatementSource       string  `json:"statement_source"`
	FactChecker           string  `json:"factchecker"`
	FactCheckDate         *string `json:"factcheck_date"`
	FactCheckAnalysisLink string  `json:"factcheck_analysis_link"`
}

type MetadataStore interface {
	Get(ctx context.Context, uids []string) ([]ClaimMetaData, error)
}

type InMemoryMetadataStore struct {
	path string
	data map[string]ClaimMetaData
}

func NewInMemoryMetadataStore(path string) (*InMemoryMetadataStore, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)

	data := make(map[string]ClaimMetaData)

	for scanner.Scan() {
		var meta ClaimMetaData

		if err := json.Unmarshal(scanner.Bytes(), &meta); err != nil {
			return nil, err
		}

		// Safety check: ensure UID exists
		if meta.UID == "" {
			return nil, fmt.Errorf("metadata record missing uid")
		}

		data[meta.UID] = meta
	}

	if err := scanner.Err(); err != nil {
		return nil, err
	}

	return &InMemoryMetadataStore{
		path: path,
		data: data,
	}, nil
}

func (s *InMemoryMetadataStore) Get(
	ctx context.Context,
	uids []string,
) ([]ClaimMetaData, error) {

	results := make([]ClaimMetaData, 0, len(uids))

	for _, uid := range uids {
		if meta, ok := s.data[uid]; ok {
			results = append(results, meta)
		}
	}

	return results, nil
}
