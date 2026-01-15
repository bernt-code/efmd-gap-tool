-- ============================================================
-- EFMD GAP ANALYSIS TOOL - SUPABASE SCHEMA
-- ============================================================
-- Run this in Supabase SQL Editor
-- Requires: pgvector extension (enabled by default in Supabase)
-- ============================================================

-- Enable pgvector if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- 1. EFMD REQUIREMENTS (Reference Data)
-- ============================================================
-- These are the EFMD standards we match against
-- Embeddings allow semantic matching across languages

CREATE TABLE IF NOT EXISTS efmd_requirements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Classification
    pillar TEXT NOT NULL,              -- 'International', 'Practice', 'ERS', 'Digital', 'Core'
    chapter TEXT,                       -- 'Programme', 'Students', 'Faculty', 'Resources'
    category TEXT,                      -- 'ILO', 'Curriculum', 'Assessment', 'Eligibility'
    requirement_code TEXT,              -- e.g., 'ELG-4', 'STD-2.3'
    
    -- Content
    requirement_text TEXT NOT NULL,     -- The actual requirement text
    description TEXT,                   -- Longer explanation
    evidence_expected TEXT[],           -- What evidence EFMD expects
    
    -- Semantic matching
    embedding vector(768),              -- Gemini text-embedding-004
    
    -- Metadata
    is_eligibility_gate BOOLEAN DEFAULT FALSE,
    is_critical BOOLEAN DEFAULT FALSE,  -- Automatic fail if missing
    weight INTEGER DEFAULT 1,           -- For scoring (1-3)
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for semantic search
CREATE INDEX IF NOT EXISTS idx_efmd_requirements_embedding 
ON efmd_requirements USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10);

-- ============================================================
-- 2. PROGRAMMES (Scraped/Imported Programmes)
-- ============================================================

CREATE TABLE IF NOT EXISTS programmes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Basic info
    institution TEXT NOT NULL,
    programme_name TEXT NOT NULL,
    degree_type TEXT,                   -- 'MSc', 'MBA', 'BSc', 'PhD'
    
    -- URLs (may have multiple language versions)
    primary_url TEXT,
    urls_scraped TEXT[],                -- All URLs we pulled from
    
    -- Programme details
    duration_months INTEGER,
    total_ects INTEGER,
    delivery_mode TEXT,                 -- 'Full-time', 'Part-time', 'Online', 'Hybrid'
    languages_of_instruction TEXT[],    -- ['English', 'Norwegian']
    
    -- Raw content (for re-processing)
    raw_html TEXT,
    raw_text TEXT,
    
    -- Analysis results (cached)
    readiness_score INTEGER,            -- 0-100
    last_analysis_at TIMESTAMPTZ,
    analysis_version TEXT,              -- Track which version of analyzer was used
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID                     -- If user-submitted
);

-- ============================================================
-- 3. PROGRAMME ILOs (Individual Learning Outcomes)
-- ============================================================
-- One row per ILO, with embedding for semantic matching

CREATE TABLE IF NOT EXISTS programme_ilos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    programme_id UUID NOT NULL REFERENCES programmes(id) ON DELETE CASCADE,
    
    -- Content
    ilo_text TEXT NOT NULL,
    ilo_order INTEGER,                  -- 1st, 2nd, 3rd ILO in sequence
    source_language TEXT DEFAULT 'en',  -- ISO 639-1 code
    source_url TEXT,                    -- Which page it came from
    
    -- Classification (from analysis)
    ksa_category TEXT,                  -- 'Knowledge', 'Skill', 'Attitude', NULL
    verb_found TEXT,                    -- The action verb detected
    has_weak_verb BOOLEAN DEFAULT FALSE,
    is_measurable BOOLEAN DEFAULT TRUE,
    quality_issues TEXT[],              -- Array of issues found
    
    -- Semantic matching
    embedding vector(768),
    
    -- Matched requirements (denormalized for speed)
    matched_pillars TEXT[],             -- Which EFMD pillars this ILO covers
    best_match_score FLOAT,             -- Highest similarity to any requirement
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_programme_ilos_programme 
ON programme_ilos(programme_id);

