import { init } from "@sentry/nextjs";

const SENTRY_DSN = process.env.SENTRY_DSN || process.env.NEXT_PUBLIC_SENTRY_DSN;
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

    replaysOnErrorSampleRate: 1.0,

    // This sets the sample rate to be 10%. You may want this to be 100% while
    // in development and sample at a lower rate in production
    replaysSessionSampleRate: 0.1,

    // You can remove this option if you're not planning to use the Sentry Session Replay feature:
    integrations: [
      // Additional integrations can be added here
    ],

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

  console.log("Sentry initialized for frontend", {
    environment: process.env.NEXT_PUBLIC_SENTRY_ENVIRONMENT || "development",
    tracesSampleRate: parseFloat(
      process.env.NEXT_PUBLIC_SENTRY_TRACES_SAMPLE_RATE || "0.1"
    ),
  });
} else {
  console.log(
    "Sentry not initialized - either no DSN provided or NEXT_PUBLIC_ENABLE_SENTRY is not true"
  );
}
