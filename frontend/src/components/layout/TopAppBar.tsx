import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import { LogOut, User } from "lucide-react";

export function TopAppBar() {
  const { user, logout } = useAuth();

  return (
    <header className="sticky top-0 z-50 w-full border-b border-primary/10 bg-gradient-to-r from-background via-primary/5 to-background backdrop-blur-xl shadow-sm">
      <div className="container flex h-16 items-center px-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-primary to-primary/70 rounded-xl shadow-md">
            <svg
              className="h-6 w-6 text-primary-foreground"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M12 2L2 7l10 5 10-5-10-5z" />
              <path d="M2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
          </div>
          <div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
              Clinical Trial Analytics
            </h1>
            <p className="text-xs text-muted-foreground">Synthetic Data Generation Platform</p>
          </div>
        </div>

        <div className="ml-auto flex items-center gap-4">
          {user && (
            <>
              <div className="flex items-center gap-2 text-sm bg-primary/5 px-3 py-2 rounded-lg border border-primary/10">
                <div className="p-1 bg-primary/10 rounded-full">
                  <User className="h-3 w-3 text-primary" />
                </div>
                <span className="font-medium">{user.username}</span>
                <span className="text-muted-foreground text-xs">·</span>
                <span className="text-primary text-xs font-medium capitalize">{user.role}</span>
              </div>
              <Button variant="ghost" size="sm" onClick={logout} className="hover:bg-destructive/10 hover:text-destructive">
                <LogOut className="h-4 w-4 mr-2" />
                Logout
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