CREATE INDEX IF NOT EXISTS idx_programme_ilos_embedding 
ON programme_ilos USING ivfflat (embedding vector_cosine_ops) WITH (lists = 20);

-- ============================================================
-- 4. PROGRAMME COURSES
-- ============================================================

CREATE TABLE IF NOT EXISTS programme_courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    programme_id UUID NOT NULL REFERENCES programmes(id) ON DELETE CASCADE,
    
    -- Content
    title TEXT NOT NULL,
    description TEXT,
    source_language TEXT DEFAULT 'en',
    
    -- Structure
    ects FLOAT,
    year INTEGER,                       -- Year 1, 2, etc.
    semester TEXT,                      -- 'Fall', 'Spring', 'Summer'
    is_mandatory BOOLEAN,
    
    -- Course-level ILOs (if available)
    course_ilos TEXT[],
    
    -- Semantic matching
    embedding vector(768),              -- Embed title + description
    
    -- Matched requirements
    matched_pillars TEXT[],
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_programme_courses_programme 
ON programme_courses(programme_id);

CREATE INDEX IF NOT EXISTS idx_programme_courses_embedding 
ON programme_courses USING ivfflat (embedding vector_cosine_ops) WITH (lists = 20);

-- ============================================================
-- 5. GAP ANALYSES (Cached Results)
-- ============================================================

CREATE TABLE IF NOT EXISTS gap_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    programme_id UUID NOT NULL REFERENCES programmes(id) ON DELETE CASCADE,
    
    -- Scores
    readiness_score INTEGER,            -- 0-100
    eligibility_pass BOOLEAN,           -- Would pass eligibility gates?
    
    -- Detailed results (JSONB for flexibility)
    ilo_analysis JSONB,                 -- ILO count, K/S/A coverage, weak verbs
    pillar_coverage JSONB,              -- Which pillars covered, scores
    eligibility_gates JSONB,            -- Each gate: pass/fail/unknown
    structure_issues JSONB,             -- ECTS, duration, etc.
    
    -- Recommendations
    critical_gaps TEXT[],
    recommendations TEXT[],
    estimated_fix_months INTEGER,
    
    -- For report generation
    report_generated_at TIMESTAMPTZ,
    report_url TEXT,                    -- Link to PDF if generated
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    analyzer_version TEXT DEFAULT '1.0'
);

CREATE INDEX IF NOT EXISTS idx_gap_analyses_programme 
ON gap_analyses(programme_id);

-- ============================================================
-- 6. SEMANTIC MATCHING FUNCTION
-- ============================================================
-- Match any text against EFMD requirements

CREATE OR REPLACE FUNCTION match_to_requirements(
    query_embedding vector(768),
    match_threshold FLOAT DEFAULT 0.5,
    match_limit INTEGER DEFAULT 5
)
RETURNS TABLE(
    requirement_id UUID,
    pillar TEXT,
    category TEXT,
    requirement_text TEXT,
    similarity FLOAT
)
LANGUAGE sql
STABLE
AS $$
    SELECT 
        id as requirement_id,
        pillar,
        category,
        requirement_text,
        1 - (embedding <=> query_embedding) as similarity
    FROM efmd_requirements
    WHERE embedding IS NOT NULL
      AND 1 - (embedding <=> query_embedding) > match_threshold
    ORDER BY embedding <=> query_embedding
    LIMIT match_limit;
$$;

-- ============================================================
-- 7. PILLAR COVERAGE FUNCTION
-- ============================================================
-- Get pillar coverage for a programme based on semantic matching

