import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { User, Activity, TestTube, Save, CheckCircle2, AlertCircle } from 'lucide-react';

type DataEntryTab = 'enroll' | 'vitals' | 'demographics' | 'labs';

interface Subject {
  subject_id: string;
  study_id: string;
  site_id: string;
  treatment_arm: string;
  enrollment_date: string;
  status: string;
}

export function DataEntry() {
  const [activeTab, setActiveTab] = useState<DataEntryTab>('enroll');
  const [studies, setStudies] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Subject Enrollment Form
  const [enrollForm, setEnrollForm] = useState({
    study_id: '',
    site_id: '',
    treatment_arm: 'Active'
  });

  // Vitals Form
  const [vitalsForm, setVitalsForm] = useState({
    subject_id: '',
    visit_name: 'Screening',
    systolic_bp: '',
    diastolic_bp: '',
    heart_rate: '',
    temperature: '',
    observation_date: new Date().toISOString().split('T')[0]
  });

  // Demographics Form
  const [demoForm, setDemoForm] = useState({
    subject_id: '',
    age: '',
    gender: 'Male',
    race: 'White',
    ethnicity: 'Not Hispanic or Latino',
    height_cm: '',
    weight_kg: '',
    smoking_status: 'Never'
  });

  // Labs Form
  const [labsForm, setLabsForm] = useState({
    subject_id: '',
    visit_name: 'Screening',
    test_date: new Date().toISOString().split('T')[0],
    hemoglobin: '',
    hematocrit: '',
    wbc: '',
    platelets: '',
    glucose: '',
    creatinine: '',
    bun: '',
    alt: '',
    ast: '',
    bilirubin: '',
    total_cholesterol: '',
    ldl: '',
    hdl: '',
    triglycerides: ''
  });

  useEffect(() => {
    loadStudies();
    loadSubjects();
  }, []);

  const loadStudies = async () => {
    try {
      const res = await fetch('http://localhost:8001/studies');
      if (res.ok) {
        const data = await res.json();
        setStudies(data.studies || []);
      }
    } catch (error) {
      console.error('Failed to load studies:', error);
    }
  };

  const loadSubjects = async () => {
    // Note: This would need a backend endpoint to list all subjects
    // For now, we'll populate it when subjects are enrolled
  };

  const handleEnrollSubject = async () => {
    if (!enrollForm.study_id || !enrollForm.site_id) {
      setMessage({ type: 'error', text: 'Please fill in all required fields' });
      return;
    }

    try {
      setLoading(true);
      const res = await fetch('http://localhost:8001/subjects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(enrollForm)
      });

      if (res.ok) {
        const data = await res.json();
        setMessage({ type: 'success', text: `Subject ${data.subject_id} enrolled successfully!` });
        setSubjects([...subjects, { ...enrollForm, subject_id: data.subject_id, enrollment_date: new Date().toISOString(), status: 'enrolled' }]);
        setEnrollForm({ study_id: '', site_id: '', treatment_arm: 'Active' });
      } else {
        throw new Error('Failed to enroll subject');
      }
    } catch (error) {
      setMessage({ type: 'error', text: error instanceof Error ? error.message : 'Enrollment failed' });
    } finally {
      setLoading(false);
    }
  };

  const handleRecordVitals = async () => {
    if (!vitalsForm.subject_id || !vitalsForm.systolic_bp || !vitalsForm.diastolic_bp) {
      setMessage({ type: 'error', text: 'Please fill in required vital signs' });
      return;
    }

    try {
      setLoading(true);
      const res = await fetch('http://localhost:8001/vitals', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...vitalsForm,
          systolic_bp: parseInt(vitalsForm.systolic_bp),
          diastolic_bp: parseInt(vitalsForm.diastolic_bp),
          heart_rate: parseInt(vitalsForm.heart_rate),
          temperature: parseFloat(vitalsForm.temperature)
        })
      });

      if (res.ok) {
        setMessage({ type: 'success', text: 'Vitals recorded successfully!' });
        setVitalsForm({
          subject_id: '',
          visit_name: 'Screening',
          systolic_bp: '',
          diastolic_bp: '',
          heart_rate: '',
          temperature: '',
          observation_date: new Date().toISOString().split('T')[0]
        });
      } else {
        throw new Error('Failed to record vitals');
      }
    } catch (error) {
      setMessage({ type: 'error', text: error instanceof Error ? error.message : 'Recording failed' });
    } finally {
      setLoading(false);
    }
  };

  const handleRecordDemographics = async () => {
    if (!demoForm.subject_id || !demoForm.age || !demoForm.height_cm || !demoForm.weight_kg) {
      setMessage({ type: 'error', text: 'Please fill in required demographic fields' });
      return;
    }

    try {
      setLoading(true);
      const res = await fetch('http://localhost:8001/demographics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...demoForm,
          age: parseInt(demoForm.age),
          height_cm: parseFloat(demoForm.height_cm),
          weight_kg: parseFloat(demoForm.weight_kg)
        })
      });

      if (res.ok) {
        const data = await res.json();
        setMessage({ type: 'success', text: `Demographics recorded! BMI: ${data.bmi}` });
        setDemoForm({
          subject_id: '',
          age: '',
          gender: 'Male',
          race: 'White',
          ethnicity: 'Not Hispanic or Latino',
          height_cm: '',
          weight_kg: '',
          smoking_status: 'Never'
        });
      } else {
        throw new Error('Failed to record demographics');
      }
    } catch (error) {
      setMessage({ type: 'error', text: error instanceof Error ? error.message : 'Recording failed' });
    } finally {
      setLoading(false);
    }
  };

  const handleRecordLabs = async () => {
    if (!labsForm.subject_id) {
      setMessage({ type: 'error', text: 'Please select a subject' });
      return;
    }

    try {
      setLoading(true);
      const labData: any = { ...labsForm };

      // Convert numeric fields
      ['hemoglobin', 'hematocrit', 'wbc', 'platelets', 'glucose', 'creatinine',
       'bun', 'alt', 'ast', 'bilirubin', 'total_cholesterol', 'ldl', 'hdl', 'triglycerides'].forEach(field => {
        if (labData[field]) {
          labData[field] = parseFloat(labData[field]);
        } else {
          labData[field] = null;
        }
      });

      const res = await fetch('http://localhost:8001/labs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(labData)
      });

      if (res.ok) {
        setMessage({ type: 'success', text: 'Lab results recorded successfully!' });
        // Reset form
        setLabsForm({
          subject_id: '',
          visit_name: 'Screening',
          test_date: new Date().toISOString().split('T')[0],
          hemoglobin: '', hematocrit: '', wbc: '', platelets: '',
          glucose: '', creatinine: '', bun: '', alt: '', ast: '', bilirubin: '',
          total_cholesterol: '', ldl: '', hdl: '', triglycerides: ''
        });
      } else {
        throw new Error('Failed to record labs');
      }
    } catch (error) {
      setMessage({ type: 'error', text: error instanceof Error ? error.message : 'Recording failed' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Data Entry</h1>
          <p className="text-muted-foreground mt-1">Electronic Data Capture for Clinical Trials</p>
        </div>
      </div>

      {message && (
        <div className={`p-4 rounded-md ${message.type === 'success' ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400' : 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'}`}>
          <div className="flex items-center gap-2">
            {message.type === 'success' ? <CheckCircle2 className="h-5 w-5" /> : <AlertCircle className="h-5 w-5" />}
            {message.text}
          </div>
        </div>
      )}

      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as DataEntryTab)} className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="enroll" className="flex items-center gap-2">
            <User className="h-4 w-4" />
            Enroll Subject
          </TabsTrigger>
          <TabsTrigger value="vitals" className="flex items-center gap-2">
            <Activity className="h-4 w-4" />
            Vitals
          </TabsTrigger>
          <TabsTrigger value="demographics" className="flex items-center gap-2">
            <User className="h-4 w-4" />
            Demographics
          </TabsTrigger>
          <TabsTrigger value="labs" className="flex items-center gap-2">
            <TestTube className="h-4 w-4" />
            Lab Results
          </TabsTrigger>
        </TabsList>

        {/* Subject Enrollment Tab */}
        <TabsContent value="enroll">
          <Card>
            <CardHeader>
              <CardTitle>Enroll New Subject</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="study_id">Study *</Label>
                  <select
                    id="study_id"
                    value={enrollForm.study_id}
                    onChange={(e) => setEnrollForm({ ...enrollForm, study_id: e.target.value })}
                    className="w-full px-3 py-2 border rounded-md bg-background"
                  >
                    <option value="">Select Study</option>
                    {studies.map(s => (
                      <option key={s.study_id} value={s.study_id}>{s.study_name}</option>
                    ))}
                  </select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="site_id">Site ID *</Label>
                  <Input
                    id="site_id"
                    placeholder="e.g., Site001"
                    value={enrollForm.site_id}
                    onChange={(e) => setEnrollForm({ ...enrollForm, site_id: e.target.value })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="treatment_arm">Treatment Arm *</Label>
                  <select
                    id="treatment_arm"
                    value={enrollForm.treatment_arm}
                    onChange={(e) => setEnrollForm({ ...enrollForm, treatment_arm: e.target.value })}
                    className="w-full px-3 py-2 border rounded-md bg-background"
                  >
                    <option value="Active">Active</option>
                    <option value="Placebo">Placebo</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end">
                <Button onClick={handleEnrollSubject} disabled={loading}>
                  {loading ? 'Enrolling...' : 'Enroll Subject'}
                </Button>
              </div>

              {subjects.length > 0 && (
                <div className="mt-6 pt-6 border-t">
                  <h3 className="font-medium mb-4">Recently Enrolled Subjects</h3>
                  <div className="space-y-2">
                    {subjects.slice(-5).reverse().map(s => (
                      <div key={s.subject_id} className="flex items-center justify-between p-3 bg-muted rounded-md">
                        <div className="flex items-center gap-3">
                          <Badge>{s.subject_id}</Badge>
                          <span className="text-sm">{s.site_id}</span>
                          <span className="text-sm text-muted-foreground">{s.treatment_arm}</span>
                        </div>
                        <Badge variant="outline">{s.status}</Badge>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Vitals Tab */}
        <TabsContent value="vitals">
          <Card>
            <CardHeader>
              <CardTitle>Record Vital Signs</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="vitals_subject">Subject ID *</Label>
                  <Input
                    id="vitals_subject"
                    placeholder="e.g., RA001-001"
                    value={vitalsForm.subject_id}
                    onChange={(e) => setVitalsForm({ ...vitalsForm, subject_id: e.target.value })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="visit_name">Visit</Label>
                  <select
                    id="visit_name"
                    value={vitalsForm.visit_name}
                    onChange={(e) => setVitalsForm({ ...vitalsForm, visit_name: e.target.value })}
                    className="w-full px-3 py-2 border rounded-md bg-background"
                  >
                    <option value="Screening">Screening</option>
                    <option value="Day 1">Day 1</option>
                    <option value="Week 4">Week 4</option>
                    <option value="Week 12">Week 12</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="systolic_bp">Systolic BP (mmHg) *</Label>
                  <Input
                    id="systolic_bp"
                    type="number"
                    placeholder="95-200"
                    value={vitalsForm.systolic_bp}
                    onChange={(e) => setVitalsForm({ ...vitalsForm, systolic_bp: e.target.value })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="diastolic_bp">Diastolic BP (mmHg) *</Label>
                  <Input
                    id="diastolic_bp"
                    type="number"
                    placeholder="55-130"
                    value={vitalsForm.diastolic_bp}
                    onChange={(e) => setVitalsForm({ ...vitalsForm, diastolic_bp: e.target.value })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="heart_rate">Heart Rate (bpm)</Label>
                  <Input
                    id="heart_rate"
                    type="number"
                    placeholder="50-120"
                    value={vitalsForm.heart_rate}
                    onChange={(e) => setVitalsForm({ ...vitalsForm, heart_rate: e.target.value })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="temperature">Temperature (°C)</Label>
                  <Input
                    id="temperature"
                    type="number"
                    step="0.1"
                    placeholder="35.0-40.0"
                    value={vitalsForm.temperature}
                    onChange={(e) => setVitalsForm({ ...vitalsForm, temperature: e.target.value })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="observation_date">Observation Date</Label>
                  <Input
                    id="observation_date"
                    type="date"
                    value={vitalsForm.observation_date}
                    onChange={(e) => setVitalsForm({ ...vitalsForm, observation_date: e.target.value })}
                  />
                </div>
              </div>

              <div className="flex justify-end">
                <Button onClick={handleRecordVitals} disabled={loading}>
                  <Save className="mr-2 h-4 w-4" />
                  {loading ? 'Saving...' : 'Record Vitals'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Demographics Tab */}
        <TabsContent value="demographics">
          <Card>
            <CardHeader>
              <CardTitle>Record Demographics</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="demo_subject">Subject ID *</Label>
                  <Input
                    id="demo_subject"
                    placeholder="e.g., RA001-001"
                    value={demoForm.subject_id}
                    onChange={(e) => setDemoForm({ ...demoForm, subject_id: e.target.value })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="age">Age (years) *</Label>
                  <Input
                    id="age"
                    type="number"
                    placeholder="18-85"
                    value={demoForm.age}
                    onChange={(e) => setDemoForm({ ...demoForm, age: e.target.value })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="gender">Gender</Label>
                  <select
                    id="gender"
                    value={demoForm.gender}
                    onChange={(e) => setDemoForm({ ...demoForm, gender: e.target.value })}
                    className="w-full px-3 py-2 border rounded-md bg-background"
                  >
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="race">Race</Label>
                  <select
                    id="race"
                    value={demoForm.race}
                    onChange={(e) => setDemoForm({ ...demoForm, race: e.target.value })}
                    className="w-full px-3 py-2 border rounded-md bg-background"
                  >
                    <option value="White">White</option>
                    <option value="Black">Black</option>
                    <option value="Asian">Asian</option>
                    <option value="Other">Other</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="ethnicity">Ethnicity</Label>
                  <select
                    id="ethnicity"
                    value={demoForm.ethnicity}
                    onChange={(e) => setDemoForm({ ...demoForm, ethnicity: e.target.value })}
                    className="w-full px-3 py-2 border rounded-md bg-background"
                  >
                    <option value="Not Hispanic or Latino">Not Hispanic or Latino</option>
                    <option value="Hispanic or Latino">Hispanic or Latino</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="smoking_status">Smoking Status</Label>
                  <select
                    id="smoking_status"
                    value={demoForm.smoking_status}
                    onChange={(e) => setDemoForm({ ...demoForm, smoking_status: e.target.value })}
                    className="w-full px-3 py-2 border rounded-md bg-background"
                  >
                    <option value="Never">Never</option>
                    <option value="Former">Former</option>
                    <option value="Current">Current</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="height_cm">Height (cm) *</Label>
                  <Input
                    id="height_cm"
                    type="number"
                    step="0.1"
                    placeholder="140-220"
                    value={demoForm.height_cm}
                    onChange={(e) => setDemoForm({ ...demoForm, height_cm: e.target.value })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="weight_kg">Weight (kg) *</Label>
                  <Input
                    id="weight_kg"
                    type="number"
                    step="0.1"
                    placeholder="40-200"
                    value={demoForm.weight_kg}
                    onChange={(e) => setDemoForm({ ...demoForm, weight_kg: e.target.value })}
                  />
                </div>
              </div>

              <div className="flex justify-end">
                <Button onClick={handleRecordDemographics} disabled={loading}>
                  <Save className="mr-2 h-4 w-4" />
                  {loading ? 'Saving...' : 'Record Demographics'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Labs Tab */}
        <TabsContent value="labs">
          <Card>
            <CardHeader>
              <CardTitle>Record Lab Results</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="labs_subject">Subject ID *</Label>
                  <Input
                    id="labs_subject"
                    placeholder="e.g., RA001-001"
                    value={labsForm.subject_id}
                    onChange={(e) => setLabsForm({ ...labsForm, subject_id: e.target.value })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="labs_visit">Visit</Label>
                  <select
                    id="labs_visit"
                    value={labsForm.visit_name}
                    onChange={(e) => setLabsForm({ ...labsForm, visit_name: e.target.value })}
                    className="w-full px-3 py-2 border rounded-md bg-background"
                  >
                    <option value="Screening">Screening</option>
                    <option value="Week 4">Week 4</option>
                    <option value="Week 12">Week 12</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="test_date">Test Date</Label>
                  <Input
                    id="test_date"
                    type="date"
                    value={labsForm.test_date}
                    onChange={(e) => setLabsForm({ ...labsForm, test_date: e.target.value })}
                  />
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="font-medium">Hematology</h3>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="hemoglobin">Hemoglobin (g/dL)</Label>
                    <Input
                      id="hemoglobin"
                      type="number"
                      step="0.1"
                      placeholder="12-18"
                      value={labsForm.hemoglobin}
                      onChange={(e) => setLabsForm({ ...labsForm, hemoglobin: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="hematocrit">Hematocrit (%)</Label>
                    <Input
                      id="hematocrit"
                      type="number"
                      step="0.1"
                      placeholder="36-50"
                      value={labsForm.hematocrit}
                      onChange={(e) => setLabsForm({ ...labsForm, hematocrit: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="wbc">WBC (K/μL)</Label>
                    <Input
                      id="wbc"
                      type="number"
                      step="0.01"
                      placeholder="4-11"
                      value={labsForm.wbc}
                      onChange={(e) => setLabsForm({ ...labsForm, wbc: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="platelets">Platelets (K/μL)</Label>
                    <Input
                      id="platelets"
                      type="number"
                      step="0.1"
                      placeholder="150-400"
                      value={labsForm.platelets}
                      onChange={(e) => setLabsForm({ ...labsForm, platelets: e.target.value })}
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="font-medium">Chemistry</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="glucose">Glucose (mg/dL)</Label>
                    <Input
                      id="glucose"
                      type="number"
                      step="0.1"
                      placeholder="70-100"
                      value={labsForm.glucose}
                      onChange={(e) => setLabsForm({ ...labsForm, glucose: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="creatinine">Creatinine (mg/dL)</Label>
                    <Input
                      id="creatinine"
                      type="number"
                      step="0.01"
                      placeholder="0.7-1.3"
                      value={labsForm.creatinine}
                      onChange={(e) => setLabsForm({ ...labsForm, creatinine: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="bun">BUN (mg/dL)</Label>
                    <Input
                      id="bun"
                      type="number"
                      step="0.1"
                      placeholder="7-20"
                      value={labsForm.bun}
                      onChange={(e) => setLabsForm({ ...labsForm, bun: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="alt">ALT (U/L)</Label>
                    <Input
                      id="alt"
                      type="number"
                      step="0.1"
                      placeholder="7-56"
                      value={labsForm.alt}
                      onChange={(e) => setLabsForm({ ...labsForm, alt: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="ast">AST (U/L)</Label>
                    <Input
                      id="ast"
                      type="number"
                      step="0.1"
                      placeholder="10-40"
                      value={labsForm.ast}
                      onChange={(e) => setLabsForm({ ...labsForm, ast: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="bilirubin">Bilirubin (mg/dL)</Label>
                    <Input
                      id="bilirubin"
                      type="number"
                      step="0.01"
                      placeholder="0.3-1.2"
                      value={labsForm.bilirubin}
                      onChange={(e) => setLabsForm({ ...labsForm, bilirubin: e.target.value })}
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="font-medium">Lipids</h3>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="total_cholesterol">Total Cholesterol</Label>
                    <Input
                      id="total_cholesterol"
                      type="number"
                      step="0.1"
                      placeholder="mg/dL"
                      value={labsForm.total_cholesterol}
                      onChange={(e) => setLabsForm({ ...labsForm, total_cholesterol: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="ldl">LDL</Label>
                    <Input
                      id="ldl"
                      type="number"
                      step="0.1"
                      placeholder="mg/dL"
                      value={labsForm.ldl}
                      onChange={(e) => setLabsForm({ ...labsForm, ldl: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="hdl">HDL</Label>
                    <Input
                      id="hdl"
                      type="number"
                      step="0.1"
                      placeholder="mg/dL"
                      value={labsForm.hdl}
                      onChange={(e) => setLabsForm({ ...labsForm, hdl: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="triglycerides">Triglycerides</Label>
                    <Input
                      id="triglycerides"
                      type="number"
                      step="0.1"
                      placeholder="mg/dL"
                      value={labsForm.triglycerides}
                      onChange={(e) => setLabsForm({ ...labsForm, triglycerides: e.target.value })}
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end">
                <Button onClick={handleRecordLabs} disabled={loading}>
                  <Save className="mr-2 h-4 w-4" />
                  {loading ? 'Saving...' : 'Record Lab Results'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
