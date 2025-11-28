import { NAV_ITEMS, type Screen } from "@/constants/navigation";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { LogOut } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface GlassSidebarProps {
    activeScreen: Screen;
    onScreenChange: (screen: Screen) => void;
}

export function GlassSidebar({ activeScreen, onScreenChange }: GlassSidebarProps) {
    const { logout } = useAuth();

    return (
        <motion.nav
            initial={{ x: -20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            className="relative z-40 flex h-screen w-20 flex-col items-center justify-between border-r border-zinc-800 bg-zinc-950/80 py-6 backdrop-blur-md"
        >
            <div className="flex flex-col items-center gap-4 w-full px-2">
                <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-teal-500/10 text-teal-500">
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        className="h-6 w-6"
                    >
                        <path d="M12 2v20M2 12h20" />
                        <path d="m17 17-5 5-5-5" />
                        <path d="m17 7-5-5-5 5" />
                    </svg>
                </div>

                <div className="flex flex-col gap-2 w-full">
                    {NAV_ITEMS.map((item) => {
                        const isActive = activeScreen === item.id;
                        const Icon = item.icon;

                        return (
                            <button
                                key={item.id}
                                onClick={() => onScreenChange(item.id)}
                                className={cn(
                                    "group relative flex h-10 w-full items-center justify-center rounded-lg transition-all hover:bg-zinc-800/50",
                                    isActive ? "text-teal-400" : "text-zinc-400 hover:text-zinc-100"
                                )}
                                title={item.label}
                            >
                                {isActive && (
                                    <motion.div
                                        layoutId="activeTab"
                                        className="absolute inset-0 rounded-lg bg-zinc-800/50 border border-zinc-700/50"
                                        initial={false}
                                        transition={{ type: "spring", stiffness: 500, damping: 30 }}
                                    />
                                )}
                                <Icon className="relative z-10 h-5 w-5" />

                                {/* Tooltip on hover */}
                                <div className="absolute left-14 hidden rounded-md border border-zinc-800 bg-zinc-900 px-2 py-1 text-xs font-medium text-zinc-200 opacity-0 shadow-xl group-hover:block group-hover:opacity-100 z-50 whitespace-nowrap">
                                    {item.label}
                                </div>
                            </button>
                        );
                    })}
                </div>
            </div>

            <div className="flex flex-col gap-4 w-full px-2">
                <button
                    onClick={logout}
                    className="flex h-10 w-full items-center justify-center rounded-lg text-zinc-400 transition-colors hover:bg-red-500/10 hover:text-red-400"
                    title="Logout"
                >
                    <LogOut className="h-5 w-5" />
                </button>
            </div>
        </motion.nav>
    );
}
