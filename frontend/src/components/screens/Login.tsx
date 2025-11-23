import { useState } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/useAuth";
import { AlertCircle, Brain, ArrowLeft, Lock, Mail, User } from "lucide-react";

interface LoginProps {
  onShowSystemCheck?: () => void;
}

export function Login({ onShowSystemCheck }: LoginProps) {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const { login, register } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      if (isLogin) {
        await login({ username, password });
      } else {
        await register({
          username,
          password,
          email,
          role: "researcher",
          tenant_id: "default",
        });
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "An error occurred";
      setError(errorMessage);
      if (errorMessage.includes("fetch") || errorMessage.includes("Failed to fetch")) {
        setError("Cannot connect to backend service. Please check if the security service (port 8005) is running.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex bg-zinc-950 text-white overflow-hidden">
      {/* Left Side - Form */}
      <div className="w-full lg:w-1/2 flex flex-col justify-center px-8 sm:px-12 lg:px-24 relative z-10">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-md mx-auto"
        >
          <div className="mb-8">
            <div className="flex items-center gap-2 mb-6">
              <div className="relative h-8 w-8">
                <div className="absolute inset-0 bg-teal-500 blur-lg opacity-50 animate-pulse" />
                <Brain className="relative h-8 w-8 text-teal-400" />
              </div>
              <span className="text-xl font-bold tracking-tight">SynData AI</span>
            </div>

            <h1 className="text-3xl font-bold mb-2">
              {isLogin ? "Welcome back" : "Create an account"}
            </h1>
            <p className="text-zinc-400">
              {isLogin
                ? "Enter your credentials to access your workspace"
                : "Join thousands of researchers generating synthetic data"}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <div className="relative">
                <User className="absolute left-3 top-3 h-4 w-4 text-zinc-500" />
                <Input
                  id="username"
                  type="text"
                  placeholder="Enter your username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  className="pl-10 bg-zinc-900/50 border-zinc-800 focus:border-teal-500/50 focus:ring-teal-500/20 h-11"
                />
              </div>
            </div>

            {!isLogin && (
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-4 w-4 text-zinc-500" />
                  <Input
                    id="email"
                    type="email"
                    placeholder="Enter your email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="pl-10 bg-zinc-900/50 border-zinc-800 focus:border-teal-500/50 focus:ring-teal-500/20 h-11"
                  />
                </div>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-3 h-4 w-4 text-zinc-500" />
                <Input
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="pl-10 bg-zinc-900/50 border-zinc-800 focus:border-teal-500/50 focus:ring-teal-500/20 h-11"
                />
              </div>
            </div>

            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 p-3 rounded-lg flex items-start gap-2"
              >
                <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <div>
                  <p>{error}</p>
                  {onShowSystemCheck && (
                    <button
                      type="button"
                      onClick={onShowSystemCheck}
                      className="text-xs underline mt-1 hover:text-red-300"
                    >
                      Check system health
                    </button>
                  )}
                </div>
              </motion.div>
            )}

            <Button
              type="submit"
              className="w-full h-11 bg-teal-500 hover:bg-teal-400 text-black font-semibold"
              disabled={isLoading}
            >
              {isLoading ? (
                <div className="h-5 w-5 border-2 border-black/30 border-t-black rounded-full animate-spin" />
              ) : (
                isLogin ? "Sign In" : "Create Account"
              )}
            </Button>

            <div className="text-center text-sm text-zinc-400">
              {isLogin ? "Don't have an account? " : "Already have an account? "}
              <button
                type="button"
                onClick={() => {
                  setIsLogin(!isLogin);
                  setError("");
                }}
                className="text-teal-400 hover:text-teal-300 font-medium hover:underline transition-colors"
              >
                {isLogin ? "Sign up" : "Sign in"}
              </button>
            </div>
          </form>

          {/* Back to home link */}
          <div className="mt-8 pt-6 border-t border-zinc-800 text-center">
            <a href="/" className="inline-flex items-center text-sm text-zinc-500 hover:text-zinc-300 transition-colors">
              <ArrowLeft className="h-3 w-3 mr-1" />
              Back to Home
            </a>
          </div>
        </motion.div>
      </div>

      {/* Right Side - Visuals */}
      <div className="hidden lg:block w-1/2 relative overflow-hidden bg-zinc-900">
        <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-20" />
        <div className="absolute inset-0 bg-gradient-to-br from-teal-500/20 via-purple-500/20 to-zinc-900/50" />

        {/* Animated blobs */}
        <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-teal-500/30 rounded-full blur-[100px] animate-pulse" />
        <div className="absolute bottom-1/4 left-1/4 w-96 h-96 bg-purple-500/30 rounded-full blur-[100px] animate-pulse delay-1000" />

        <div className="relative z-10 h-full flex flex-col items-center justify-center text-center p-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="max-w-lg"
          >
            <h2 className="text-4xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-white to-white/60">
              Accelerate Your Research
            </h2>
            <p className="text-lg text-zinc-400 leading-relaxed">
              "SynData AI has revolutionized how we approach clinical trials. The synthetic data quality is indistinguishable from real patient records."
            </p>
            <div className="mt-8 flex items-center justify-center gap-4">
              <div className="h-10 w-10 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center text-xs font-bold">
                JD
              </div>
              <div className="text-left">
                <div className="text-sm font-medium text-white">Dr. Jane Doe</div>
                <div className="text-xs text-zinc-500">Director of Clinical Research</div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
