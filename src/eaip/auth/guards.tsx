"use client";

import { useEffect } from "react";
import type { ReactNode } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "./context";

function SessionLoading() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-surface-secondary p-4">
      <div className="flex flex-col items-center gap-4 rounded-xl border border-border bg-surface p-8 shadow-card">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-border-subtle border-t-primary" />
        <p className="text-sm text-text-secondary">Loading session...</p>
      </div>
    </div>
  );
}

export interface RequireAuthProps {
  children: ReactNode;
  fallback?: ReactNode;
  redirectTo?: string;
}

export function RequireAuth({ children, fallback, redirectTo = "/login" }: RequireAuthProps) {
  const { isAuthenticated, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push(redirectTo);
    }
  }, [loading, isAuthenticated, router, redirectTo]);

  if (loading) {
    return fallback ?? <SessionLoading />;
  }

  if (!isAuthenticated) {
    return fallback ?? null;
  }

  return children;
}

export interface RequireRoleProps extends RequireAuthProps {
  requiredRole: string;
}

export function RequireRole({
  children,
  requiredRole,
  fallback,
  redirectTo = "/unauthorized",
}: RequireRoleProps) {
  const { isAuthenticated, loading, hasRole } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && isAuthenticated && !hasRole(requiredRole)) {
      router.push(redirectTo);
    }
  }, [loading, isAuthenticated, hasRole, requiredRole, router, redirectTo]);

  if (loading) {
    return fallback ?? <SessionLoading />;
  }

  if (!isAuthenticated || !hasRole(requiredRole)) {
    return fallback ?? null;
  }

  return children;
}

export interface RedirectIfAuthenticatedProps {
  children: ReactNode;
  redirectTo?: string;
}

export function RedirectIfAuthenticated({
  children,
  redirectTo = "/dashboard",
}: RedirectIfAuthenticatedProps) {
  const { isAuthenticated, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && isAuthenticated) {
      router.push(redirectTo);
    }
  }, [loading, isAuthenticated, router, redirectTo]);

  if (loading) {
    return <SessionLoading />;
  }

  return children;
}
