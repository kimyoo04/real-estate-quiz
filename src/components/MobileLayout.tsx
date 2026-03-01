import type { ReactNode } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Mail } from "lucide-react";

interface MobileLayoutProps {
  children: ReactNode;
  title?: ReactNode;
  showBack?: boolean;
}

export function MobileLayout({ children, title, showBack = false }: MobileLayoutProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const isHome = location.pathname === "/";

  return (
    <div className="mx-auto flex min-h-dvh max-w-md flex-col bg-background">
      {/* Header */}
      <header className="sticky top-0 z-10 flex h-14 items-center border-b bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        {showBack && !isHome && (
          <button
            onClick={() => navigate(-1)}
            className="mr-3 flex h-8 w-8 items-center justify-center rounded-md hover:bg-accent"
            aria-label="뒤로가기"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="m15 18-6-6 6-6" />
            </svg>
          </button>
        )}
        <h1 className="text-lg font-semibold truncate">
          {title ?? "CertiPass"}
        </h1>
        {isHome && (
          <button
            onClick={() => navigate("/contact")}
            className="ml-auto flex items-center gap-1 rounded-md px-2 py-1 text-xs text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
            aria-label="문의하기"
          >
            <Mail className="h-3.5 w-3.5" />
            <span>문의</span>
          </button>
        )}
      </header>

      {/* Content */}
      <main className="flex-1 overflow-y-auto px-4 py-4">
        {children}
      </main>
    </div>
  );
}
