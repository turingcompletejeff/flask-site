CREATE TABLE IF NOT EXISTS public.blog_posts (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    thumbnail TEXT,
    portrait TEXT,
    themap JSON,
    date_posted DATE NOT NULL DEFAULT CURRENT_DATE,
    last_updated TIMESTAMPTZ
);

ALTER TABLE IF EXISTS public.blog_posts OWNER TO flasker;
GRANT ALL ON TABLE public.blog_posts TO flasker;
GRANT USAGE, SELECT ON SEQUENCE blog_posts_id_seq TO flasker;

COMMENT ON TABLE public.blog_posts IS 'collection of post material: text, images';
COMMENT ON COLUMN public.blog_posts.thumbnail IS 'path to the thumbnail image, not the image itself';
