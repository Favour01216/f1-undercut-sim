const { withSentryConfig } = require("@sentry/nextjs");

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable experimental instrumentation
  experimental: {
    instrumentationHook: true,
  },

  // Force fresh builds - disable all caching
  generateBuildId: async () => {
    return `build-${Date.now()}`;
  },

  // Enable standalone output for Docker
  output: "standalone",

  // App Router is now stable in Next.js 14
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/:path*",
      },
    ];
  },
  // Ensure TypeScript path resolution works in CI
  typescript: {
    // This will help with path resolution in CI
    ignoreBuildErrors: false,
  },
  // Ensure webpack resolves paths correctly
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      "@": require("path").resolve(__dirname),
      "@/lib": require("path").resolve(__dirname, "lib"),
      "@/components": require("path").resolve(__dirname, "components"),
    };
    return config;
  },
};

// Sentry configuration options
const sentryWebpackPluginOptions = {
  // For all available options, see:
  // https://github.com/getsentry/sentry-webpack-plugin#options

  // Suppresses source map uploading logs during build
  silent: true,

  // Upload source maps only in production
  dryRun: process.env.NODE_ENV !== "production",

  org: process.env.SENTRY_ORG,
  project: process.env.SENTRY_PROJECT,

  // For all available options, see:
  // https://docs.sentry.io/platforms/javascript/guides/nextjs/manual-setup/

  // Upload a larger set of source maps for prettier stack traces (increases build time)
  widenClientFileUpload: true,

  // Transpiles SDK to be compatible with IE11 (increases bundle size)
  transpileClientSDK: true,

  // Routes browser requests to Sentry through a Next.js rewrite to circumvent ad-blockers (increases server load)
  tunnelRoute: "/monitoring",

  // Hides source maps from generated client bundles
  hideSourceMaps: true,

  // Automatically tree-shake Sentry logger statements to reduce bundle size
  disableLogger: true,
};

module.exports =
  process.env.NEXT_PUBLIC_ENABLE_SENTRY === "true"
    ? withSentryConfig(nextConfig, sentryWebpackPluginOptions)
    : nextConfig;
