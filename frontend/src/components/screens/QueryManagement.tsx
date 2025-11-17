import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { AlertCircle, MessageSquare, CheckCircle2, XCircle, Clock, Filter } from 'lucide-react';

interface Query {
  query_id: number;
  subject_id: string;
  query_text: string;
  severity: string;
  status: string;
  opened_at: string;
  response_text?: string;
}

type StatusFilter = 'all' | 'open' | 'answered' | 'closed';
type SeverityFilter = 'all' | 'info' | 'warning' | 'error' | 'critical';

export function QueryManagement() {
  const [queries, setQueries] = useState<Query[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedQuery, setSelectedQuery] = useState<Query | null>(null);
  const [showResponseModal, setShowResponseModal] = useState(false);
  const [responseText, setResponseText] = useState('');
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Filters
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>('all');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchQueries();
  }, [statusFilter, severityFilter]);

  const fetchQueries = async () => {
    try {
      setLoading(true);

      const params = new URLSearchParams();
      if (statusFilter !== 'all') params.append('status_filter', statusFilter);
      if (severityFilter !== 'all') params.append('severity', severityFilter);

      const url = `http://localhost:8001/queries${params.toString() ? `?${params.toString()}` : ''}`;
      const res = await fetch(url);

      if (res.ok) {
        const data = await res.json();
        setQueries(Array.isArray(data) ? data : []);
      } else {
        console.error('Failed to fetch queries');
        setQueries([]);
      }
    } catch (error) {
      console.error('Failed to fetch queries:', error);
      setQueries([]);
    } finally {
      setLoading(false);
    }
  };

  const handleRespond = (query: Query) => {
    setSelectedQuery(query);
    setResponseText('');
    setShowResponseModal(true);
  };

  const handleClose = (query: Query) => {
    setSelectedQuery(query);
    setResolutionNotes('');
    setShowResponseModal(true);
  };

  const submitResponse = async () => {
    if (!selectedQuery) return;

    try {
      setSubmitting(true);

      const endpoint = selectedQuery.status === 'open'
        ? `/queries/${selectedQuery.query_id}/respond`
        : `/queries/${selectedQuery.query_id}/close`;

      const body = selectedQuery.status === 'open'
        ? { response_text: responseText }
        : { resolution_notes: resolutionNotes };

      const res = await fetch(`http://localhost:8001${endpoint}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      if (res.ok) {
        setShowResponseModal(false);
        setResponseText('');
        setResolutionNotes('');
        fetchQueries(); // Refresh the list
      } else {
        alert('Failed to submit response');
      }
    } catch (error) {
      console.error('Failed to submit response:', error);
      alert('Failed to submit response');
    } finally {
      setSubmitting(false);
    }
  };

  const getSeverityBadgeVariant = (severity: string): "default" | "destructive" => {
    switch (severity) {
      case 'critical':
      case 'error':
        return 'destructive';
      default:
        return 'default';
    }
  };

  const getSeverityColor = (severity: string): string => {
    switch (severity) {
      case 'critical':
        return 'text-red-600 dark:text-red-400';
      case 'error':
        return 'text-orange-600 dark:text-orange-400';
      case 'warning':
        return 'text-yellow-600 dark:text-yellow-400';
      default:
        return 'text-blue-600 dark:text-blue-400';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'open':
        return <AlertCircle className="h-4 w-4" />;
      case 'answered':
        return <MessageSquare className="h-4 w-4" />;
      case 'closed':
        return <CheckCircle2 className="h-4 w-4" />;
      default:
        return <XCircle className="h-4 w-4" />;
    }
  };

  const getStatusBadgeVariant = (status: string): "default" | "destructive" => {
    return status === 'open' ? 'destructive' : 'default';
  };

  // Filter queries based on search term
  const filteredQueries = queries.filter(query => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      query.subject_id.toLowerCase().includes(term) ||
      query.query_text.toLowerCase().includes(term)
    );
  });

  const queryCounts = {
    open: queries.filter(q => q.status === 'open').length,
    answered: queries.filter(q => q.status === 'answered').length,
    closed: queries.filter(q => q.status === 'closed').length,
    total: queries.length
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="h-12 w-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading queries...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Query Management</h1>
          <p className="text-muted-foreground mt-1">Manage data queries and responses</p>
        </div>
        <button
          onClick={fetchQueries}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
        >
          Refresh
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="hover:shadow-lg transition-shadow">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Queries</p>
                <p className="text-2xl font-bold mt-1">{queryCounts.total}</p>
              </div>
              <MessageSquare className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Open</p>
                <p className="text-2xl font-bold mt-1 text-red-600">{queryCounts.open}</p>
              </div>
              <AlertCircle className="h-8 w-8 text-red-600" />
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Answered</p>
                <p className="text-2xl font-bold mt-1 text-yellow-600">{queryCounts.answered}</p>
              </div>
              <Clock className="h-8 w-8 text-yellow-600" />
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Closed</p>
                <p className="text-2xl font-bold mt-1 text-green-600">{queryCounts.closed}</p>
              </div>
              <CheckCircle2 className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Status</label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
                className="w-full px-3 py-2 border rounded-md bg-background"
              >
                <option value="all">All Statuses</option>
                <option value="open">Open</option>
                <option value="answered">Answered</option>
                <option value="closed">Closed</option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Severity</label>
              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value as SeverityFilter)}
                className="w-full px-3 py-2 border rounded-md bg-background"
              >
                <option value="all">All Severities</option>
                <option value="info">Info</option>
                <option value="warning">Warning</option>
                <option value="error">Error</option>
                <option value="critical">Critical</option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Search</label>
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search by subject or text..."
                className="w-full px-3 py-2 border rounded-md bg-background"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Queries Table */}
      <Card>
        <CardHeader>
          <CardTitle>Queries ({filteredQueries.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-3 font-medium">Query ID</th>
                  <th className="text-left p-3 font-medium">Subject ID</th>
                  <th className="text-left p-3 font-medium">Query Text</th>
                  <th className="text-center p-3 font-medium">Severity</th>
                  <th className="text-center p-3 font-medium">Status</th>
                  <th className="text-left p-3 font-medium">Opened</th>
                  <th className="text-center p-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredQueries.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="text-center p-8 text-muted-foreground">
                      No queries found
                    </td>
                  </tr>
                ) : (
                  filteredQueries.map((query) => (
                    <tr key={query.query_id} className="border-b hover:bg-muted/50">
                      <td className="p-3 font-mono text-sm">{query.query_id}</td>
                      <td className="p-3 font-medium">{query.subject_id}</td>
                      <td className="p-3 max-w-md truncate">{query.query_text}</td>
                      <td className="p-3 text-center">
                        <Badge variant={getSeverityBadgeVariant(query.severity)}>
                          <span className={getSeverityColor(query.severity)}>
                            {query.severity.toUpperCase()}
                          </span>
                        </Badge>
                      </td>
                      <td className="p-3 text-center">
                        <Badge variant={getStatusBadgeVariant(query.status)} className="flex items-center gap-1 w-fit mx-auto">
                          {getStatusIcon(query.status)}
                          {query.status.toUpperCase()}
                        </Badge>
                      </td>
                      <td className="p-3 text-sm text-muted-foreground">
                        {new Date(query.opened_at).toLocaleDateString()}
                      </td>
                      <td className="p-3 text-center">
                        {query.status === 'open' && (
                          <Button
                            size="sm"
                            onClick={() => handleRespond(query)}
                            className="mx-auto"
                          >
                            Respond
                          </Button>
                        )}
                        {query.status === 'answered' && (
                          <Button
                            size="sm"
                            onClick={() => handleClose(query)}
                            variant="outline"
                            className="mx-auto"
                          >
                            Close
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Response/Close Modal */}
      <Dialog open={showResponseModal} onOpenChange={setShowResponseModal}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>
              {selectedQuery?.status === 'open' ? 'Respond to Query' : 'Close Query'}
            </DialogTitle>
          </DialogHeader>

          {selectedQuery && (
            <div className="space-y-4">
              <div className="p-4 bg-muted rounded-md">
                <p className="text-sm font-medium mb-1">Query:</p>
                <p className="text-sm">{selectedQuery.query_text}</p>
                <div className="flex items-center gap-2 mt-2">
                  <Badge variant="outline" className="text-xs">
                    {selectedQuery.subject_id}
                  </Badge>
                  <Badge variant={getSeverityBadgeVariant(selectedQuery.severity)} className="text-xs">
                    {selectedQuery.severity}
                  </Badge>
                </div>
              </div>

              {selectedQuery.status === 'open' ? (
                <div>
                  <label className="text-sm font-medium mb-2 block">Response</label>
                  <textarea
                    value={responseText}
                    onChange={(e) => setResponseText(e.target.value)}
                    placeholder="Enter your response..."
                    rows={4}
                    className="w-full px-3 py-2 border rounded-md bg-background resize-none"
                  />
                </div>
              ) : (
                <div>
                  <label className="text-sm font-medium mb-2 block">Resolution Notes</label>
                  <textarea
                    value={resolutionNotes}
                    onChange={(e) => setResolutionNotes(e.target.value)}
                    placeholder="Enter resolution notes..."
                    rows={4}
                    className="w-full px-3 py-2 border rounded-md bg-background resize-none"
                  />
                </div>
              )}
            </div>
          )}

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowResponseModal(false)}
              disabled={submitting}
            >
              Cancel
            </Button>
            <Button
              onClick={submitResponse}
              disabled={submitting || (!responseText && !resolutionNotes)}
            >
              {submitting ? 'Submitting...' : 'Submit'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
