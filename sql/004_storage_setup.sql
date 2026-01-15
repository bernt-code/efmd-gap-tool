-- ============================================================
-- SUPABASE STORAGE SETUP FOR CV FILES
-- Run this in Supabase SQL Editor
-- ============================================================

-- Create storage bucket for CVs (if not using UI)
-- Note: It's easier to create buckets via Supabase Dashboard > Storage > New Bucket

-- The bucket should be named 'cvs' with these settings:
-- - Public: Yes (so download URLs work)
-- - File size limit: 10MB
-- - Allowed MIME types: application/pdf, application/vnd.openxmlformats-officedocument.wordprocessingml.document

-- Storage policies (run after creating bucket via UI)

-- Allow authenticated uploads
CREATE POLICY "Allow uploads" ON storage.objects
FOR INSERT WITH CHECK (bucket_id = 'cvs');

-- Allow public downloads
CREATE POLICY "Allow public downloads" ON storage.objects
FOR SELECT USING (bucket_id = 'cvs');

-- ============================================================
-- ALTERNATIVE: Create bucket via SQL (Supabase specific)
-- ============================================================

-- INSERT INTO storage.buckets (id, name, public)
-- VALUES ('cvs', 'cvs', true);
