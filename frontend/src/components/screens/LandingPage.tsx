import { motion, useScroll, useTransform } from "framer-motion";
import {
    Brain,
    Shield,
    Zap,
    Activity,
    Database,
    Lock,
    ArrowRight,
    CheckCircle2,
    Globe,
    Play
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface LandingPageProps {
    onLogin: () => void;
}

export function LandingPage({ onLogin }: LandingPageProps) {
    const { scrollY } = useScroll();
    const y1 = useTransform(scrollY, [0, 500], [0, 200]);
    const opacity = useTransform(scrollY, [0, 300], [1, 0]);

    return (
        <div className="min-h-screen bg-zinc-950 text-white overflow-x-hidden selection:bg-teal-500/30">
            {/* Navigation */}
            <nav className="fixed top-0 left-0 right-0 z-50 border-b border-white/5 bg-zinc-950/50 backdrop-blur-xl">
                <div className="container mx-auto px-6 h-20 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="relative h-8 w-8">
                            <div className="absolute inset-0 bg-teal-500 blur-lg opacity-50 animate-pulse" />
                            <Brain className="relative h-8 w-8 text-teal-400" />
                        </div>
                        <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">
                            SynData<span className="text-teal-500">AI</span>
                        </span>
                    </div>

                    <div className="hidden md:flex items-center gap-8 text-sm font-medium text-zinc-400">
                        <a href="#features" className="hover:text-white transition-colors">Features</a>
                        <a href="#technology" className="hover:text-white transition-colors">Technology</a>
                        <a href="#security" className="hover:text-white transition-colors">Security</a>
                    </div>

                    <div className="flex items-center gap-4">
                        <Button
                            variant="ghost"
                            className="text-zinc-400 hover:text-white hover:bg-white/5"
                            onClick={onLogin}
                        >
                            Sign In
                        </Button>
                        <Button
                            className="bg-teal-500 hover:bg-teal-400 text-black font-semibold rounded-full px-6"
                            onClick={onLogin}
                        >
                            Get Started
                        </Button>
                    </div>
                </div>
            </nav>

            {/* Hero Section */}
            <section className="relative min-h-screen flex items-center justify-center pt-20 overflow-hidden">
                {/* Background Elements */}
                <div className="absolute inset-0 overflow-hidden pointer-events-none">
                    <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-teal-500/20 rounded-full blur-[120px] animate-pulse" />
                    <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-purple-500/20 rounded-full blur-[120px] animate-pulse delay-1000" />
                    <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-20" />
                </div>

                <div className="container relative z-10 px-6 text-center">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8 }}
                        className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-teal-500/30 bg-teal-500/10 text-teal-400 text-sm font-medium mb-8"
                    >
                        <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-teal-500"></span>
                        </span>
                        Next Generation Clinical Data Synthesis
                    </motion.div>

                    <motion.h1
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8, delay: 0.2 }}
                        className="text-5xl md:text-8xl font-bold tracking-tight mb-8"
                    >
                        <span className="block text-transparent bg-clip-text bg-gradient-to-b from-white to-white/40 pb-4">
                            Accelerate Cures with
                        </span>
                        <span className="block text-transparent bg-clip-text bg-gradient-to-r from-teal-400 via-cyan-400 to-purple-400">
                            Synthetic Intelligence
                        </span>
                    </motion.h1>

                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8, delay: 0.4 }}
                        className="text-xl text-zinc-400 max-w-2xl mx-auto mb-12 leading-relaxed"
                    >
                        Generate regulatory-grade synthetic clinical trial data in seconds.
                        Reduce costs, protect privacy, and bring life-saving treatments to market faster.
                    </motion.p>

                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8, delay: 0.6 }}
                        className="flex flex-col sm:flex-row items-center justify-center gap-4"
                    >
                        <Button
                            size="lg"
                            className="h-14 px-8 text-lg bg-white text-black hover:bg-zinc-200 rounded-full w-full sm:w-auto group"
                            onClick={onLogin}
                        >
                            Start Generating
                            <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
                        </Button>
                        <Button
                            size="lg"
                            variant="outline"
                            className="h-14 px-8 text-lg border-zinc-800 hover:bg-zinc-900 text-zinc-300 rounded-full w-full sm:w-auto"
                        >
                            <Play className="mr-2 h-5 w-5" />
                            Watch Demo
                        </Button>
                    </motion.div>

                    {/* Floating UI Elements Animation */}
                    <motion.div
                        style={{ y: y1, opacity }}
                        className="absolute top-1/2 -right-20 hidden lg:block pointer-events-none"
                    >
                        <div className="bg-zinc-900/90 backdrop-blur-xl border border-zinc-800 p-4 rounded-2xl shadow-2xl transform rotate-12">
                            <div className="flex items-center gap-4 mb-4">
                                <div className="h-10 w-10 rounded-full bg-teal-500/20 flex items-center justify-center">
                                    <Activity className="h-6 w-6 text-teal-500" />
                                </div>
                                <div>
                                    <div className="text-sm font-medium text-zinc-200">Heart Rate Analysis</div>
                                    <div className="text-xs text-zinc-500">Real-time generation</div>
                                </div>
                            </div>
                            <div className="h-24 w-48 bg-gradient-to-t from-teal-500/10 to-transparent rounded-lg border border-teal-500/20 relative overflow-hidden">
                                <div className="absolute inset-0 flex items-end justify-around pb-2">
                                    {[40, 65, 45, 70, 50, 80, 60].map((h, i) => (
                                        <motion.div
                                            key={i}
                                            initial={{ height: 0 }}
                                            animate={{ height: `${h}%` }}
                                            transition={{ duration: 1, repeat: Infinity, repeatType: "reverse", delay: i * 0.1 }}
                                            className="w-4 bg-teal-500/50 rounded-t-sm"
                                        />
                                    ))}
                                </div>
                            </div>
                        </div>
                    </motion.div>
                </div>
            </section>

            {/* Stats Section */}
            <section className="py-20 border-y border-white/5 bg-zinc-900/30 backdrop-blur-sm">
                <div className="container mx-auto px-6">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-12">
                        {[
                            { label: "Data Points Generated", value: "1B+", icon: Database },
                            { label: "Privacy Score", value: "99.9%", icon: Shield },
                            { label: "Processing Time", value: "<2ms", icon: Zap },
                            { label: "Global Compliance", value: "100%", icon: Globe },
                        ].map((stat, index) => (
                            <motion.div
                                key={index}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: index * 0.1 }}
                                className="text-center group"
                            >
                                <div className="mb-4 inline-flex p-3 rounded-2xl bg-zinc-900 border border-zinc-800 group-hover:border-teal-500/50 group-hover:bg-teal-500/10 transition-all duration-300">
                                    <stat.icon className="h-6 w-6 text-zinc-400 group-hover:text-teal-500 transition-colors" />
                                </div>
                                <div className="text-3xl font-bold text-white mb-1">{stat.value}</div>
                                <div className="text-sm text-zinc-500">{stat.label}</div>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Features Grid */}
            <section id="features" className="py-32 relative">
                <div className="container mx-auto px-6">
                    <div className="text-center max-w-3xl mx-auto mb-20">
                        <h2 className="text-3xl md:text-5xl font-bold mb-6">
                            Designed for the Future of <br />
                            <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-400 to-purple-400">Clinical Research</span>
                        </h2>
                        <p className="text-zinc-400 text-lg">
                            Our platform combines advanced generative AI with rigorous statistical validation to create synthetic data that mirrors reality.
                        </p>
                    </div>

                    <div className="grid md:grid-cols-3 gap-8">
                        {[
                            {
                                title: "Generative AI Models",
                                description: "State-of-the-art GANs and VAEs trained on millions of real patient records.",
                                icon: Brain,
                                color: "teal"
                            },
                            {
                                title: "Privacy Guarantee",
                                description: "Differential privacy and k-anonymity ensure zero re-identification risk.",
                                icon: Lock,
                                color: "purple"
                            },
                            {
                                title: "Instant Validation",
                                description: "Automated quality reports comparing statistical properties in real-time.",
                                icon: CheckCircle2,
                                color: "cyan"
                            }
                        ].map((feature, index) => (
                            <motion.div
                                key={index}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: index * 0.2 }}
                                className="relative p-8 rounded-3xl bg-zinc-900/50 border border-white/5 hover:border-teal-500/30 hover:bg-zinc-900/80 transition-all duration-500 group overflow-hidden"
                            >
                                <div className={`absolute inset-0 bg-gradient-to-br from-${feature.color}-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />

                                <div className="relative z-10">
                                    <div className="h-12 w-12 rounded-2xl bg-zinc-800 border border-zinc-700 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-500">
                                        <feature.icon className="h-6 w-6 text-white" />
                                    </div>
                                    <h3 className="text-xl font-bold mb-3">{feature.title}</h3>
                                    <p className="text-zinc-400 leading-relaxed">
                                        {feature.description}
                                    </p>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="py-32 relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-b from-zinc-950 to-teal-950/20" />
                <div className="container mx-auto px-6 relative z-10">
                    <div className="max-w-4xl mx-auto text-center p-12 rounded-[3rem] border border-white/10 bg-zinc-900/50 backdrop-blur-xl relative overflow-hidden">
                        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full bg-gradient-to-b from-teal-500/10 to-transparent pointer-events-none" />

                        <h2 className="text-4xl md:text-5xl font-bold mb-6 relative z-10">
                            Ready to Revolutionize Your Research?
                        </h2>
                        <p className="text-xl text-zinc-400 mb-10 max-w-2xl mx-auto relative z-10">
                            Join leading pharmaceutical companies and research institutions using SynData AI.
                        </p>
                        <Button
                            size="lg"
                            className="h-16 px-10 text-lg bg-white text-black hover:bg-zinc-200 rounded-full relative z-10"
                            onClick={onLogin}
                        >
                            Get Started Now
                        </Button>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="py-12 border-t border-white/5 bg-zinc-950">
                <div className="container mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-6">
                    <div className="flex items-center gap-2">
                        <Brain className="h-6 w-6 text-teal-500" />
                        <span className="text-lg font-bold text-zinc-200">SynData AI</span>
                    </div>
                    <div className="text-sm text-zinc-500">
                        © 2025 Synthetic Data Generation Platform. All rights reserved.
                    </div>
                </div>
            </footer>
        </div>
    );
}
