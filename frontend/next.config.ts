import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  devIndicators: false,
  // Hosts allowed to invoke Server Actions. Next compares the request Origin
  // with the bound host; mismatch → 500 with an opaque digest. Needed when
  // the app is reached via a tunnel/proxy domain (devtunnels, ngrok, etc.).
  allowedDevOrigins: ["*.devtunnels.ms"],
  experimental: {
    serverActions: {
      allowedOrigins: [
        "localhost",
        "localhost:80",
        "localhost:3000",
        "127.0.0.1",
        "127.0.0.1:80",
        "127.0.0.1:3000",
        "*.devtunnels.ms",
        "*.ngrok-free.dev",
        "*.ngrok-free.app",
        "*.ngrok.io",
      ],
    },
  },
};

export default nextConfig;
