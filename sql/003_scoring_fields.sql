-- ============================================================
-- EFMD SCORING & SELECTION FIELDS
-- Run this in Supabase SQL Editor to add scoring capabilities
-- ============================================================

-- FACULTY CV SCORING FIELDS
ALTER TABLE faculty_cvs ADD COLUMN IF NOT EXISTS efmd_score INTEGER DEFAULT 0;
ALTER TABLE faculty_cvs ADD COLUMN IF NOT EXISTS include_recommended BOOLEAN DEFAULT FALSE;
ALTER TABLE faculty_cvs ADD COLUMN IF NOT EXISTS inclusion_reasons TEXT[];
ALTER TABLE faculty_cvs ADD COLUMN IF NOT EXISTS exclusion_risks TEXT[];
ALTER TABLE faculty_cvs ADD COLUMN IF NOT EXISTS score_breakdown JSONB;
-- Breakdown: {phd: 20, publications: 15, international: 15, industry: 10, ...}

-- STUDENT CV SCORING FIELDS
ALTER TABLE student_cvs ADD COLUMN IF NOT EXISTS efmd_score INTEGER DEFAULT 0;
ALTER TABLE student_cvs ADD COLUMN IF NOT EXISTS include_recommended BOOLEAN DEFAULT FALSE;
ALTER TABLE student_cvs ADD COLUMN IF NOT EXISTS inclusion_reasons TEXT[];
ALTER TABLE student_cvs ADD COLUMN IF NOT EXISTS exclusion_risks TEXT[];
ALTER TABLE student_cvs ADD COLUMN IF NOT EXISTS score_breakdown JSONB;
-- Breakdown: {prior_education: 20, work_experience: 15, diversity_value: 15, ...}

-- ALUMNI CV SCORING FIELDS
ALTER TABLE alumni_cvs ADD COLUMN IF NOT EXISTS efmd_score INTEGER DEFAULT 0;
ALTER TABLE alumni_cvs ADD COLUMN IF NOT EXISTS include_recommended BOOLEAN DEFAULT FALSE;
ALTER TABLE alumni_cvs ADD COLUMN IF NOT EXISTS inclusion_reasons TEXT[];
ALTER TABLE alumni_cvs ADD COLUMN IF NOT EXISTS exclusion_risks TEXT[];
ALTER TABLE alumni_cvs ADD COLUMN IF NOT EXISTS score_breakdown JSONB;
-- Breakdown: {employment_speed: 25, employer_prestige: 20, international: 15, ...}

-- ============================================================
-- PROGRAMME COLLECTION STATUS VIEW
-- Shows data collection progress for each programme
-- ============================================================

CREATE OR REPLACE VIEW programme_collection_status AS
SELECT 
    p.id as programme_id,
    p.programme_name,
    i.name as institution_name,
    
    -- Faculty counts (institution level)
    (SELECT COUNT(*) FROM faculty_cvs f WHERE f.institution_id = i.id) as faculty_total,
    (SELECT COUNT(*) FROM faculty_cvs f WHERE f.institution_id = i.id AND f.include_recommended = true) as faculty_recommended,
    (SELECT AVG(efmd_score) FROM faculty_cvs f WHERE f.institution_id = i.id)::INTEGER as faculty_avg_score,
    
    -- Student counts
    (SELECT COUNT(*) FROM student_cvs s WHERE s.programme_id = p.id) as students_total,
    (SELECT COUNT(*) FROM student_cvs s WHERE s.programme_id = p.id AND s.include_recommended = true) as students_recommended,
    (SELECT AVG(efmd_score) FROM student_cvs s WHERE s.programme_id = p.id)::INTEGER as students_avg_score,
    
    -- Alumni counts
    (SELECT COUNT(*) FROM alumni_cvs a WHERE a.programme_id = p.id) as alumni_total,
    (SELECT COUNT(*) FROM alumni_cvs a WHERE a.programme_id = p.id AND a.include_recommended = true) as alumni_recommended,
    (SELECT AVG(efmd_score) FROM alumni_cvs a WHERE a.programme_id = p.id)::INTEGER as alumni_avg_score,
    
    -- Programme analysis
    p.readiness_score,
    p.last_analysis_at

FROM programmes p
JOIN institutions i ON p.institution_id = i.id;

