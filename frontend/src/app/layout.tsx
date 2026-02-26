import "./globals.css";
import { AntdRegistry } from "@ant-design/nextjs-registry";
import { AntdConfigProvider } from "./providers";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <AntdRegistry>
          <AntdConfigProvider>{children}</AntdConfigProvider>
        </AntdRegistry>
      </body>
    </html>
  );
}
