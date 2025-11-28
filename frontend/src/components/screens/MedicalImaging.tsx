import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { medicalImagingApi } from "@/services/api";
import { Upload, Loader2, AlertCircle, CheckCircle, Image as ImageIcon, Download, Trash2, FileImage, Activity } from "lucide-react";

interface ImageMetadata {
  image_id: number;
  subject_id: string;
  filename: string;
  file_type: string;
  image_type?: string;
  visit_name?: string;
  file_size_bytes: number;
  modality?: string;
  has_thumbnail: boolean;
  uploaded_at: string;
  dicom_metadata?: any;
  thumbnail_metadata?: any;
}

export function MedicalImaging() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [subjectId, setSubjectId] = useState("");
  const [visitName, setVisitName] = useState("");
  const [imageType, setImageType] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Search and view state
  const [searchSubjectId, setSearchSubjectId] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [subjectImages, setSubjectImages] = useState<ImageMetadata[]>([]);
  const [selectedImage, setSelectedImage] = useState<ImageMetadata | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);

  // Imaging status
  const [imagingStatus, setImagingStatus] = useState<any>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const imageTypes = [
    { value: "X-ray", label: "X-ray" },
    { value: "CT", label: "CT Scan" },
    { value: "MRI", label: "MRI" },
    { value: "Ultrasound", label: "Ultrasound" },
    { value: "ECG", label: "ECG" },
    { value: "Photo", label: "Photo" },
    { value: "Other", label: "Other" },
  ];

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      setSelectedFile(files[0]);
      setError("");
      setSuccess("");
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError("Please select a file to upload");
      return;
    }

    if (!subjectId.trim()) {
      setError("Subject ID is required");
      return;
    }

    setIsUploading(true);
    setError("");
    setSuccess("");
    setUploadResult(null);

    try {
      const result = await medicalImagingApi.uploadImage(
        selectedFile,
        subjectId.trim(),
        visitName.trim() || undefined,
        imageType || undefined
      );

      setUploadResult(result);
      setSuccess(`Successfully uploaded ${selectedFile.name}`);

      // Reset form
      setSelectedFile(null);
      setSubjectId("");
      setVisitName("");
      setImageType("");
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (err: any) {
      setError(err?.message ?? "Upload failed. Please try again.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchSubjectId.trim()) {
      setError("Please enter a Subject ID to search");
      return;
    }

    setIsSearching(true);
    setError("");
    setSubjectImages([]);
    setSelectedImage(null);
    setImagePreview(null);

    try {
      const images = await medicalImagingApi.getSubjectImages(searchSubjectId.trim());
      setSubjectImages(images ?? []);

      if ((images ?? []).length === 0) {
        setError(`No images found for subject ${searchSubjectId}`);
      }
    } catch (err: any) {
      setError(err?.message ?? "Search failed. Please try again.");
    } finally {
      setIsSearching(false);
    }
  };

  const handleViewImage = async (image: ImageMetadata, thumbnail: boolean = false) => {
    try {
      setSelectedImage(image);
      const blob = await medicalImagingApi.getImageFile(image.image_id, thumbnail);
      const url = URL.createObjectURL(blob);
      setImagePreview(url);
    } catch (err: any) {
      setError(`Failed to load image: ${err?.message ?? 'Unknown error'}`);
    }
  };

  const handleDownload = async (image: ImageMetadata) => {
    try {
      const blob = await medicalImagingApi.getImageFile(image.image_id, false);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = image.filename ?? 'image';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(`Download failed: ${err?.message ?? 'Unknown error'}`);
    }
  };

  const handleDelete = async (imageId: number) => {
    if (!confirm("Are you sure you want to delete this image?")) {
      return;
    }

    try {
      await medicalImagingApi.deleteImage(imageId);
      setSuccess("Image deleted successfully");

      // Refresh the list
      if (searchSubjectId) {
        await handleSearch();
      }

      if (selectedImage?.image_id === imageId) {
        setSelectedImage(null);
        setImagePreview(null);
      }
    } catch (err: any) {
      setError(`Delete failed: ${err?.message ?? 'Unknown error'}`);
    }
  };

  const checkStatus = async () => {
    try {
      const status = await medicalImagingApi.getStatus();
      setImagingStatus(status);
    } catch (err: any) {
      setError(`Failed to check status: ${err?.message ?? 'Unknown error'}`);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Medical Imaging</h1>
          <p className="text-muted-foreground">Upload and manage DICOM, X-rays, CT scans, MRI, and other medical images</p>
        </div>
        <Button onClick={checkStatus} variant="outline" size="sm">
          <Activity className="h-4 w-4 mr-2" />
          Check Status
        </Button>
      </div>

      {/* Status Card */}
      {imagingStatus && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              Imaging Service Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium">DICOM Support:</span> {imagingStatus?.dicom_support ? "✅ Enabled" : "❌ Disabled"}
              </div>
              <div>
                <span className="font-medium">Imaging Available:</span> {imagingStatus?.imaging_available ? "✅ Yes" : "❌ No"}
              </div>
            </div>
            <div className="mt-3">
              <span className="font-medium">Supported Formats:</span>
              <div className="flex flex-wrap gap-2 mt-2">
                {Object.entries(imagingStatus?.supported_formats ?? {}).map(([type, formats]: [string, any]) => (
                  <Badge key={type} variant="secondary">
                    {type}: {(formats ?? []).join(', ')}
                  </Badge>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error/Success Messages */}
      {error && (
        <Card className="border-red-500 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-red-600">
              <AlertCircle className="h-5 w-5" />
              <span>{error}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {success && (
        <Card className="border-green-500 bg-green-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-green-600">
              <CheckCircle className="h-5 w-5" />
              <span>{success}</span>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-2 gap-6">
        {/* Upload Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="h-5 w-5" />
              Upload Medical Image
            </CardTitle>
            <CardDescription>Upload DICOM, PNG, JPEG, or PDF files</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="file">Select File</Label>
              <Input
                id="file"
                type="file"
                ref={fileInputRef}
                onChange={handleFileSelect}
                accept=".dcm,.dicom,.png,.jpg,.jpeg,.pdf"
              />
              {selectedFile && (
                <div className="mt-2 text-sm text-muted-foreground">
                  Selected: {selectedFile.name} ({formatFileSize(selectedFile.size)})
                </div>
              )}
            </div>

            <div>
              <Label htmlFor="subjectId">Subject ID *</Label>
              <Input
                id="subjectId"
                value={subjectId}
                onChange={(e) => setSubjectId(e.target.value)}
                placeholder="e.g., RA001-001"
              />
            </div>

            <div>
              <Label htmlFor="visitName">Visit Name (Optional)</Label>
              <Input
                id="visitName"
                value={visitName}
                onChange={(e) => setVisitName(e.target.value)}
                placeholder="e.g., Week 4, Screening"
              />
            </div>

            <div>
              <Label htmlFor="imageType">Image Type (Optional)</Label>
              <Select value={imageType} onValueChange={setImageType}>
                <SelectTrigger>
                  <SelectValue placeholder="Select image type" />
                </SelectTrigger>
                <SelectContent>
                  {imageTypes.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Button onClick={handleUpload} disabled={isUploading || !selectedFile} className="w-full">
              {isUploading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  Upload Image
                </>
              )}
            </Button>

            {uploadResult && (
              <div className="p-3 bg-muted rounded-lg text-sm space-y-1">
                <div><span className="font-medium">Image ID:</span> {uploadResult?.image_id ?? 'N/A'}</div>
                <div><span className="font-medium">File Type:</span> {uploadResult?.file_type ?? 'N/A'}</div>
                <div><span className="font-medium">Thumbnail:</span> {uploadResult?.has_thumbnail ? "✅ Generated" : "❌ Not generated"}</div>
                {uploadResult?.dicom_metadata && (
                  <div><span className="font-medium">DICOM:</span> ✅ Metadata extracted</div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Search Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileImage className="h-5 w-5" />
              Search Subject Images
            </CardTitle>
            <CardDescription>View all images for a subject</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <div className="flex-1">
                <Label htmlFor="searchSubjectId">Subject ID</Label>
                <Input
                  id="searchSubjectId"
                  value={searchSubjectId}
                  onChange={(e) => setSearchSubjectId(e.target.value)}
                  placeholder="e.g., RA001-001"
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                />
              </div>
              <div className="flex items-end">
                <Button onClick={handleSearch} disabled={isSearching}>
                  {isSearching ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    "Search"
                  )}
                </Button>
              </div>
            </div>

            {(subjectImages ?? []).length > 0 && (
              <div className="space-y-2">
                <div className="text-sm font-medium">
                  Found {(subjectImages ?? []).length} image(s)
                </div>
                <div className="max-h-96 overflow-y-auto space-y-2">
                  {(subjectImages ?? []).map((image) => (
                    <div
                      key={image.image_id}
                      className="p-3 border rounded-lg hover:bg-muted cursor-pointer"
                      onClick={() => handleViewImage(image, true)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="font-medium text-sm">{image.filename ?? 'Unknown'}</div>
                          <div className="text-xs text-muted-foreground space-y-1 mt-1">
                            <div>Type: {image.image_type ?? image.file_type ?? 'Unknown'}</div>
                            {image.visit_name && <div>Visit: {image.visit_name}</div>}
                            {image.modality && <div>Modality: {image.modality}</div>}
                            <div>Size: {formatFileSize(image.file_size_bytes ?? 0)}</div>
                            <div>Uploaded: {formatDate(image.uploaded_at ?? '')}</div>
                          </div>
                        </div>
                        <div className="flex gap-1">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDownload(image);
                            }}
                          >
                            <Download className="h-3 w-3" />
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDelete(image.image_id);
                            }}
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Image Preview */}
      {selectedImage && imagePreview && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ImageIcon className="h-5 w-5" />
              Image Preview: {selectedImage.filename ?? 'Unknown'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-6">
              <div>
                <img
                  src={imagePreview}
                  alt={selectedImage.filename ?? 'Medical Image'}
                  className="w-full rounded-lg border"
                />
              </div>
              <div className="space-y-3 text-sm">
                <div>
                  <span className="font-medium">File Type:</span> {selectedImage.file_type ?? 'N/A'}
                </div>
                <div>
                  <span className="font-medium">Image Type:</span> {selectedImage.image_type ?? 'N/A'}
                </div>
                <div>
                  <span className="font-medium">Subject ID:</span> {selectedImage.subject_id ?? 'N/A'}
                </div>
                {selectedImage.visit_name && (
                  <div>
                    <span className="font-medium">Visit:</span> {selectedImage.visit_name}
                  </div>
                )}
                {selectedImage.modality && (
                  <div>
                    <span className="font-medium">Modality:</span> {selectedImage.modality}
                  </div>
                )}
                <div>
                  <span className="font-medium">File Size:</span> {formatFileSize(selectedImage.file_size_bytes ?? 0)}
                </div>
                <div>
                  <span className="font-medium">Thumbnail:</span> {selectedImage.has_thumbnail ? "✅ Available" : "❌ Not available"}
                </div>
                <div>
                  <span className="font-medium">Uploaded:</span> {formatDate(selectedImage.uploaded_at ?? '')}
                </div>

                {selectedImage.dicom_metadata && (
                  <div className="mt-4">
                    <div className="font-medium mb-2">DICOM Metadata:</div>
                    <div className="p-3 bg-muted rounded-lg max-h-64 overflow-y-auto">
                      <pre className="text-xs whitespace-pre-wrap">
                        {JSON.stringify(selectedImage.dicom_metadata, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
