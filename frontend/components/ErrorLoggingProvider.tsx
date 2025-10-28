"use client";

import { useEffect } from "react";
import { setupGlobalErrorHandlers } from "@/lib/error-logging";

/**
 * Component to initialize global error handlers.
 * Should be mounted once in the app root.
 */
export function ErrorLoggingProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  useEffect(() => {
    setupGlobalErrorHandlers();
  }, []);

  return <>{children}</>;
}

