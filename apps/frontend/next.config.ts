import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  transpilePackages: ["@acg/contract"],
  turbopack: {
    root: "../../",
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "https://agc-backend-ix19.onrender.com/api/:path*",
      },
    ];
  },
};

export default nextConfig;