-- ============================================================
-- FACULTY AGGREGATION FOR EFMD TABLE 9
-- Generates Table 9 statistics from selected faculty
-- ============================================================

CREATE OR REPLACE FUNCTION get_faculty_table9(p_institution_id UUID, selected_only BOOLEAN DEFAULT TRUE)
RETURNS TABLE (
    total_faculty INTEGER,
    total_fte FLOAT,
    professors INTEGER,
    associate_professors INTEGER,
    assistant_professors INTEGER,
    other_titles INTEGER,
    female_count INTEGER,
    female_percentage FLOAT,
    with_doctorate INTEGER,
    doctorate_percentage FLOAT,
    international_exp INTEGER,
    international_percentage FLOAT,
    nationalities INTEGER,
    hired_last_3yr INTEGER,
    adjunct_count INTEGER,
    visiting_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    WITH faculty AS (
        SELECT * FROM faculty_cvs 
        WHERE institution_id = p_institution_id
        AND (NOT selected_only OR include_recommended = true)
    )
    SELECT
        COUNT(*)::INTEGER as total_faculty,
        COALESCE(SUM(COALESCE(fte_percentage, 100) / 100.0), 0)::FLOAT as total_fte,
        COUNT(*) FILTER (WHERE current_title ILIKE '%professor%' AND current_title NOT ILIKE '%associate%' AND current_title NOT ILIKE '%assistant%')::INTEGER as professors,
        COUNT(*) FILTER (WHERE current_title ILIKE '%associate professor%')::INTEGER as associate_professors,
        COUNT(*) FILTER (WHERE current_title ILIKE '%assistant professor%' OR current_title ILIKE '%lecturer%')::INTEGER as assistant_professors,
        COUNT(*) FILTER (WHERE current_title NOT ILIKE '%professor%' AND current_title NOT ILIKE '%lecturer%')::INTEGER as other_titles,
        COUNT(*) FILTER (WHERE cv_text ILIKE '%she %' OR cv_text ILIKE '%her %' OR full_name ILIKE 'dr. m%' OR full_name ILIKE 'prof. m%')::INTEGER as female_count, -- Rough heuristic
        (COUNT(*) FILTER (WHERE cv_text ILIKE '%she %' OR cv_text ILIKE '%her %') * 100.0 / NULLIF(COUNT(*), 0))::FLOAT as female_percentage,
        COUNT(*) FILTER (WHERE highest_degree ILIKE '%phd%' OR highest_degree ILIKE '%doctor%' OR highest_degree ILIKE '%dba%' OR highest_degree ILIKE '%dphil%')::INTEGER as with_doctorate,
        (COUNT(*) FILTER (WHERE highest_degree ILIKE '%phd%' OR highest_degree ILIKE '%doctor%' OR highest_degree ILIKE '%dba%') * 100.0 / NULLIF(COUNT(*), 0))::FLOAT as doctorate_percentage,
        COUNT(*) FILTER (WHERE international_experience_years > 0 OR (international_education IS NOT NULL AND jsonb_array_length(international_education) > 0))::INTEGER as international_exp,
        (COUNT(*) FILTER (WHERE international_experience_years > 0) * 100.0 / NULLIF(COUNT(*), 0))::FLOAT as international_percentage,
        COUNT(DISTINCT (languages->0->>'language'))::INTEGER as nationalities, -- Rough proxy
        COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '3 years')::INTEGER as hired_last_3yr,
        COUNT(*) FILTER (WHERE employment_type ILIKE '%adjunct%' OR employment_type ILIKE '%part%')::INTEGER as adjunct_count,
        COUNT(*) FILTER (WHERE employment_type ILIKE '%visiting%')::INTEGER as visiting_count
    FROM faculty;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- ALUMNI AGGREGATION FOR EFMD TABLE 4
-- Generates Table 4 employment statistics from selected alumni
-- ============================================================

