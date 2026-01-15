-- ============================================================
-- EFMD REQUIREMENTS SEED DATA
-- ============================================================
-- These are the core EFMD Programme Accreditation requirements
-- Embeddings will be generated via API after insert
-- Run AFTER 001_schema.sql
-- ============================================================

-- Clear existing (for re-seeding)
-- TRUNCATE efmd_requirements CASCADE;

-- ============================================================
-- ELIGIBILITY GATES (10 Pass/Fail Criteria)
-- ============================================================

INSERT INTO efmd_requirements (pillar, chapter, category, requirement_code, requirement_text, description, evidence_expected, is_eligibility_gate, is_critical, weight) VALUES

-- Gate 1: Business/Management Focus
('Core', 'Programme', 'Eligibility', 'ELG-1', 
 'Programme must be in business and/or management discipline',
 'The programme should clearly position itself within business, management, or a closely related professional field.',
 ARRAY['Programme title', 'Curriculum overview', 'Learning outcomes'],
 TRUE, TRUE, 3),

-- Gate 2: Degree-granting
('Core', 'Programme', 'Eligibility', 'ELG-2',
 'Programme must be a complete degree-granting programme',
 'Must award a recognized academic degree (Bachelor, Master, MBA, PhD) not just a certificate or diploma.',
 ARRAY['Degree certificate sample', 'Accreditation by national authority'],
 TRUE, TRUE, 3),

-- Gate 3: Operating History
('Core', 'Programme', 'Eligibility', 'ELG-3',
 'Programme must have been operating for at least 3 years with graduates',
 'Minimum of 3 complete cohorts must have graduated to demonstrate track record.',
 ARRAY['Graduation statistics', 'Cohort data for 3+ years'],
 TRUE, TRUE, 3),

-- Gate 4: ILO Documentation
('Core', 'Programme', 'Eligibility', 'ELG-4',
 'Programme must have clearly articulated Intended Learning Outcomes covering Knowledge, Skills, and Attitudes',
 'ILOs must be documented, measurable, and cover all three dimensions. EFMD recommends 5-6 programme-level ILOs.',
 ARRAY['Programme ILO document', 'ILO matrix', 'Assessment mapping'],
 TRUE, TRUE, 3),

-- Gate 5: Quality Assurance
('Core', 'Programme', 'Eligibility', 'ELG-5',
 'Programme must have systematic quality assurance processes',
 'Evidence of continuous improvement cycle including student feedback, external review, and action plans.',
 ARRAY['QA policy', 'Student evaluation summaries', 'Improvement action log'],
 TRUE, FALSE, 2),

-- Gate 6: Faculty Qualifications
('Core', 'Faculty', 'Eligibility', 'ELG-6',
 'Programme must have academically and professionally qualified faculty',
 'Mix of research-active academics and practitioners with relevant industry experience.',
 ARRAY['Faculty CVs', 'Publication records', 'Professional credentials'],
 TRUE, TRUE, 3),

-- Gate 7: Student Services
('Core', 'Students', 'Eligibility', 'ELG-7',
 'Programme must provide adequate student support services',
 'Career services, academic advising, and student development resources.',
 ARRAY['Student handbook', 'Career services description', 'Support staff list'],
 TRUE, FALSE, 2),

-- Gate 8: Physical Resources
('Core', 'Resources', 'Eligibility', 'ELG-8',
 'Programme must have adequate physical and technological resources',
 'Classrooms, library, IT infrastructure, and learning management systems.',
 ARRAY['Facilities overview', 'Technology inventory', 'Library resources'],
 TRUE, FALSE, 2),

-- Gate 9: Governance
('Core', 'Programme', 'Eligibility', 'ELG-9',
 'Programme must have clear governance and management structure',
 'Defined roles, responsibilities, and decision-making processes.',
 ARRAY['Organizational chart', 'Committee structure', 'Role descriptions'],
 TRUE, FALSE, 2),

-- Gate 10: Financial Sustainability
('Core', 'Resources', 'Eligibility', 'ELG-10',
 'Programme must demonstrate financial viability and sustainability',
 'Budget allocation, revenue streams, and long-term financial planning.',
 ARRAY['Budget summary', 'Revenue breakdown', 'Financial projections'],
 TRUE, FALSE, 2);

-- ============================================================
-- INTERNATIONAL PILLAR
-- ============================================================

INSERT INTO efmd_requirements (pillar, chapter, category, requirement_code, requirement_text, description, evidence_expected, is_critical, weight) VALUES

('International', 'Programme', 'Curriculum', 'INT-1',
 'Programme curriculum includes international and global business perspectives',
 'Content addresses cross-border business, global markets, and international management challenges.',
 ARRAY['Course syllabi with international content', 'Case studies from multiple regions'],
 TRUE, 2),

('International', 'Programme', 'Curriculum', 'INT-2',
 'Programme develops cross-cultural competencies and global mindset',
 'Students develop ability to work across cultures and understand diverse business environments.',
 ARRAY['ILOs mentioning international/global', 'Cross-cultural assignments'],
 FALSE, 2),

