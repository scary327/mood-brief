"use client";

import { ConfigProvider } from "antd";

export function AntdConfigProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: "#18181b",
          colorSuccess: "#16a34a",
          colorWarning: "#d97706",
          colorError: "#dc2626",
          colorInfo: "#18181b",
          colorTextBase: "#09090b",
          colorBgBase: "#ffffff",
          colorPrimaryBg: "#f4f4f5",
          colorPrimaryBgHover: "#e4e4e7",
          colorPrimaryBorder: "#a1a1aa",
          colorPrimaryBorderHover: "#71717a",
          colorPrimaryHover: "#27272a",
          colorPrimaryActive: "#09090b",
          colorPrimaryText: "#18181b",
          colorPrimaryTextHover: "#27272a",
          colorPrimaryTextActive: "#09090b",
          colorSuccessBg: "#f0fdf4",
          colorSuccessBgHover: "#dcfce7",
          colorSuccessBorder: "#bbf7d0",
          colorSuccessBorderHover: "#86efac",
          colorSuccessHover: "#15803d",
          colorSuccessActive: "#14532d",
          colorSuccessText: "#16a34a",
          colorSuccessTextHover: "#15803d",
          colorSuccessTextActive: "#14532d",
          colorWarningBg: "#fffbeb",
          colorWarningBgHover: "#fef3c7",
          colorWarningBorder: "#fde68a",
          colorWarningBorderHover: "#fcd34d",
          colorWarningHover: "#b45309",
          colorWarningActive: "#92400e",
          colorWarningText: "#d97706",
          colorWarningTextHover: "#b45309",
          colorWarningTextActive: "#92400e",
          colorErrorBg: "#fef2f2",
          colorErrorBgHover: "#fee2e2",
          colorErrorBorder: "#fecaca",
          colorErrorBorderHover: "#fca5a5",
          colorErrorHover: "#b91c1c",
          colorErrorActive: "#7f1d1d",
          colorErrorText: "#dc2626",
          colorErrorTextHover: "#b91c1c",
          colorErrorTextActive: "#7f1d1d",
          colorInfoBg: "#f4f4f5",
          colorInfoBgHover: "#e4e4e7",
          colorInfoBorder: "#a1a1aa",
          colorInfoBorderHover: "#71717a",
          colorInfoHover: "#27272a",
          colorInfoActive: "#09090b",
          colorInfoText: "#18181b",
          colorInfoTextHover: "#27272a",
          colorInfoTextActive: "#09090b",
          colorText: "#09090b",
          colorTextSecondary: "#52525b",
          colorTextTertiary: "#a1a1aa",
          colorTextQuaternary: "#d4d4d8",
          colorTextDisabled: "#a1a1aa",
          colorBgContainer: "#ffffff",
          colorBgElevated: "#ffffff",
          colorBgLayout: "#fafafa",
          colorBgSpotlight: "rgba(9, 9, 11, 0.8)",
          colorBgMask: "rgba(9, 9, 11, 0.6)",
          colorBorder: "#e4e4e7",
          colorBorderSecondary: "#f4f4f5",
          borderRadius: 6,
          borderRadiusXS: 2,
          borderRadiusSM: 4,
          borderRadiusLG: 8,
          padding: 16,
          paddingSM: 12,
          paddingLG: 20,
          margin: 16,
          marginSM: 12,
          marginLG: 20,
          boxShadow:
            "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)",
          boxShadowSecondary:
            "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)",
        },
      }}
    >
      {children}
    </ConfigProvider>
  );
}
