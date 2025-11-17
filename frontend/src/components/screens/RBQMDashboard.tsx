import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, TrendingUp, Users, FileText, Clock } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface SiteSummary {
  SiteID: string;
  queries_per_100: number;
  protocol_deviations: number;
  serious_related_aes: number;
  QTL_flag: boolean;
  QTL_flag_queries: boolean;
  QTL_flag_deviations: boolean;
  QTL_flag_safety: boolean;
}

interface KRIS {
  total_queries: number;
  query_rate_per_100: number;
  protocol_deviations: number;
  serious_related_aes: number;
  late_entry_pct: number;
  screen_fail_rate: number;
}

interface RBQMData {
  summary_markdown: string;
  site_summary: SiteSummary[];
  kris: KRIS;
}

export function RBQMDashboard() {
  const [rbqmData, setRBQMData] = useState<RBQMData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchRBQMData();
  }, []);

  const fetchRBQMData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch vitals data
      const vitalsRes = await fetch('http://localhost:8001/store-vitals');
      let vitals = [];
      if (vitalsRes.ok) {
        vitals = await vitalsRes.json();
      }

      // Fetch queries data
      const queriesRes = await fetch('http://localhost:8001/queries');
      let queries = [];
      if (queriesRes.ok) {
        queries = await queriesRes.json();
      }

      // Call RBQM service
      const rbqmRes = await fetch('http://localhost:8003/rbqm/summary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vitals_data: vitals,
          queries_data: queries,
          ae_data: [],
          thresholds: {
            q_rate_site: 6.0,
            missing_subj: 3,
            site_deviations: 5,
            site_serious_aes: 3,
            serious_related: 5
          },
          site_size: 20
        })
      });

      if (rbqmRes.ok) {
        const rbqmDataResult = await rbqmRes.json();
        setRBQMData(rbqmDataResult);
      } else {
        throw new Error('Failed to fetch RBQM data');
      }
    } catch (err) {
      console.error('Failed to fetch RBQM data:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const getRiskColorClass = (site: SiteSummary): string => {
    if (site.QTL_flag) return 'bg-red-100 border-red-300 dark:bg-red-900/20 dark:border-red-700';
    return 'bg-green-50 border-green-200 dark:bg-green-900/10 dark:border-green-800';
  };

  const getRiskBadgeVariant = (site: SiteSummary): "destructive" | "default" => {
    return site.QTL_flag ? "destructive" : "default";
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="h-12 w-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading RBQM Dashboard...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-destructive">
              <AlertCircle className="h-5 w-5" />
              Error Loading RBQM Data
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">{error}</p>
            <button
              onClick={fetchRBQMData}
              className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
            >
              Retry
            </button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!rbqmData) {
    return (
      <div className="container mx-auto p-6">
        <Card>
          <CardContent className="p-6">
            <p className="text-muted-foreground">No RBQM data available</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">RBQM Dashboard</h1>
          <p className="text-muted-foreground mt-1">Risk-Based Quality Management Overview</p>
        </div>
        <button
          onClick={fetchRBQMData}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
        >
          Refresh Data
        </button>
      </div>

      {/* KRI Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Queries</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{rbqmData.kris.total_queries}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {rbqmData.kris.query_rate_per_100.toFixed(1)} per 100 CRFs
            </p>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium text-muted-foreground">Protocol Deviations</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{rbqmData.kris.protocol_deviations}</div>
            <p className="text-xs text-muted-foreground mt-1">Subjects with deviations</p>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium text-muted-foreground">Serious + Related AEs</CardTitle>
              <AlertCircle className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{rbqmData.kris.serious_related_aes}</div>
            <p className="text-xs text-muted-foreground mt-1">Safety events</p>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium text-muted-foreground">Late Data Entry</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{rbqmData.kris.late_entry_pct.toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground mt-1">&gt;72hrs after visit</p>
          </CardContent>
        </Card>
      </div>

      {/* Site Risk Heatmap */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Site Risk Heatmap
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {rbqmData.site_summary.map((site) => (
              <div
                key={site.SiteID}
                className={`p-4 rounded-lg border-2 transition-all hover:shadow-md ${getRiskColorClass(site)}`}
              >
                <div className="font-bold text-lg mb-3">{site.SiteID}</div>

                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Query Rate:</span>
                    <div className="flex items-center gap-1">
                      <span className="font-medium">{site.queries_per_100.toFixed(1)}/100</span>
                      {site.QTL_flag_queries && (
                        <Badge variant="destructive" className="text-xs py-0">⚠</Badge>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Deviations:</span>
                    <div className="flex items-center gap-1">
                      <span className="font-medium">{site.protocol_deviations}</span>
                      {site.QTL_flag_deviations && (
                        <Badge variant="destructive" className="text-xs py-0">⚠</Badge>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Serious AEs:</span>
                    <div className="flex items-center gap-1">
                      <span className="font-medium">{site.serious_related_aes}</span>
                      {site.QTL_flag_safety && (
                        <Badge variant="destructive" className="text-xs py-0">⚠</Badge>
                      )}
                    </div>
                  </div>
                </div>

                {site.QTL_flag && (
                  <Badge variant={getRiskBadgeVariant(site)} className="mt-3 w-full justify-center">
                    HIGH RISK
                  </Badge>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Site Comparison Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Query Rate by Site</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={rbqmData.site_summary}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="SiteID" />
              <YAxis label={{ value: 'Queries per 100 CRFs', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="queries_per_100" fill="#8884d8" name="Query Rate" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Site Details Table */}
      <Card>
        <CardHeader>
          <CardTitle>Site Details</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2 font-medium">Site ID</th>
                  <th className="text-right p-2 font-medium">Query Rate</th>
                  <th className="text-right p-2 font-medium">Deviations</th>
                  <th className="text-right p-2 font-medium">Serious AEs</th>
                  <th className="text-center p-2 font-medium">Risk Level</th>
                </tr>
              </thead>
              <tbody>
                {rbqmData.site_summary.map((site) => (
                  <tr
                    key={site.SiteID}
                    className={`border-b hover:bg-muted/50 ${site.QTL_flag ? 'bg-destructive/10' : ''}`}
                  >
                    <td className="p-2 font-medium">{site.SiteID}</td>
                    <td className="p-2 text-right">{site.queries_per_100.toFixed(1)}</td>
                    <td className="p-2 text-right">{site.protocol_deviations}</td>
                    <td className="p-2 text-right">{site.serious_related_aes}</td>
                    <td className="p-2 text-center">
                      <Badge variant={site.QTL_flag ? "destructive" : "default"}>
                        {site.QTL_flag ? "HIGH RISK" : "LOW RISK"}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
