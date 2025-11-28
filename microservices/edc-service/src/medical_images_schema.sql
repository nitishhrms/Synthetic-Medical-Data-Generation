-- Medical Images Table for EDC Service
-- Stores metadata and references to uploaded medical images (DICOM, X-rays, scans, etc.)

CREATE TABLE IF NOT EXISTS medical_images (
    image_id SERIAL PRIMARY KEY,

    -- Foreign keys
    subject_id VARCHAR(50) NOT NULL,  -- References subjects(subject_id)
    visit_name VARCHAR(50),

    -- File information
    filename VARCHAR(255) NOT NULL,
    unique_filename VARCHAR(255) UNIQUE NOT NULL,
    file_type VARCHAR(20) NOT NULL,  -- 'dicom', 'image', 'document'
    file_hash VARCHAR(64) UNIQUE NOT NULL,  -- SHA256 hash for deduplication
    file_size_bytes INTEGER NOT NULL,

    -- Storage paths
    original_path TEXT NOT NULL,
    thumbnail_path TEXT,

    -- Image classification
    image_type VARCHAR(100),  -- 'X-ray', 'CT', 'MRI', 'Ultrasound', 'ECG', 'Photo', etc.
    modality VARCHAR(50),  -- DICOM modality code
    body_part VARCHAR(100),  -- Body part examined

    -- DICOM metadata (if applicable)
    dicom_metadata JSONB,  -- Full DICOM tags as JSON

    -- Thumbnail metadata
    thumbnail_metadata JSONB,

    -- Processing status
    processing_status VARCHAR(20) DEFAULT 'uploaded',  -- 'uploaded', 'processed', 'failed'
    processing_error TEXT,

    -- Audit fields
    uploaded_at TIMESTAMP DEFAULT NOW(),
    uploaded_by INTEGER,  -- References users(user_id)
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Indexes for common queries
    CONSTRAINT fk_image_subject FOREIGN KEY (subject_id) REFERENCES subjects(subject_id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_medical_images_subject_id ON medical_images(subject_id);
CREATE INDEX IF NOT EXISTS idx_medical_images_visit_name ON medical_images(visit_name);
CREATE INDEX IF NOT EXISTS idx_medical_images_image_type ON medical_images(image_type);
CREATE INDEX IF NOT EXISTS idx_medical_images_modality ON medical_images(modality);
CREATE INDEX IF NOT EXISTS idx_medical_images_file_hash ON medical_images(file_hash);
CREATE INDEX IF NOT EXISTS idx_medical_images_uploaded_at ON medical_images(uploaded_at DESC);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_medical_images_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER medical_images_update_timestamp
    BEFORE UPDATE ON medical_images
    FOR EACH ROW
    EXECUTE FUNCTION update_medical_images_timestamp();

-- Add comments for documentation
COMMENT ON TABLE medical_images IS 'Stores metadata and file references for medical images (DICOM, X-rays, scans, photos)';
COMMENT ON COLUMN medical_images.file_hash IS 'SHA256 hash for deduplication - prevents uploading same image twice';
COMMENT ON COLUMN medical_images.dicom_metadata IS 'DICOM tags extracted from .dcm files (Patient ID, Study Date, Modality, etc.)';
COMMENT ON COLUMN medical_images.modality IS 'DICOM modality: CR (X-ray), CT, MR (MRI), US (Ultrasound), ECG, etc.';
