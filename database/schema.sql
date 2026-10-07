-- Run as a database administrator: mysql -u root -p < database/schema.sql
CREATE DATABASE IF NOT EXISTS document_ai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE document_ai;

CREATE TABLE IF NOT EXISTS documents (
  id VARCHAR(36) PRIMARY KEY,
  filename VARCHAR(180) NOT NULL,
  file_hash VARCHAR(64) NOT NULL,
  file_size INTEGER NOT NULL,
  page_count INTEGER NOT NULL DEFAULT 0,
  chunk_count INTEGER NOT NULL DEFAULT 0,
  uploaded_at DATETIME NOT NULL,
  processing_status VARCHAR(20) NOT NULL DEFAULT 'processing',
  embedding_ms DOUBLE NOT NULL DEFAULT 0,
  indexing_ms DOUBLE NOT NULL DEFAULT 0,
  CONSTRAINT uq_document_hash UNIQUE (file_hash)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS queries (
  id VARCHAR(36) PRIMARY KEY,
  actor_role VARCHAR(10) NOT NULL,
  query_text TEXT NOT NULL,
  response_text TEXT NOT NULL,
  created_at DATETIME NOT NULL,
  retrieval_count INTEGER NOT NULL,
  retrieval_ms DOUBLE NOT NULL,
  embedding_ms DOUBLE NOT NULL,
  llm_ms DOUBLE NOT NULL,
  duration_ms DOUBLE NOT NULL,
  outcome VARCHAR(30) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS query_sources (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  query_id VARCHAR(36) NOT NULL,
  document_id VARCHAR(36) NOT NULL,
  page_number INTEGER NOT NULL,
  chunk_id VARCHAR(36) NOT NULL,
  similarity_score DOUBLE NOT NULL,
  INDEX ix_query_sources_query_id (query_id),
  INDEX ix_query_sources_document_id (document_id),
  FOREIGN KEY (query_id) REFERENCES queries(id) ON DELETE CASCADE,
  FOREIGN KEY (document_id) REFERENCES documents(id)
) ENGINE=InnoDB;
