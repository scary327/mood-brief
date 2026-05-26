"use client";

import { Layout, Dropdown, Button, Avatar, Space } from "antd";
import { LogoutOutlined, UserOutlined } from "@ant-design/icons";
import { useRouter } from "next/navigation";
import { useAuthStore, type User } from "@/store/authStore";

const { Header } = Layout;

export default function AppHeader() {
  const router = useRouter();
  const { user, isAuthenticated, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    router.push("/auth/login");
  };

  if (!isAuthenticated || !user) {
    return null;
  }

  const menuItems = [
    {
      key: "logout",
      icon: <LogoutOutlined />,
      label: "Выйти",
      onClick: handleLogout,
    },
  ];

  return (
    <Header
      className="bg-white border-b border-[#e4e4e7] !px-3 sm:!px-6 !h-14 sm:!h-16"
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 8,
      }}
    >
      <h1 className="text-lg sm:text-xl font-bold text-[#1d1d1f] m-0 truncate">
        MoodBrief
      </h1>

      <Dropdown menu={{ items: menuItems }} placement="bottomRight">
        <Button type="text" size="large" className="!px-2 sm:!px-3">
          <Space size={6}>
            <Avatar
              size={28}
              icon={<UserOutlined />}
              className="bg-[#3b82f6]"
            />
            <span className="text-[#1d1d1f] font-medium hidden sm:inline max-w-[160px] truncate">
              {user.username}
            </span>
          </Space>
        </Button>
      </Dropdown>
    </Header>
  );
}
