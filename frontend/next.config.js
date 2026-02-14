/** @type {import('next').NextConfig} */
const nextConfig = {
  output: process.env.NODE_ENV === "production" ? "standalone" : undefined,
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8001/api/:path*",
      },
      {
        source: "/uploads/:path*",
        destination: "http://127.0.0.1:8001/uploads/:path*",
      },
    ];
  },
};

module.exports = nextConfig;