('International', 'Students', 'Experience', 'INT-3',
 'Students have opportunities for international exposure',
 'Exchange programmes, study trips, international projects, or diverse cohort composition.',
 ARRAY['Exchange agreements', 'International student %', 'Study abroad data'],
 FALSE, 2),

('International', 'Faculty', 'Profile', 'INT-4',
 'Faculty bring international experience and perspectives',
 'Faculty with international education, research collaborations, or professional experience abroad.',
 ARRAY['Faculty international backgrounds', 'International research collaborations'],
 FALSE, 1),

('International', 'Programme', 'Partnerships', 'INT-5',
 'Programme has international institutional partnerships',
 'Formal agreements with universities or organizations in other countries.',
 ARRAY['Partnership agreements', 'Joint programme descriptions', 'Visiting faculty'],
 FALSE, 1);

-- ============================================================
-- PRACTICE/CORPORATE CONNECTION PILLAR
-- ============================================================

INSERT INTO efmd_requirements (pillar, chapter, category, requirement_code, requirement_text, description, evidence_expected, is_critical, weight) VALUES

('Practice', 'Programme', 'Curriculum', 'PRA-1',
 'Programme integrates practical business application throughout curriculum',
 'Case studies, simulations, live projects, and real-world problem solving.',
 ARRAY['Case study list', 'Simulation descriptions', 'Project briefs'],
 TRUE, 2),

('Practice', 'Programme', 'Experience', 'PRA-2',
 'Programme includes internships, placements, or work-integrated learning',
 'Structured opportunities for students to gain professional experience.',
 ARRAY['Internship requirements', 'Placement statistics', 'Company partnerships'],
 FALSE, 2),

('Practice', 'Faculty', 'Profile', 'PRA-3',
 'Faculty maintain connections to business practice',
 'Consulting, board memberships, executive education, or recent industry experience.',
 ARRAY['Faculty consulting activities', 'Industry advisory roles'],
 FALSE, 2),

('Practice', 'Programme', 'Engagement', 'PRA-4',
 'Programme engages corporate partners in curriculum and delivery',
 'Guest speakers, company-sponsored projects, advisory boards with industry representation.',
 ARRAY['Guest speaker list', 'Advisory board composition', 'Sponsored projects'],
 FALSE, 1),

('Practice', 'Students', 'Outcomes', 'PRA-5',
 'Graduates achieve strong employment outcomes',
 'High employment rates, career progression, employer satisfaction.',
 ARRAY['Employment statistics', 'Salary data', 'Employer feedback'],
 FALSE, 2);

-- ============================================================
-- ERS PILLAR (Ethics, Responsibility, Sustainability)
-- ============================================================

INSERT INTO efmd_requirements (pillar, chapter, category, requirement_code, requirement_text, description, evidence_expected, is_critical, weight) VALUES

('ERS', 'Programme', 'Curriculum', 'ERS-1',
 'Programme integrates ethics, responsibility, and sustainability throughout curriculum',
 'Not just a standalone course but embedded across multiple courses and experiences.',
 ARRAY['ERS content mapping', 'Course syllabi showing ERS integration'],
 TRUE, 3),

('ERS', 'Programme', 'ILO', 'ERS-2',
 'Programme ILOs explicitly address ethical reasoning and responsible leadership',
 'Learning outcomes that develop ethical decision-making and sustainability mindset.',
 ARRAY['ILOs with ethics/responsibility language', 'Assessment of ethical reasoning'],
 TRUE, 2),

('ERS', 'Faculty', 'Research', 'ERS-3',
 'Faculty conduct research in ethics, CSR, sustainability, or governance',
 'Research output addressing responsible business topics.',
 ARRAY['Faculty publications on ERS topics', 'Research projects'],
 FALSE, 1),

('ERS', 'Programme', 'Experience', 'ERS-4',
 'Students engage in activities promoting social responsibility',
 'Community projects, social entrepreneurship, sustainability initiatives.',
 ARRAY['Student projects with social impact', 'CSR activities', 'Volunteering programs'],
 FALSE, 1),

('ERS', 'Programme', 'Curriculum', 'ERS-5',
 'Programme addresses UN Sustainable Development Goals or equivalent framework',
 'Explicit connection to global sustainability frameworks.',
 ARRAY['SDG mapping', 'Sustainability reporting', 'PRME engagement'],
 FALSE, 1);

-- ============================================================
-- DIGITAL PILLAR
-- ============================================================

INSERT INTO efmd_requirements (pillar, chapter, category, requirement_code, requirement_text, description, evidence_expected, is_critical, weight) VALUES

('Digital', 'Programme', 'Curriculum', 'DIG-1',
 'Programme develops digital and data literacy competencies',
 'Students learn to work with data, digital tools, and technology-enabled business.',
 ARRAY['Digital skills in ILOs', 'Data/analytics courses', 'Technology tools used'],
 TRUE, 2),

