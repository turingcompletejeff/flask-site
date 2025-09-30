CREATE TABLE IF NOT EXISTS public.minecraft_commands (
    command_id SERIAL PRIMARY KEY,  -- Ensured proper primary key
    command_name VARCHAR(20),
    options VARCHAR(40)[]
);

ALTER TABLE IF EXISTS public.minecraft_commands OWNER TO flasker;
GRANT ALL ON TABLE public.minecraft_commands TO flasker;
GRANT USAGE, SELECT ON SEQUENCE minecraft_commands_command_id_seq TO flasker;
