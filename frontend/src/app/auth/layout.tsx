export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-[#f4f4f5] to-[#e4e4e7] px-4">
      <div className="w-full max-w-md">{children}</div>
    </div>
  );
}