('Digital', 'Programme', 'Curriculum', 'DIG-2',
 'Programme addresses digital transformation of business',
 'Content on how technology is changing industries, business models, and work.',
 ARRAY['Digital transformation content', 'Technology case studies'],
 FALSE, 2),

('Digital', 'Programme', 'Delivery', 'DIG-3',
 'Programme uses technology effectively in teaching and learning',
 'Learning management systems, online resources, digital collaboration tools.',
 ARRAY['LMS usage', 'Digital learning tools', 'Online components'],
 FALSE, 1),

('Digital', 'Faculty', 'Capability', 'DIG-4',
 'Faculty are competent in digital teaching methods',
 'Faculty development in educational technology and digital pedagogy.',
 ARRAY['Faculty digital training', 'Innovation in teaching methods'],
 FALSE, 1),

('Digital', 'Programme', 'Curriculum', 'DIG-5',
 'Programme prepares students for AI and automation impact on business',
 'Content addressing artificial intelligence, machine learning, and future of work.',
 ARRAY['AI/ML content in curriculum', 'Future of work discussions'],
 FALSE, 2);

-- ============================================================
-- ASSURANCE OF LEARNING (Critical for ILO Analysis)
-- ============================================================

INSERT INTO efmd_requirements (pillar, chapter, category, requirement_code, requirement_text, description, evidence_expected, is_critical, weight) VALUES

('Core', 'Programme', 'Assessment', 'AOL-1',
 'Programme has systematic assurance of learning process',
 'Documented process for measuring whether ILOs are achieved.',
 ARRAY['AoL policy', 'Assessment rubrics', 'Results analysis'],
 TRUE, 3),

('Core', 'Programme', 'Assessment', 'AOL-2',
 'Each Programme ILO is mapped to specific assessments',
 'Clear matrix showing which assessments measure which ILOs.',
 ARRAY['ILO-assessment matrix', 'Assessment descriptions'],
 TRUE, 3),

('Core', 'Programme', 'Assessment', 'AOL-3',
 'Course ILOs align with and support Programme ILOs',
 'Cascade from programme-level to course-level outcomes.',
 ARRAY['Course-programme ILO mapping', 'Curriculum map'],
 TRUE, 2),

('Core', 'Programme', 'Assessment', 'AOL-4',
 'Programme collects and analyzes evidence of learning outcome achievement',
 'Direct and indirect measures of student learning.',
 ARRAY['Assessment results data', 'Student performance analysis', 'Graduate surveys'],
 TRUE, 2),

('Core', 'Programme', 'Assessment', 'AOL-5',
 'Programme uses AoL results to improve curriculum and teaching',
 'Closing the loop: evidence leads to action.',
 ARRAY['Improvement actions based on AoL', 'Curriculum changes', 'Faculty development'],
 TRUE, 2);

-- ============================================================
-- ILO QUALITY STANDARDS (For Analysis)
-- ============================================================

INSERT INTO efmd_requirements (pillar, chapter, category, requirement_code, requirement_text, description, evidence_expected, is_critical, weight) VALUES

('Core', 'Programme', 'ILO', 'ILO-1',
 'Programme has 5-6 well-articulated programme-level ILOs',
 'Optimal number for meaningful assessment. Too few lacks specificity, too many becomes unmanageable.',
 ARRAY['ILO document', 'Programme handbook'],
 TRUE, 2),

('Core', 'Programme', 'ILO', 'ILO-2',
 'ILOs use measurable action verbs aligned with Blooms taxonomy',
 'Verbs like analyze, evaluate, create, apply rather than understand, know, appreciate.',
 ARRAY['ILO text analysis', 'Verb usage'],
 TRUE, 2),

('Core', 'Programme', 'ILO', 'ILO-3',
 'ILOs cover Knowledge dimension - what students will know',
 'Theoretical foundations, conceptual understanding, factual knowledge.',
 ARRAY['Knowledge-focused ILOs'],
 TRUE, 2),

('Core', 'Programme', 'ILO', 'ILO-4',
 'ILOs cover Skills dimension - what students will be able to do',
 'Practical abilities, analytical skills, professional competencies.',
 ARRAY['Skill-focused ILOs'],
 TRUE, 2),

('Core', 'Programme', 'ILO', 'ILO-5',
 'ILOs cover Attitudes dimension - values and professional dispositions',
 'Ethical stance, professional attitudes, mindset development.',
 ARRAY['Attitude-focused ILOs'],
 TRUE, 2);

-- ============================================================
-- Count check
-- ============================================================
-- Should have ~40 requirements covering:
-- - 10 Eligibility gates
-- - 5 International
-- - 5 Practice
-- - 5 ERS
-- - 5 Digital
-- - 5 AoL
-- - 5 ILO Quality

SELECT pillar, COUNT(*) as count 
FROM efmd_requirements 
GROUP BY pillar 
ORDER BY pillar;
