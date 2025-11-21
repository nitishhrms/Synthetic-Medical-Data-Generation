import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Brain, Loader2, AlertCircle, CheckCircle2, Info, AlertTriangle } from 'lucide-react';
import { aiMonitorApi, edcApi } from '@/services/api';

interface AIFinding {
    subject_id: string;
    issue_description: string;
    severity: string;
    suggested_action: string;
    field_name?: string;
}

interface ReviewResult {
    study_id: string;
    reviewed_at: string;
    findings: AIFinding[];
    subjects_reviewed: number;
}

export function AIMedicalMonitor() {
    const [studies, setStudies] = useState<any[]>([]);
    const [selectedStudyId, setSelectedStudyId] = useState<string>('');
    const [reviewing, setReviewing] = useState(false);
    const [reviewResult, setReviewResult] = useState<ReviewResult | null>(null);
    const [error, setError] = useState<string>('');
    const [loadingStudies, setLoadingStudies] = useState(false);

    const loadStudies = async () => {
        setLoadingStudies(true);
        try {
            const data = await edcApi.listStudies();
            setStudies(data.studies || []);
        } catch (err) {
            setError('Failed to load studies');
        } finally {
            setLoadingStudies(false);
        }
    };

    const runAIReview = async () => {
        if (!selectedStudyId) {
            setError('Please select a study');
            return;
        }

        setReviewing(true);
        setError('');
        setReviewResult(null);

        try {
            const result = await aiMonitorApi.reviewStudyAndPostQueries(selectedStudyId);
            setReviewResult(result.review);
        } catch (err: any) {
            setError(err.message || 'AI review failed');
        } finally {
            setReviewing(false);
        }
    };

    const getSeverityIcon = (severity: string) => {
        switch (severity) {
            case 'critical':
                return <AlertCircle className="h-4 w-4 text-red-600" />;
            case 'error':
                return <AlertTriangle className="h-4 w-4 text-orange-600" />;
            case 'warning':
                return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
            default:
                return <Info className="h-4 w-4 text-blue-600" />;
        }
    };

    const getSeverityBadgeVariant = (severity: string): "default" | "destructive" => {
        return severity === 'critical' || severity === 'error' ? 'destructive' : 'default';
    };

    return (
        <div className="container mx-auto p-6 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
                        <Brain className="h-8 w-8 text-primary" />
                        AI Medical Monitor
                    </h1>
                    <p className="text-muted-foreground mt-1">
                        Automated review of clinical trial data using AI
                    </p>
                </div>
            </div>

            {/* Info Card */}
            <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription>
                    The AI Medical Monitor reviews subject data and automatically raises queries for potential issues,
                    inconsistencies, or safety concerns. Queries are posted to the EDC and appear in Query Management.
                </AlertDescription>
            </Alert>

            {/* Control Panel */}
            <Card>
                <CardHeader>
                    <CardTitle>Run AI Review</CardTitle>
                    <CardDescription>
                        Select a study and let AI review all subjects
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    {error && (
                        <Alert variant="destructive">
                            <AlertCircle className="h-4 w-4" />
                            <AlertDescription>{error}</AlertDescription>
                        </Alert>
                    )}

                    <div className="flex items-center gap-4">
                        <div className="flex-1">
                            <label className="text-sm font-medium mb-2 block">Select Study</label>
                            <select
                                value={selectedStudyId}
                                onChange={(e) => setSelectedStudyId(e.target.value)}
                                className="w-full px-3 py-2 border rounded-md bg-background"
                                disabled={reviewing}
                            >
                                <option value="">-- Select a study --</option>
                                {studies.map((study) => (
                                    <option key={study.study_id} value={study.study_id}>
                                        {study.study_name} ({study.study_id})
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div className="flex gap-2 items-end">
                            <Button
                                onClick={loadStudies}
                                variant="outline"
                                disabled={loadingStudies || reviewing}
                            >
                                {loadingStudies ? (
                                    <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        Loading...
                                    </>
                                ) : (
                                    'Load Studies'
                                )}
                            </Button>

                            <Button
                                onClick={runAIReview}
                                disabled={!selectedStudyId || reviewing}
                            >
                                {reviewing ? (
                                    <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        AI Reviewing...
                                    </>
                                ) : (
                                    <>
                                        <Brain className="mr-2 h-4 w-4" />
                                        Run AI Review
                                    </>
                                )}
                            </Button>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Results */}
            {reviewResult && (
                <>
                    {/* Summary Card */}
                    <Card className="border-primary">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <CheckCircle2 className="h-5 w-5 text-green-600" />
                                Review Complete
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-3 gap-4">
                                <div className="p-4 bg-muted/50 rounded-lg">
                                    <p className="text-sm text-muted-foreground">Subjects Reviewed</p>
                                    <p className="text-2xl font-bold mt-1">{reviewResult.subjects_reviewed}</p>
                                </div>
                                <div className="p-4 bg-muted/50 rounded-lg">
                                    <p className="text-sm text-muted-foreground">Findings</p>
                                    <p className="text-2xl font-bold mt-1">{reviewResult.findings.length}</p>
                                </div>
                                <div className="p-4 bg-muted/50 rounded-lg">
                                    <p className="text-sm text-muted-foreground">Reviewed At</p>
                                    <p className="text-sm font-medium mt-1">
                                        {new Date(reviewResult.reviewed_at).toLocaleString()}
                                    </p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Findings Table */}
                    <Card>
                        <CardHeader>
                            <CardTitle>AI Findings ({reviewResult.findings.length})</CardTitle>
                            <CardDescription>
                                These findings have been posted as queries in the EDC system
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            {reviewResult.findings.length === 0 ? (
                                <div className="text-center py-8 text-muted-foreground">
                                    <CheckCircle2 className="h-12 w-12 mx-auto mb-2 text-green-600" />
                                    <p>No issues found! All subjects look good.</p>
                                </div>
                            ) : (
                                <div className="overflow-x-auto">
                                    <table className="w-full">
                                        <thead>
                                            <tr className="border-b">
                                                <th className="text-left p-3 font-medium">Subject ID</th>
                                                <th className="text-left p-3 font-medium">Issue</th>
                                                <th className="text-center p-3 font-medium">Severity</th>
                                                <th className="text-left p-3 font-medium">Suggested Action</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {reviewResult.findings.map((finding, idx) => (
                                                <tr key={idx} className="border-b hover:bg-muted/50">
                                                    <td className="p-3 font-mono text-sm">{finding.subject_id}</td>
                                                    <td className="p-3 max-w-md">
                                                        <div className="flex items-start gap-2">
                                                            {getSeverityIcon(finding.severity)}
                                                            <span className="text-sm">{finding.issue_description}</span>
                                                        </div>
                                                    </td>
                                                    <td className="p-3 text-center">
                                                        <Badge variant={getSeverityBadgeVariant(finding.severity)}>
                                                            {finding.severity.toUpperCase()}
                                                        </Badge>
                                                    </td>
                                                    <td className="p-3 text-sm text-muted-foreground">
                                                        {finding.suggested_action}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </>
            )}
        </div>
    );
}
