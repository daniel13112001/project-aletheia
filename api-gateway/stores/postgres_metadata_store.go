package stores

import (
	"context"
	"database/sql"
)

type PostgresMetadataStore struct {
	db *sql.DB
}

func NewPostgresMetadataStore(db *sql.DB) *PostgresMetadataStore {
	return &PostgresMetadataStore{db: db}
}


func (s *PostgresMetadataStore) Get(uids []string) ([]ClaimMetaData, error) {
	if len(uids) == 0 {
		return nil, nil
	}

	query := `
		SELECT
			uid,
			statement,
			verdict,
			statement_originator,
			statement_date,
			statement_source,
			factchecker,
			factcheck_date,
			factcheck_analysis_link
		FROM claim_metadata
		WHERE uid = ANY($1)
	`

	rows, err := s.db.QueryContext(
		context.Background(),
		query,
		uids, 
	)

	if err != nil {
		return nil, err
	}
	defer rows.Close()

	results := make([]ClaimMetaData, 0, len(uids))

	for rows.Next() {
		var meta ClaimMetaData
		if err := rows.Scan(
			&meta.UID,
			&meta.Statement,
			&meta.Verdict,
			&meta.StatementOriginator,
			&meta.StatementDate,
			&meta.StatementSource,
			&meta.FactChecker,
			&meta.FactCheckDate,
			&meta.FactCheckAnalysisLink,
		); err != nil {
			return nil, err
		}

		results = append(results, meta)
	}

	if err := rows.Err(); err != nil {
		return nil, err
	}

	return results, nil
}