CREATE OR REPLACE FUNCTION get_alumni_table4(p_programme_id UUID, selected_only BOOLEAN DEFAULT TRUE)
RETURNS TABLE (
    total_alumni INTEGER,
    employed_count INTEGER,
    employment_rate FLOAT,
    avg_months_to_employment FLOAT,
    working_abroad INTEGER,
    working_abroad_percentage FLOAT,
    top_employers TEXT[],
    top_industries TEXT[],
    career_levels JSONB
) AS $$
BEGIN
    RETURN QUERY
    WITH alumni AS (
        SELECT * FROM alumni_cvs 
        WHERE programme_id = p_programme_id
        AND (NOT selected_only OR include_recommended = true)
    )
    SELECT
        COUNT(*)::INTEGER as total_alumni,
        COUNT(*) FILTER (WHERE employed = true)::INTEGER as employed_count,
        (COUNT(*) FILTER (WHERE employed = true) * 100.0 / NULLIF(COUNT(*), 0))::FLOAT as employment_rate,
        AVG(months_to_employment)::FLOAT as avg_months_to_employment,
        COUNT(*) FILTER (WHERE working_abroad = true)::INTEGER as working_abroad,
        (COUNT(*) FILTER (WHERE working_abroad = true) * 100.0 / NULLIF(COUNT(*), 0))::FLOAT as working_abroad_percentage,
        ARRAY(SELECT current_employer FROM alumni GROUP BY current_employer ORDER BY COUNT(*) DESC LIMIT 10) as top_employers,
        ARRAY(SELECT current_industry FROM alumni WHERE current_industry IS NOT NULL GROUP BY current_industry ORDER BY COUNT(*) DESC LIMIT 5) as top_industries,
        jsonb_build_object(
            'entry', COUNT(*) FILTER (WHERE career_level = 'Entry'),
            'mid', COUNT(*) FILTER (WHERE career_level = 'Mid'),
            'senior', COUNT(*) FILTER (WHERE career_level = 'Senior'),
            'executive', COUNT(*) FILTER (WHERE career_level = 'Executive')
        ) as career_levels
    FROM alumni;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- STUDENT DIVERSITY METRICS FOR EFMD TABLE 2/3
-- ============================================================

CREATE OR REPLACE FUNCTION get_student_diversity(p_programme_id UUID, selected_only BOOLEAN DEFAULT TRUE)
RETURNS TABLE (
    total_students INTEGER,
    nationalities_count INTEGER,
    top_nationalities JSONB,
    gender_breakdown JSONB,
    avg_age FLOAT,
    avg_work_experience FLOAT,
    prior_degree_types JSONB,
    business_background_pct FLOAT
) AS $$
BEGIN
    RETURN QUERY
    WITH students AS (
        SELECT * FROM student_cvs 
        WHERE programme_id = p_programme_id
        AND (NOT selected_only OR include_recommended = true)
    )
    SELECT
        COUNT(*)::INTEGER as total_students,
        COUNT(DISTINCT nationality)::INTEGER as nationalities_count,
        (SELECT jsonb_object_agg(nationality, cnt) FROM (
            SELECT nationality, COUNT(*) as cnt FROM students WHERE nationality IS NOT NULL GROUP BY nationality ORDER BY cnt DESC LIMIT 10
        ) t) as top_nationalities,
        jsonb_build_object(
            'male', COUNT(*) FILTER (WHERE gender ILIKE '%male%' AND gender NOT ILIKE '%female%'),
            'female', COUNT(*) FILTER (WHERE gender ILIKE '%female%'),
            'other', COUNT(*) FILTER (WHERE gender IS NOT NULL AND gender NOT ILIKE '%male%' AND gender NOT ILIKE '%female%')
        ) as gender_breakdown,
        AVG(age_at_entry)::FLOAT as avg_age,
        AVG(work_experience_years)::FLOAT as avg_work_experience,
        (SELECT jsonb_object_agg(prior_degree, cnt) FROM (
            SELECT prior_degree, COUNT(*) as cnt FROM students WHERE prior_degree IS NOT NULL GROUP BY prior_degree ORDER BY cnt DESC LIMIT 5
        ) t) as prior_degree_types,
        (COUNT(*) FILTER (WHERE prior_degree_field ILIKE '%business%' OR prior_degree_field ILIKE '%management%' OR prior_degree_field ILIKE '%economics%' OR prior_degree_field ILIKE '%finance%') * 100.0 / NULLIF(COUNT(*), 0))::FLOAT as business_background_pct
    FROM students;
END;
$$ LANGUAGE plpgsql;
