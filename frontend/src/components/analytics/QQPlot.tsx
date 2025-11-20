import { useMemo } from "react";
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Line } from "recharts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp } from "lucide-react";

interface QQPlotProps {
  realData: number[];
  syntheticData: number[];
  variable: string;
  unit?: string;
  syntheticMethodName?: string;
}

// Calculate theoretical quantiles for normal distribution
function calculateTheoreticalQuantiles(n: number): number[] {
  const quantiles: number[] = [];
  for (let i = 1; i <= n; i++) {
    // Using approximation for inverse normal CDF (probit function)
    const p = (i - 0.5) / n;
    const t = Math.sqrt(-2 * Math.log(Math.min(p, 1 - p)));
    const c0 = 2.515517;
    const c1 = 0.802853;
    const c2 = 0.010328;
    const d1 = 1.432788;
    const d2 = 0.189269;
    const d3 = 0.001308;

    let z = t - (c0 + c1 * t + c2 * t * t) / (1 + d1 * t + d2 * t * t + d3 * t * t * t);
    if (p > 0.5) z = -z;
    quantiles.push(z);
  }
  return quantiles;
}

export default function QQPlot({
  realData,
  syntheticData,
  variable,
  unit = "",
  syntheticMethodName = "Synthetic",
}: QQPlotProps) {
  const { realQQData, syntheticQQData, r2Real, r2Synthetic } = useMemo(() => {
    // Standardize data (z-score normalization)
    const standardize = (data: number[]) => {
      const mean = data.reduce((sum, v) => sum + v, 0) / data.length;
      const variance = data.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / data.length;
      const std = Math.sqrt(variance);
      return data.map((v) => (v - mean) / std);
    };

    const standardizedReal = standardize([...realData].sort((a, b) => a - b));
    const standardizedSynthetic = standardize([...syntheticData].sort((a, b) => a - b));

    const theoreticalReal = calculateTheoreticalQuantiles(standardizedReal.length);
    const theoreticalSynthetic = calculateTheoreticalQuantiles(standardizedSynthetic.length);

    // Calculate R² for normality assessment
    const calculateR2 = (observed: number[], theoretical: number[]) => {
      const n = observed.length;
      const meanObserved = observed.reduce((sum, v) => sum + v, 0) / n;

      const ssTotal = observed.reduce((sum, v) => sum + Math.pow(v - meanObserved, 2), 0);
      const ssResidual = observed.reduce((sum, v, i) => sum + Math.pow(v - theoretical[i], 2), 0);

      return 1 - ssResidual / ssTotal;
    };

    const realQQData = standardizedReal.map((v, i) => ({
      theoretical: theoreticalReal[i],
      observed: v,
      dataset: "Real",
    }));

    const syntheticQQData = standardizedSynthetic.map((v, i) => ({
      theoretical: theoreticalSynthetic[i],
      observed: v,
      dataset: syntheticMethodName,
    }));

    return {
      realQQData,
      syntheticQQData,
      r2Real: calculateR2(standardizedReal, theoreticalReal),
      r2Synthetic: calculateR2(standardizedSynthetic, theoreticalSynthetic),
    };
  }, [realData, syntheticData, syntheticMethodName]);

  // Combine both datasets for reference line
  const allData = [...realQQData, ...syntheticQQData];
  const minVal = Math.min(...allData.map((d) => Math.min(d.theoretical, d.observed)));
  const maxVal = Math.max(...allData.map((d) => Math.max(d.theoretical, d.observed)));
  const referenceLine = [
    { theoretical: minVal, observed: minVal },
    { theoretical: maxVal, observed: maxVal },
  ];

  // Assess normality based on R²
  const getNormalityAssessment = (r2: number) => {
    if (r2 >= 0.99) return { level: "Excellent", color: "green", description: "Very close to normal distribution" };
    if (r2 >= 0.95) return { level: "Good", color: "blue", description: "Approximately normal distribution" };
    if (r2 >= 0.90) return { level: "Fair", color: "yellow", description: "Moderately normal distribution" };
    return { level: "Poor", color: "red", description: "Deviates from normal distribution" };
  };

  const realAssessment = getNormalityAssessment(r2Real);
  const syntheticAssessment = getNormalityAssessment(r2Synthetic);

  return (
    <Card className="border-2 border-indigo-200">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-indigo-600" />
          Q-Q Plot: {variable} Normality Assessment
        </CardTitle>
        <CardDescription>
          Quantile-Quantile plot comparing data distributions to theoretical normal distribution
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Q-Q Plots Side by Side */}
        <div className="grid grid-cols-2 gap-4">
          {/* Real Data Q-Q Plot */}
          <div>
            <h4 className="font-semibold text-sm mb-2 text-green-800">Real Data Q-Q Plot</h4>
            <ResponsiveContainer width="100%" height={250}>
              <ScatterChart margin={{ top: 10, right: 10, bottom: 20, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="theoretical"
                  type="number"
                  name="Theoretical Quantiles"
                  label={{ value: "Theoretical Quantiles", position: "insideBottom", offset: -10 }}
                />
                <YAxis
                  dataKey="observed"
                  type="number"
                  name="Observed Quantiles"
                  label={{ value: "Observed", angle: -90, position: "insideLeft" }}
                />
                <Tooltip
                  cursor={{ strokeDasharray: "3 3" }}
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="bg-white p-2 border rounded shadow-lg text-xs">
                          <div>Theoretical: {data.theoretical.toFixed(2)}</div>
                          <div>Observed: {data.observed.toFixed(2)}</div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Scatter data={realQQData} fill="#10b981" />
                <Line data={referenceLine} dataKey="observed" stroke="#94a3b8" strokeWidth={2} dot={false} />
              </ScatterChart>
            </ResponsiveContainer>
            <div className="mt-2 text-center">
              <Badge variant="outline" className={`bg-${realAssessment.color}-50 text-${realAssessment.color}-700`}>
                R² = {r2Real.toFixed(4)} - {realAssessment.level}
              </Badge>
            </div>
          </div>

          {/* Synthetic Data Q-Q Plot */}
          <div>
            <h4 className="font-semibold text-sm mb-2 text-blue-800">{syntheticMethodName} Q-Q Plot</h4>
            <ResponsiveContainer width="100%" height={250}>
              <ScatterChart margin={{ top: 10, right: 10, bottom: 20, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="theoretical"
                  type="number"
                  name="Theoretical Quantiles"
                  label={{ value: "Theoretical Quantiles", position: "insideBottom", offset: -10 }}
                />
                <YAxis
                  dataKey="observed"
                  type="number"
                  name="Observed Quantiles"
                  label={{ value: "Observed", angle: -90, position: "insideLeft" }}
                />
                <Tooltip
                  cursor={{ strokeDasharray: "3 3" }}
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="bg-white p-2 border rounded shadow-lg text-xs">
                          <div>Theoretical: {data.theoretical.toFixed(2)}</div>
                          <div>Observed: {data.observed.toFixed(2)}</div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Scatter data={syntheticQQData} fill="#3b82f6" />
                <Line data={referenceLine} dataKey="observed" stroke="#94a3b8" strokeWidth={2} dot={false} />
              </ScatterChart>
            </ResponsiveContainer>
            <div className="mt-2 text-center">
              <Badge variant="outline" className={`bg-${syntheticAssessment.color}-50 text-${syntheticAssessment.color}-700`}>
                R² = {r2Synthetic.toFixed(4)} - {syntheticAssessment.level}
              </Badge>
            </div>
          </div>
        </div>

        {/* Interpretation Guide */}
        <div className="bg-gradient-to-r from-indigo-50 to-purple-50 p-4 rounded-lg border border-indigo-200">
          <h4 className="font-semibold text-indigo-800 mb-2">How to Interpret Q-Q Plots</h4>
          <div className="text-sm text-gray-700 space-y-2">
            <div className="flex items-start gap-2">
              <div className="w-2 h-2 rounded-full bg-indigo-500 mt-1.5"></div>
              <div>
                <strong>Points on diagonal line:</strong> Data follows normal distribution
              </div>
            </div>
            <div className="flex items-start gap-2">
              <div className="w-2 h-2 rounded-full bg-indigo-500 mt-1.5"></div>
              <div>
                <strong>S-shaped curve:</strong> Data has heavy tails (more extreme values than normal)
              </div>
            </div>
            <div className="flex items-start gap-2">
              <div className="w-2 h-2 rounded-full bg-indigo-500 mt-1.5"></div>
              <div>
                <strong>Inverted S-curve:</strong> Data has light tails (fewer extreme values than normal)
              </div>
            </div>
            <div className="flex items-start gap-2">
              <div className="w-2 h-2 rounded-full bg-indigo-500 mt-1.5"></div>
              <div>
                <strong>R² value:</strong> Closer to 1.0 indicates better fit to normal distribution
              </div>
            </div>
          </div>
        </div>

        {/* Normality Assessments */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-green-50 p-3 rounded-lg border border-green-200">
            <h5 className="font-semibold text-green-800 text-sm mb-2">Real Data Normality</h5>
            <div className="text-xs text-gray-700">{realAssessment.description}</div>
          </div>
          <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
            <h5 className="font-semibold text-blue-800 text-sm mb-2">{syntheticMethodName} Normality</h5>
            <div className="text-xs text-gray-700">{syntheticAssessment.description}</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
