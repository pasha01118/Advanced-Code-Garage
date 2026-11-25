import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  transpilePackages: ["@acg/contract"],
  turbopack: {
    root: "../../",
  },
};

export default nextConfig;