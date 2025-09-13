/** @type {import('next').NextConfig} */
const nextConfig = {
  // App Router is now stable in Next.js 14
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/:path*',
      },
    ]
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
      '@': require('path').resolve(__dirname),
      '@/lib': require('path').resolve(__dirname, 'lib'),
      '@/components': require('path').resolve(__dirname, 'components'),
    }
    return config
  },
}

module.exports = nextConfig
