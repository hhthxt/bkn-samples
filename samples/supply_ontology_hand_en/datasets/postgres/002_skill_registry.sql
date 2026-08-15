CREATE TABLE IF NOT EXISTS public.skills (
    skill_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    version TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'published',
    business_domain_id TEXT NOT NULL DEFAULT '',
    kn_id TEXT NOT NULL,
    object_type_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    skill_query TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_skills_status ON public.skills (status);
CREATE INDEX IF NOT EXISTS idx_skills_kn_id ON public.skills (kn_id);
