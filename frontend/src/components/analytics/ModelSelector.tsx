import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Info } from "lucide-react";

export type GenerationMethod = "mvn" | "bootstrap" | "rules" | "llm" | "bayesian" | "mice";

interface ModelSelectorProps {
  selectedMethod: GenerationMethod;
  onMethodChange: (method: GenerationMethod) => void;
  showDescription?: boolean;
}

const methodInfo: Record<GenerationMethod, { name: string; description: string; speed: string; quality: string }> = {
  mvn: {
    name: "MVN (Multivariate Normal)",
    description: "Statistical distribution-based generation. Preserves mean and covariance structure.",
    speed: "Very Fast (29K records/sec)",
    quality: "High - Best for normally distributed data"
  },
  bootstrap: {
    name: "Bootstrap",
    description: "Resampling from real data with Gaussian jitter. Preserves empirical distribution.",
    speed: "Ultra Fast (140K records/sec)",
    quality: "Excellent - Closest to real data"
  },
  rules: {
    name: "Rules-Based",
    description: "Deterministic generation using business rules and domain constraints.",
    speed: "Fast (80K records/sec)",
    quality: "Good - Predictable and consistent"
  },
  llm: {
    name: "LLM (GPT-4o-mini)",
    description: "AI-powered generation with context awareness and creative variability.",
    speed: "Slow (70 records/sec)",
    quality: "Creative - Context-aware patterns"
  },
  bayesian: {
    name: "Bayesian Network",
    description: "Probabilistic graphical model capturing conditional dependencies.",
    speed: "Moderate",
    quality: "High - Realistic correlations"
  },
  mice: {
    name: "MICE (Multiple Imputation)",
    description: "Multiple Imputation by Chained Equations with uncertainty quantification.",
    speed: "Moderate",
    quality: "High - Handles missing data well"
  }
};

export default function ModelSelector({ selectedMethod, onMethodChange, showDescription = true }: ModelSelectorProps) {
  const currentMethod = methodInfo[selectedMethod];

  return (
    <Card className="border-2 border-purple-200">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Info className="h-5 w-5 text-purple-600" />
          Generation Method Selection
        </CardTitle>
        <CardDescription>
          Choose which synthetic data generation method to compare against real pilot data
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="method-select">Select Generation Method</Label>
          <Select value={selectedMethod} onValueChange={(value) => onMethodChange(value as GenerationMethod)}>
            <SelectTrigger id="method-select" className="w-full">
              <SelectValue placeholder="Select a generation method" />
            </SelectTrigger>
            <SelectContent>
              {Object.entries(methodInfo).map(([key, info]) => (
                <SelectItem key={key} value={key}>
                  {info.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {showDescription && currentMethod && (
          <div className="bg-gradient-to-r from-purple-50 to-pink-50 p-4 rounded-lg space-y-3">
            <div className="flex items-center gap-2">
              <h4 className="font-semibold text-lg">{currentMethod.name}</h4>
              <Badge variant="outline" className="bg-white">
                {selectedMethod.toUpperCase()}
              </Badge>
            </div>

            <p className="text-sm text-gray-700">{currentMethod.description}</p>

            <div className="grid grid-cols-2 gap-4 mt-3">
              <div className="bg-white p-3 rounded-md border border-purple-200">
                <div className="text-xs text-gray-500 mb-1">Performance</div>
                <div className="text-sm font-medium text-purple-700">{currentMethod.speed}</div>
              </div>
              <div className="bg-white p-3 rounded-md border border-purple-200">
                <div className="text-xs text-gray-500 mb-1">Quality Profile</div>
                <div className="text-sm font-medium text-pink-700">{currentMethod.quality}</div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
