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


func (s *PostgresMetadataStore) Get(
	ctx context.Context,
	uids []string,
) ([]ClaimMetaData, error) {

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
		ctx,
		query,
		uids,
	)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	// 1️⃣ Read all rows into a map
	byUID := make(map[string]ClaimMetaData, len(uids))

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

		byUID[meta.UID] = meta
	}

	if err := rows.Err(); err != nil {
		return nil, err
	}

	// 2️⃣ Rebuild slice in input order
	ordered := make([]ClaimMetaData, 0, len(uids))
	for _, uid := range uids {
		if meta, ok := byUID[uid]; ok {
			ordered = append(ordered, meta)
		}
	}

	return ordered, nil
}
