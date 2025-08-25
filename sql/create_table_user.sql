CREATE TABLE users (
	id SERIAL PRIMARY KEY,
	username VARCHAR(50) UNIQUE NOT NULL,
	email VARCHAR(120) UNIQUE NOT NULL,
	password_hash VARCHAR(128) NOT NULL,
	jellyfin_user_id VARCHAR(36),
	jellyfin_session_token VARCHAR(128),
	jellyfin_device_id VARCHAR(36)
);
