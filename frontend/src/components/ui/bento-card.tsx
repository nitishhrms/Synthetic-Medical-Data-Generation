import { cn } from "@/lib/utils";
import { ReactNode } from "react";

interface BentoCardProps {
    title: string;
    value?: string | number;
    subtitle?: string;
    icon?: any;
    className?: string;
    children?: ReactNode;
    colSpan?: string;
    rowSpan?: string;
}

export const BentoCard = ({
    title,
    value,
    subtitle,
    icon: Icon,
    className,
    children,
    colSpan = "col-span-1",
    rowSpan = "row-span-1"
}: BentoCardProps) => (
    <div className={cn(
        "relative group overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900/50 p-6 transition-all hover:border-zinc-700",
        colSpan,
        rowSpan,
        className
    )}>
        {/* Subtle Gradient Glow on Hover */}
        <div className="absolute -inset-px bg-gradient-to-r from-teal-500/10 to-zinc-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

        <div className="relative z-10 h-full flex flex-col">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-zinc-400 font-mono uppercase tracking-wider">{title}</h3>
                {Icon && <Icon className="h-4 w-4 text-zinc-500 group-hover:text-teal-500 transition-colors" />}
            </div>

            {value && (
                <div className="mt-auto">
                    <p className="text-3xl font-bold text-white tracking-tight">{value}</p>
                    {subtitle && <p className="mt-1 text-xs text-zinc-500">{subtitle}</p>}
                </div>
            )}

            {children}
        </div>
    </div>
);
