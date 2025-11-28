import { useEffect } from "react";
import { Command } from "cmdk";
import type { Screen } from "@/constants/navigation";
import { NAV_ITEMS } from "@/constants/navigation";
import { Search, Calculator, FileText } from "lucide-react";

interface CommandMenuProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onNavigate: (screen: Screen) => void;
}

export function CommandMenu({ open, onOpenChange, onNavigate }: CommandMenuProps) {
    useEffect(() => {
        const down = (e: KeyboardEvent) => {
            if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
                e.preventDefault();
                onOpenChange(!open);
            }
        };

        document.addEventListener("keydown", down);
        return () => document.removeEventListener("keydown", down);
    }, [open, onOpenChange]);

    return (
        <Command.Dialog
            open={open}
            onOpenChange={onOpenChange}
            label="Global Command Menu"
            className="fixed inset-0 z-50 bg-zinc-950/80 backdrop-blur-sm p-4 pt-[20vh] data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0"
            onClick={() => onOpenChange(false)} // Close on backdrop click
        >
            <div
                className="mx-auto max-w-2xl w-full overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900 shadow-2xl ring-1 ring-white/5"
                onClick={(e) => e.stopPropagation()} // Prevent closing when clicking inside
            >
                <div className="flex items-center border-b border-zinc-800 px-4" cmdk-input-wrapper="">
                    <Search className="mr-2 h-5 w-5 shrink-0 text-zinc-500" />
                    <Command.Input
                        placeholder="Type a command or search..."
                        className="flex h-14 w-full bg-transparent py-3 text-sm outline-none placeholder:text-zinc-500 text-zinc-100 disabled:cursor-not-allowed disabled:opacity-50"
                    />
                    <div className="flex items-center text-xs text-zinc-500">
                        <span className="mr-1">ESC</span> to close
                    </div>
                </div>
                <Command.List className="max-h-[300px] overflow-y-auto overflow-x-hidden p-2 scrollbar-thin scrollbar-thumb-zinc-700 scrollbar-track-transparent">
                    <Command.Empty className="py-6 text-center text-sm text-zinc-500">
                        No results found.
                    </Command.Empty>

                    <Command.Group heading="Navigation" className="px-2 py-1.5 text-xs font-medium text-zinc-500">
                        {NAV_ITEMS.map((item) => (
                            <Command.Item
                                key={item.id}
                                onSelect={() => {
                                    onNavigate(item.id);
                                    onOpenChange(false);
                                }}
                                className="flex cursor-pointer select-none items-center rounded-md px-2 py-2 text-sm text-zinc-300 outline-none aria-selected:bg-teal-500/10 aria-selected:text-teal-400 data-[selected=true]:bg-teal-500/10 data-[selected=true]:text-teal-400 transition-colors"
                            >
                                <item.icon className="mr-2 h-4 w-4" />
                                <span>{item.label}</span>
                            </Command.Item>
                        ))}
                    </Command.Group>

                    <Command.Group heading="Quick Actions" className="px-2 py-1.5 text-xs font-medium text-zinc-500 mt-2">
                        <Command.Item
                            onSelect={() => {
                                onNavigate("generate");
                                onOpenChange(false);
                            }}
                            className="flex cursor-pointer select-none items-center rounded-md px-2 py-2 text-sm text-zinc-300 outline-none aria-selected:bg-teal-500/10 aria-selected:text-teal-400 data-[selected=true]:bg-teal-500/10 data-[selected=true]:text-teal-400 transition-colors"
                        >
                            <Calculator className="mr-2 h-4 w-4" />
                            <span>Generate New Dataset</span>
                        </Command.Item>
                        <Command.Item
                            onSelect={() => {
                                onNavigate("studies");
                                onOpenChange(false);
                            }}
                            className="flex cursor-pointer select-none items-center rounded-md px-2 py-2 text-sm text-zinc-300 outline-none aria-selected:bg-teal-500/10 aria-selected:text-teal-400 data-[selected=true]:bg-teal-500/10 data-[selected=true]:text-teal-400 transition-colors"
                        >
                            <FileText className="mr-2 h-4 w-4" />
                            <span>View Recent Studies</span>
                        </Command.Item>
                    </Command.Group>
                </Command.List>
            </div>
        </Command.Dialog>
    );
}
