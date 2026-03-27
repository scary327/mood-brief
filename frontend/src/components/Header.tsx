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
      className="bg-white border-b border-[#e4e4e7]"
      style={{
        padding: "0 24px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
      }}
    >
      <h1 className="text-xl font-bold text-[#1d1d1f] m-0">MoodBrief</h1>

      <Dropdown menu={{ items: menuItems }} placement="bottomRight">
        <Button type="text" size="large">
          <Space>
            <Avatar
              size={32}
              icon={<UserOutlined />}
              className="bg-[#3b82f6]"
            />
            <span className="text-[#1d1d1f] font-medium">{user.username}</span>
          </Space>
        </Button>
      </Dropdown>
    </Header>
  );
}
