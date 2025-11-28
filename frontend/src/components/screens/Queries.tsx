import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { RefreshCw, AlertCircle, CheckCircle2, Clock, XCircle, FileText } from "lucide-react";

interface Query {
    query_id: number;
    subject_id: string;
    query_text: string;
    field_name: string;
    severity: string;
    status: string;
    created_at?: string;
    responded_at?: string;
    check_id?: number;
}

interface QueriesProps {
    onNavigateToDataEntry?: (subjectId: string, queryId?: number) => void;
}

export function Queries({ onNavigateToDataEntry }: QueriesProps) {
    const [queries, setQueries] = useState<Query[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchQueries = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch('http://localhost:8001/queries');
            if (res.ok) {
                const data = await res.json();
                setQueries(data.queries || data || []);
            } else {
                setError('Failed to fetch queries');
            }
        } catch (err) {
            console.error('Failed to fetch queries:', err);
            setError('Network error. Please check if services are running.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchQueries();
    }, []);

    const getSeverityVariant = (severity: string) => {
        if (!severity) return 'secondary';
        const s = severity.toUpperCase();
        switch (s) {
            case 'CRITICAL': return 'destructive';
            case 'WARNING': return 'default';
            default: return 'secondary';
        }
    };

    const getStatusIcon = (status: string) => {
        if (!status) return <AlertCircle className="h-4 w-4 text-orange-600" />;
        const s = status.toLowerCase();
        switch (s) {
            case 'closed': return <CheckCircle2 className="h-4 w-4 text-green-600" />;
            case 'responded': return <Clock className="h-4 w-4 text-blue-600" />;
            default: return <AlertCircle className="h-4 w-4 text-orange-600" />;
        }
    };

    const criticalCount = queries.filter(q => q.severity && q.severity.toUpperCase() === 'CRITICAL').length;
    const warningCount = queries.filter(q => q.severity && q.severity.toUpperCase() === 'WARNING').length;
    const openCount = queries.filter(q => q.status && q.status.toLowerCase() === 'open').length;

    return (
        <div className="container mx-auto p-6 space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Data Queries</h1>
                    <p className="text-muted-foreground mt-1">View and manage data quality queries</p>
                </div>
                <Button onClick={fetchQueries} disabled={loading}>
                    <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                    Refresh
                </Button>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card>
                    <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Total Queries</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{queries.length}</div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Open</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-orange-600">{openCount}</div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Critical</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-red-600">{criticalCount}</div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Warnings</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-yellow-600">{warningCount}</div>
                    </CardContent>
                </Card>
            </div>

            {/* Queries List */}
            <Card>
                <CardHeader>
                    <CardTitle>All Queries ({queries.length})</CardTitle>
                </CardHeader>
                <CardContent>
                    {error && (
                        <div className="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded mb-4">
                            {error}
                        </div>
                    )}

                    {loading && queries.length === 0 ? (
                        <div className="text-center py-8">
                            <RefreshCw className="h-8 w-8 animate-spin mx-auto text-muted-foreground mb-2" />
                            <p className="text-muted-foreground">Loading queries...</p>
                        </div>
                    ) : queries.length === 0 ? (
                        <div className="text-center py-8">
                            <AlertCircle className="h-12 w-12 mx-auto text-muted-foreground mb-3" />
                            <p className="text-muted-foreground">No queries found</p>
                            <p className="text-sm text-muted-foreground mt-1">
                                Queries will appear here when AI Monitor or edit checks detect issues
                            </p>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {queries.map((q) => (
                                <div
                                    key={q.query_id}
                                    className="border rounded-lg p-4 hover:bg-muted/50 transition-colors"
                                >
                                    <div className="flex justify-between items-start mb-2">
                                        <div className="flex items-center gap-2">
                                            <Badge variant={getSeverityVariant(q.severity)}>
                                                {q.severity}
                                            </Badge>
                                            <span className="font-medium">{q.subject_id}</span>
                                            {q.check_id && (
                                                <span className="text-xs text-muted-foreground">
                                                    Check: {q.check_id}
                                                </span>
                                            )}
                                        </div>
                                        <div className="flex items-center gap-2">
                                            {getStatusIcon(q.status)}
                                            <Badge variant="outline">{q.status}</Badge>
                                        </div>
                                    </div>
                                    <p className="text-sm mb-2">{q.query_text}</p>
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                                            <span>Field: <span className="font-mono">{q.field_name}</span></span>
                                            {q.created_at && (
                                                <span>Created: {new Date(q.created_at).toLocaleString()}</span>
                                            )}
                                        </div>
                                        <Button
                                            size="sm"
                                            variant="outline"
                                            onClick={() => onNavigateToDataEntry?.(q.subject_id, q.query_id)}
                                        >
                                            View Subject Data
                                        </Button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
