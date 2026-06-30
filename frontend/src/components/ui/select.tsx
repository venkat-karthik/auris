import * as React from "react";
import { ChevronDown } from "lucide-react";

interface SelectProps {
  value: string;
  onValueChange: (value: string) => void;
  children: React.ReactNode;
}

const SelectContext = React.createContext<{
  value: string;
  onValueChange: (value: string) => void;
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
} | null>(null);

export function Select({ value, onValueChange, children }: SelectProps) {
  const [open, setOpen] = React.useState(false);
  const containerRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <SelectContext.Provider value={{ value, onValueChange, open, setOpen }}>
      <div ref={containerRef} className="relative w-full">
        {children}
      </div>
    </SelectContext.Provider>
  );
}

export function SelectTrigger({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  const context = React.useContext(SelectContext);
  if (!context) throw new Error("SelectTrigger must be used inside Select");
  return (
    <button
      type="button"
      onClick={() => context.setOpen(!context.open)}
      className={`flex items-center justify-between w-full px-4 py-2 text-xs font-medium rounded-xl border border-slate-200 dark:border-zinc-800 bg-white/70 dark:bg-zinc-950/70 focus:outline-none focus:ring-2 focus:ring-purple-500/50 text-left ${className}`}
    >
      {children}
      <ChevronDown className="w-4 h-4 ml-2 text-slate-400 shrink-0" />
    </button>
  );
}

export function SelectValue({ placeholder }: { placeholder: string }) {
  const context = React.useContext(SelectContext);
  if (!context) throw new Error("SelectValue must be used inside Select");
  
  // Find matching select label to show
  return <span>{context.value || placeholder}</span>;
}

export function SelectContent({ children }: { children: React.ReactNode }) {
  const context = React.useContext(SelectContext);
  if (!context) throw new Error("SelectContent must be used inside Select");
  if (!context.open) return null;
  return (
    <div className="absolute left-0 right-0 z-50 mt-1.5 overflow-hidden rounded-xl border border-slate-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 shadow-xl max-h-[200px] overflow-y-auto">
      <div className="p-1">{children}</div>
    </div>
  );
}

interface SelectItemProps {
  value: string;
  children: React.ReactNode;
}

export function SelectItem({ value, children }: SelectItemProps) {
  const context = React.useContext(SelectContext);
  if (!context) throw new Error("SelectItem must be used inside Select");
  const selected = context.value === value;
  return (
    <button
      type="button"
      onClick={() => {
        context.onValueChange(value);
        context.setOpen(false);
      }}
      className={`w-full text-left px-3 py-2 rounded-lg text-xs font-semibold hover:bg-slate-100 dark:hover:bg-zinc-900/60 transition-colors ${
        selected
          ? "bg-purple-500/10 text-purple-600 dark:text-purple-400"
          : "text-slate-700 dark:text-slate-300"
      }`}
    >
      {children}
    </button>
  );
}
