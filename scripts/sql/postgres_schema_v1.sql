-- PostgreSQL schema bootstrap v1 for GitHub Follower Bot
CREATE TABLE IF NOT EXISTS bot_runs (
  id BIGSERIAL PRIMARY KEY,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  status TEXT NOT NULL,
  trace_id TEXT,
  followers_fetched INTEGER NOT NULL DEFAULT 0,
  followers_followed INTEGER NOT NULL DEFAULT 0,
  error_message TEXT
);

CREATE TABLE IF NOT EXISTS followers (
  github_login TEXT PRIMARY KEY,
  first_seen_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  followed INTEGER NOT NULL DEFAULT 0,
  followed_at TEXT
);

CREATE TABLE IF NOT EXISTS follow_actions (
  id BIGSERIAL PRIMARY KEY,
  run_id BIGINT NOT NULL REFERENCES bot_runs(id),
  github_login TEXT NOT NULL,
  success INTEGER NOT NULL,
  status_code INTEGER,
  error_message TEXT,
  discovery_context JSONB,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS security_events (
  id BIGSERIAL PRIMARY KEY,
  run_id BIGINT REFERENCES bot_runs(id),
  event TEXT NOT NULL,
  details TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rate_limit_snapshots (
  id BIGSERIAL PRIMARY KEY,
  run_id BIGINT REFERENCES bot_runs(id),
  remaining INTEGER,
  reset_at INTEGER,
  captured_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS follow_jobs (
  id BIGSERIAL PRIMARY KEY,
  run_id BIGINT NOT NULL REFERENCES bot_runs(id),
  github_login TEXT NOT NULL,
  status TEXT NOT NULL,
  attempts INTEGER NOT NULL DEFAULT 0,
  last_error TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(run_id, github_login)
);

CREATE TABLE IF NOT EXISTS repository_catalog (
  full_name TEXT PRIMARY KEY,
  owner_login TEXT NOT NULL,
  repo_name TEXT NOT NULL,
  is_fork BOOLEAN NOT NULL DEFAULT FALSE,
  parent_full_name TEXT,
  source_root_full_name TEXT,
  last_seen_at TEXT NOT NULL,
  repo_updated_at TEXT,
  stargazers_count INTEGER,
  forks_count INTEGER,
  watchers_count INTEGER,
  open_issues_count INTEGER,
  language TEXT,
  default_branch TEXT,
  archived BOOLEAN,
  disabled BOOLEAN,
  pushed_at TEXT,
  last_forked_at TEXT,
  last_fork_status TEXT,
  last_fork_error TEXT
);

CREATE INDEX IF NOT EXISTS idx_followers_followed ON followers(followed);
CREATE INDEX IF NOT EXISTS idx_follow_actions_run ON follow_actions(run_id);
CREATE INDEX IF NOT EXISTS idx_rate_limit_snapshots_run ON rate_limit_snapshots(run_id);
CREATE INDEX IF NOT EXISTS idx_follow_jobs_run_status ON follow_jobs(run_id, status);
CREATE INDEX IF NOT EXISTS idx_security_events_run ON security_events(run_id);
CREATE INDEX IF NOT EXISTS idx_repository_catalog_owner ON repository_catalog(owner_login);
