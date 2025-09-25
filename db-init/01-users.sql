CREATE TABLE IF NOT EXISTS public.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);

ALTER TABLE IF EXISTS public.users OWNER TO flasker;
GRANT ALL ON TABLE public.users TO flasker;
GRANT USAGE, SELECT ON SEQUENCE users_id_seq TO flasker;
