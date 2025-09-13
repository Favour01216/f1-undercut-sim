import { init } from "@sentry/nextjs";

const SENTRY_DSN = process.env.SENTRY_DSN;
const SENTRY_ENABLED = process.env.NEXT_PUBLIC_ENABLE_SENTRY === "true";

if (SENTRY_DSN && SENTRY_ENABLED) {
  init({
    dsn: SENTRY_DSN,
    environment: process.env.NEXT_PUBLIC_SENTRY_ENVIRONMENT || "development",
    tracesSampleRate: parseFloat(
      process.env.NEXT_PUBLIC_SENTRY_TRACES_SAMPLE_RATE || "0.1"
    ),
    debug: process.env.NODE_ENV === "development",
    sendDefaultPii: false,
  });
}
