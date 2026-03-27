import "./globals.css";
import { AntdRegistry } from "@ant-design/nextjs-registry";
import { AntdConfigProvider, AuthProvider } from "./providers";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <AntdRegistry>
          <AntdConfigProvider>
            <AuthProvider>
              {children}
            </AuthProvider>
          </AntdConfigProvider>
        </AntdRegistry>
      </body>
    </html>
  );
}
