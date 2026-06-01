"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Separator } from "@/components/ui/separator";

const navItems = [
  { href: "/",        label: "עמוד הבית",           icon: "🏠" },
  { href: "/find",    label: "מצא אזור להשקעה",      icon: "🔍" },
  { href: "/check",   label: "בדוק נכס ספציפי",      icon: "🏡" },
  { href: "/browse",  label: "עיין בנכסים ביישוב",   icon: "📊" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 shrink-0 bg-white border-l border-border flex flex-col py-6 px-3 shadow-sm">
      <div className="text-center mb-4">
        <div className="text-4xl mb-1">🏠</div>
        <p className="font-bold text-[#006AFF] text-base leading-tight">יועץ נדל&quot;ן חכם</p>
      </div>

      <Separator className="mb-4" />

      <nav className="flex flex-col gap-1">
        {navItems.map(({ href, label, icon }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors",
              pathname === href
                ? "bg-[#EBF3FF] text-[#006AFF]"
                : "text-muted-foreground hover:bg-muted hover:text-foreground"
            )}
          >
            <span>{icon}</span>
            <span>{label}</span>
          </Link>
        ))}
      </nav>

      <div className="mt-auto pt-4">
        <Separator className="mb-3" />
        <p className="text-xs text-muted-foreground leading-relaxed text-right">
          המודל אומן על 6,609 עסקאות נדל&quot;ן אמיתיות בישראל.
          <br /><br />
          הכלי מיועד לסיוע בקבלת החלטות בלבד — אינו תחליף לייעוץ מקצועי.
        </p>
      </div>
    </aside>
  );
}
