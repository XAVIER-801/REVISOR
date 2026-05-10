/** @type {import('next').NextConfig} */
const nextConfig = {
  serverExternalPackages: ['jszip', 'xml2js'],
  output: 'standalone',
};

export default nextConfig;
