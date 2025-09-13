import { init } from "@sentry/nextjs";

const SENTRY_DSN = process.env.SENTRY_DSN;
const SENTRY_ENABLED = process.env.NEXT_PUBLIC_ENABLE_SENTRY === "true";

if (SENTRY_DSN && SENTRY_ENABLED) {
  init({
    dsn: SENTRY_DSN,
    environment: process.env.NEXT_PUBLIC_SENTRY_ENVIRONMENT || "development",

    // Adjust this value in production, or use tracesSampler for greater control
    tracesSampleRate: parseFloat(
      process.env.NEXT_PUBLIC_SENTRY_TRACES_SAMPLE_RATE || "0.1"
    ),

    // Setting this option to true will print useful information to the console while you're setting up Sentry.
    debug: process.env.NODE_ENV === "development",

    // Don't send default PII
    sendDefaultPii: false,

    // Filter out transactions we don't care about
    beforeSend(event) {
      // Filter out Next.js internal routes
      if (event.request?.url?.includes("/_next/")) {
        return null;
      }

      return event;
    },

    beforeSendTransaction(event) {
      // Filter out internal Next.js transactions
      if (event.transaction?.includes("/_next/")) {
        return null;
      }

      return event;
    },
  });
} else {
  console.log(
    "Sentry not initialized on server - either no DSN provided or NEXT_PUBLIC_ENABLE_SENTRY is not true"
  );
}