CREATE OR REPLACE FUNCTION get_programme_pillar_coverage(
    p_programme_id UUID,
    match_threshold FLOAT DEFAULT 0.55
)
RETURNS TABLE(
    pillar TEXT,
    coverage_score FLOAT,
    matching_ilos INTEGER,
    matching_courses INTEGER,
    best_match_text TEXT
)
LANGUAGE sql
STABLE
AS $$
    WITH ilo_matches AS (
        SELECT DISTINCT ON (er.pillar)
            er.pillar,
            1 - (pi.embedding <=> er.embedding) as similarity,
            pi.ilo_text
        FROM programme_ilos pi
        CROSS JOIN efmd_requirements er
        WHERE pi.programme_id = p_programme_id
          AND pi.embedding IS NOT NULL
          AND er.embedding IS NOT NULL
          AND 1 - (pi.embedding <=> er.embedding) > match_threshold
        ORDER BY er.pillar, pi.embedding <=> er.embedding
    ),
    course_matches AS (
        SELECT DISTINCT ON (er.pillar)
            er.pillar,
            1 - (pc.embedding <=> er.embedding) as similarity
        FROM programme_courses pc
        CROSS JOIN efmd_requirements er
        WHERE pc.programme_id = p_programme_id
          AND pc.embedding IS NOT NULL
          AND er.embedding IS NOT NULL
          AND 1 - (pc.embedding <=> er.embedding) > match_threshold
        ORDER BY er.pillar, pc.embedding <=> er.embedding
    ),
    ilo_counts AS (
        SELECT er.pillar, COUNT(DISTINCT pi.id) as cnt
        FROM programme_ilos pi
        CROSS JOIN efmd_requirements er
        WHERE pi.programme_id = p_programme_id
          AND pi.embedding IS NOT NULL
          AND er.embedding IS NOT NULL
          AND 1 - (pi.embedding <=> er.embedding) > match_threshold
        GROUP BY er.pillar
    ),
    course_counts AS (
        SELECT er.pillar, COUNT(DISTINCT pc.id) as cnt
        FROM programme_courses pc
        CROSS JOIN efmd_requirements er
        WHERE pc.programme_id = p_programme_id
          AND pc.embedding IS NOT NULL
          AND er.embedding IS NOT NULL
          AND 1 - (pc.embedding <=> er.embedding) > match_threshold
        GROUP BY er.pillar
    )
    SELECT 
        p.pillar,
        GREATEST(
            COALESCE(im.similarity, 0),
            COALESCE(cm.similarity, 0)
        ) as coverage_score,
        COALESCE(ic.cnt, 0)::INTEGER as matching_ilos,
        COALESCE(cc.cnt, 0)::INTEGER as matching_courses,
        im.ilo_text as best_match_text
    FROM (SELECT DISTINCT pillar FROM efmd_requirements) p
    LEFT JOIN ilo_matches im ON im.pillar = p.pillar
    LEFT JOIN course_matches cm ON cm.pillar = p.pillar
    LEFT JOIN ilo_counts ic ON ic.pillar = p.pillar
    LEFT JOIN course_counts cc ON cc.pillar = p.pillar
    ORDER BY p.pillar;
$$;

-- ============================================================
-- 8. HYBRID SEARCH FOR PROGRAMMES
-- ============================================================
-- Search programmes by institution/name + filter by readiness

CREATE OR REPLACE FUNCTION search_programmes(
    search_query TEXT DEFAULT NULL,
    min_score INTEGER DEFAULT 0,
    max_score INTEGER DEFAULT 100,
    result_limit INTEGER DEFAULT 20
)
RETURNS TABLE(
    id UUID,
    institution TEXT,
    programme_name TEXT,
    degree_type TEXT,
    readiness_score INTEGER,
    last_analysis_at TIMESTAMPTZ
)
LANGUAGE sql
STABLE
AS $$
    SELECT 
        p.id,
        p.institution,
        p.programme_name,
        p.degree_type,
        p.readiness_score,
        p.last_analysis_at
    FROM programmes p
    WHERE (search_query IS NULL 
           OR p.institution ILIKE '%' || search_query || '%'
           OR p.programme_name ILIKE '%' || search_query || '%')
      AND (p.readiness_score IS NULL 
           OR p.readiness_score BETWEEN min_score AND max_score)
    ORDER BY p.updated_at DESC
    LIMIT result_limit;
$$;

-- ============================================================
-- 9. UPDATED_AT TRIGGER
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at
DROP TRIGGER IF EXISTS update_programmes_updated_at ON programmes;
CREATE TRIGGER update_programmes_updated_at
    BEFORE UPDATE ON programmes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS update_efmd_requirements_updated_at ON efmd_requirements;
CREATE TRIGGER update_efmd_requirements_updated_at
    BEFORE UPDATE ON efmd_requirements
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- DONE
-- ============================================================
-- Next: Run 002_seed_requirements.sql to populate EFMD requirements
