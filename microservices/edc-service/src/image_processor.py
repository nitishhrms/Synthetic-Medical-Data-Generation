"""
Medical Image Processor - DICOM and Image Processing for EDC
Handles medical image uploads, DICOM metadata extraction, and batch processing
"""
import io
import os
import base64
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import hashlib

import numpy as np
from PIL import Image
import cv2

# DICOM support
try:
    import pydicom
    from pydicom.dataset import FileDataset
    DICOM_AVAILABLE = True
except ImportError:
    DICOM_AVAILABLE = False

# Daft for batch processing
try:
    import daft
    DAFT_AVAILABLE = True
except ImportError:
    DAFT_AVAILABLE = False


class MedicalImageProcessor:
    """
    Process medical images including DICOM, PNG, JPEG

    Features:
    - DICOM metadata extraction
    - Thumbnail generation
    - Image format conversion
    - Hash-based deduplication
    - Batch processing with Daft
    """

    SUPPORTED_FORMATS = {
        'dicom': ['.dcm', '.dicom', '.DCM', '.DICOM'],
        'image': ['.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG'],
        'document': ['.pdf', '.PDF']
    }

    def __init__(self, storage_base: str = "/data/medical-images"):
        """
        Initialize image processor

        Args:
            storage_base: Base directory for storing images
        """
        self.storage_base = Path(storage_base)
        self.storage_base.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (self.storage_base / "originals").mkdir(exist_ok=True)
        (self.storage_base / "thumbnails").mkdir(exist_ok=True)
        (self.storage_base / "temp").mkdir(exist_ok=True)

    def identify_file_type(self, filename: str, content: bytes = None) -> str:
        """
        Identify file type from filename or content

        Args:
            filename: File name
            content: File content bytes (optional)

        Returns:
            File type: 'dicom', 'image', 'document', or 'unknown'
        """
        ext = Path(filename).suffix.lower()

        # Check by extension
        for file_type, extensions in self.SUPPORTED_FORMATS.items():
            if ext in [e.lower() for e in extensions]:
                return file_type

        # Check by content if available
        if content:
            # DICOM magic bytes
            if content[:128].find(b'DICM') != -1:
                return 'dicom'

            # PNG magic bytes
            if content.startswith(b'\x89PNG\r\n\x1a\n'):
                return 'image'

            # JPEG magic bytes
            if content.startswith(b'\xff\xd8\xff'):
                return 'image'

            # PDF magic bytes
            if content.startswith(b'%PDF'):
                return 'document'

        return 'unknown'

    def calculate_file_hash(self, content: bytes) -> str:
        """Calculate SHA256 hash of file content for deduplication"""
        return hashlib.sha256(content).hexdigest()

    def extract_dicom_metadata(self, dicom_path: str) -> Dict[str, Any]:
        """
        Extract metadata from DICOM file

        Args:
            dicom_path: Path to DICOM file

        Returns:
            Dictionary with DICOM metadata
        """
        if not DICOM_AVAILABLE:
            raise RuntimeError("pydicom not installed. Install: pip install pydicom==2.4.4")

        try:
            ds = pydicom.dcmread(dicom_path)

            metadata = {
                # Patient information
                'patient_id': str(ds.get('PatientID', '')),
                'patient_name': str(ds.get('PatientName', '')),
                'patient_birth_date': str(ds.get('PatientBirthDate', '')),
                'patient_sex': str(ds.get('PatientSex', '')),
                'patient_age': str(ds.get('PatientAge', '')),

                # Study information
                'study_instance_uid': str(ds.get('StudyInstanceUID', '')),
                'study_date': str(ds.get('StudyDate', '')),
                'study_time': str(ds.get('StudyTime', '')),
                'study_description': str(ds.get('StudyDescription', '')),
                'study_id': str(ds.get('StudyID', '')),

                # Series information
                'series_instance_uid': str(ds.get('SeriesInstanceUID', '')),
                'series_number': str(ds.get('SeriesNumber', '')),
                'series_description': str(ds.get('SeriesDescription', '')),
                'modality': str(ds.get('Modality', '')),

                # Image information
                'sop_instance_uid': str(ds.get('SOPInstanceUID', '')),
                'sop_class_uid': str(ds.get('SOPClassUID', '')),
                'instance_number': str(ds.get('InstanceNumber', '')),

                # Technical parameters
                'rows': int(ds.get('Rows', 0)),
                'columns': int(ds.get('Columns', 0)),
                'bits_allocated': int(ds.get('BitsAllocated', 0)),
                'bits_stored': int(ds.get('BitsStored', 0)),
                'pixel_spacing': str(ds.get('PixelSpacing', '')),
                'slice_thickness': str(ds.get('SliceThickness', '')),

                # Equipment
                'manufacturer': str(ds.get('Manufacturer', '')),
                'manufacturer_model': str(ds.get('ManufacturerModelName', '')),
                'station_name': str(ds.get('StationName', '')),

                # Clinical
                'body_part_examined': str(ds.get('BodyPartExamined', '')),
                'protocol_name': str(ds.get('ProtocolName', '')),
                'acquisition_date': str(ds.get('AcquisitionDate', '')),
                'acquisition_time': str(ds.get('AcquisitionTime', '')),
            }

            # Add custom tags if present
            if hasattr(ds, 'PixelData'):
                metadata['has_pixel_data'] = True
                metadata['pixel_data_size_bytes'] = len(ds.PixelData)
            else:
                metadata['has_pixel_data'] = False

            return metadata

        except Exception as e:
            raise ValueError(f"Failed to extract DICOM metadata: {str(e)}")

    def dicom_to_image(self, dicom_path: str) -> np.ndarray:
        """
        Convert DICOM to numpy array (image)

        Args:
            dicom_path: Path to DICOM file

        Returns:
            Numpy array of image pixels
        """
        if not DICOM_AVAILABLE:
            raise RuntimeError("pydicom not installed")

        ds = pydicom.dcmread(dicom_path)

        if not hasattr(ds, 'PixelData'):
            raise ValueError("DICOM file has no pixel data")

        # Get pixel array
        pixel_array = ds.pixel_array

        # Normalize to 0-255 range
        pixel_array = pixel_array.astype(float)
        pixel_min = pixel_array.min()
        pixel_max = pixel_array.max()

        if pixel_max > pixel_min:
            pixel_array = ((pixel_array - pixel_min) / (pixel_max - pixel_min) * 255).astype(np.uint8)
        else:
            pixel_array = np.zeros_like(pixel_array, dtype=np.uint8)

        # Handle color vs grayscale
        if len(pixel_array.shape) == 2:
            # Grayscale - convert to RGB
            pixel_array = cv2.cvtColor(pixel_array, cv2.COLOR_GRAY2RGB)

        return pixel_array

    def create_thumbnail(
        self,
        image_path: str,
        thumbnail_size: Tuple[int, int] = (256, 256),
        quality: int = 85
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Create thumbnail from image

        Args:
            image_path: Path to image file
            thumbnail_size: Target thumbnail size (width, height)
            quality: JPEG quality (1-100)

        Returns:
            Tuple of (thumbnail_bytes, metadata)
        """
        file_type = self.identify_file_type(image_path)

        # Load image
        if file_type == 'dicom':
            pixel_array = self.dicom_to_image(image_path)
            img = Image.fromarray(pixel_array)
        elif file_type == 'image':
            img = Image.open(image_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        # Original dimensions
        original_size = img.size

        # Create thumbnail
        img.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)

        # Save to bytes
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=quality, optimize=True)
        thumbnail_bytes = buffer.getvalue()

        metadata = {
            'original_width': original_size[0],
            'original_height': original_size[1],
            'thumbnail_width': img.size[0],
            'thumbnail_height': img.size[1],
            'thumbnail_size_bytes': len(thumbnail_bytes),
            'format': 'JPEG',
            'quality': quality
        }

        return thumbnail_bytes, metadata

    def process_upload(
        self,
        filename: str,
        content: bytes,
        subject_id: str,
        visit_name: Optional[str] = None,
        image_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process uploaded medical image

        Args:
            filename: Original filename
            content: File content bytes
            subject_id: Subject identifier
            visit_name: Visit name (optional)
            image_type: Image type (X-ray, CT, MRI, etc.)

        Returns:
            Processing results with file paths and metadata
        """
        # Identify file type
        file_type = self.identify_file_type(filename, content)

        if file_type == 'unknown':
            raise ValueError(f"Unsupported file format: {filename}")

        # Calculate hash for deduplication
        file_hash = self.calculate_file_hash(content)

        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_filename = Path(filename).stem.replace(" ", "_")
        ext = Path(filename).suffix
        unique_filename = f"{subject_id}_{timestamp}_{safe_filename}_{file_hash[:8]}{ext}"

        # Save original file
        original_path = self.storage_base / "originals" / unique_filename
        original_path.write_bytes(content)

        result = {
            'filename': filename,
            'unique_filename': unique_filename,
            'file_type': file_type,
            'file_hash': file_hash,
            'file_size_bytes': len(content),
            'original_path': str(original_path),
            'subject_id': subject_id,
            'visit_name': visit_name,
            'image_type': image_type,
            'uploaded_at': datetime.utcnow().isoformat(),
        }

        # Extract DICOM metadata if applicable
        if file_type == 'dicom' and DICOM_AVAILABLE:
            try:
                dicom_metadata = self.extract_dicom_metadata(str(original_path))
                result['dicom_metadata'] = dicom_metadata
            except Exception as e:
                result['dicom_metadata_error'] = str(e)

        # Generate thumbnail for images and DICOM
        if file_type in ['image', 'dicom']:
            try:
                thumbnail_bytes, thumb_meta = self.create_thumbnail(str(original_path))

                # Save thumbnail
                thumbnail_filename = f"thumb_{unique_filename}.jpg"
                thumbnail_path = self.storage_base / "thumbnails" / thumbnail_filename
                thumbnail_path.write_bytes(thumbnail_bytes)

                result['thumbnail_path'] = str(thumbnail_path)
                result['thumbnail_metadata'] = thumb_meta
            except Exception as e:
                result['thumbnail_error'] = str(e)

        return result

    def get_image_bytes(self, file_path: str, as_thumbnail: bool = False) -> bytes:
        """
        Retrieve image bytes from storage

        Args:
            file_path: Path to image file
            as_thumbnail: If True, return thumbnail instead

        Returns:
            Image bytes
        """
        path = Path(file_path)

        if as_thumbnail:
            # Try to find thumbnail
            thumbnail_path = self.storage_base / "thumbnails" / f"thumb_{path.name}.jpg"
            if thumbnail_path.exists():
                return thumbnail_path.read_bytes()

        if not path.exists():
            raise FileNotFoundError(f"Image not found: {file_path}")

        return path.read_bytes()

    def batch_process_dicom(
        self,
        dicom_paths: List[str],
        use_daft: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Batch process multiple DICOM files

        Args:
            dicom_paths: List of DICOM file paths
            use_daft: Use Daft for distributed processing

        Returns:
            List of metadata dictionaries
        """
        if use_daft and DAFT_AVAILABLE:
            # Use Daft for parallel processing
            import pandas as pd

            # Create DataFrame with paths
            df = pd.DataFrame({'path': dicom_paths})
            daft_df = daft.from_pandas(df)

            # Note: Full Daft UDF implementation would go here
            # For now, fall back to sequential processing
            results = []
            for path in dicom_paths:
                try:
                    metadata = self.extract_dicom_metadata(path)
                    metadata['path'] = path
                    metadata['processing_status'] = 'success'
                    results.append(metadata)
                except Exception as e:
                    results.append({
                        'path': path,
                        'processing_status': 'failed',
                        'error': str(e)
                    })

            return results
        else:
            # Sequential processing
            results = []
            for path in dicom_paths:
                try:
                    metadata = self.extract_dicom_metadata(path)
                    metadata['path'] = path
                    metadata['processing_status'] = 'success'
                    results.append(metadata)
                except Exception as e:
                    results.append({
                        'path': path,
                        'processing_status': 'failed',
                        'error': str(e)
                    })

            return results

    def cleanup_temp_files(self, max_age_hours: int = 24):
        """
        Clean up temporary files older than max_age_hours

        Args:
            max_age_hours: Maximum age in hours
        """
        import time

        temp_dir = self.storage_base / "temp"
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600

        deleted_count = 0
        for file_path in temp_dir.glob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    file_path.unlink()
                    deleted_count += 1

        return {
            'deleted_files': deleted_count,
            'max_age_hours': max_age_hours
        }


# Convenience functions
def process_medical_image(
    filename: str,
    content: bytes,
    subject_id: str,
    visit_name: Optional[str] = None,
    image_type: Optional[str] = None,
    storage_base: str = "/data/medical-images"
) -> Dict[str, Any]:
    """
    Convenience function to process a medical image upload

    Example:
        >>> result = process_medical_image(
        ...     filename="xray_chest.dcm",
        ...     content=file_bytes,
        ...     subject_id="RA001-001",
        ...     visit_name="Week 4",
        ...     image_type="X-ray"
        ... )
    """
    processor = MedicalImageProcessor(storage_base=storage_base)
    return processor.process_upload(filename, content, subject_id, visit_name, image_type)
