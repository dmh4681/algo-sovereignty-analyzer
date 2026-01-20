import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async redirects() {
    return [
      {
        source: '/philosophy',
        destination: '/about',
        permanent: true,
      },
    ];
  },
  async rewrites() {
    // NEXT_PUBLIC_API_URL should include /api/v1 (e.g., https://api.algosovereignty.com/api/v1)
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
    return [
      {
        source: '/api/v1/:path*',
        destination: `${apiUrl}/:path*`, // Proxy to FastAPI backend (Railway in production)
      },
    ];
  },
  // Suppress hydration warnings in development
  reactStrictMode: true,

  // Webpack configuration for wallet packages
  webpack: (config, { isServer }) => {
    // Handle Node.js modules in browser context
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
        crypto: false,
        stream: false,
        http: false,
        https: false,
        zlib: false,
        path: false,
        os: false,
        worker_threads: false,
      };
    }

    // Exclude test files from bundling
    config.module.rules.push({
      test: /\.test\.(js|ts|tsx)$/,
      loader: 'ignore-loader',
    });

    return config;
  },

  // Transpile wallet packages
  transpilePackages: [
    '@txnlab/use-wallet',
    '@txnlab/use-wallet-react',
    '@walletconnect/sign-client',
    '@walletconnect/modal',
    '@perawallet/connect',
    '@blockshake/defly-connect',
  ],

  // Use experimental features
  experimental: {
    // Enable Server Components
    serverActions: {
      bodySizeLimit: '2mb',
    },
  },
};

export default nextConfig;
