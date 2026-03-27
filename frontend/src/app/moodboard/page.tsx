"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Layout } from "antd";
import MoodBoardForm from "@/components/moodboard/Form";
import AppHeader from "@/components/Header";
import { useAuthStore } from "@/store/authStore";

function MoodboardPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/auth/login");
    }
  }, [isAuthenticated, router]);

  if (!isAuthenticated) {
    return null;
  }

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <AppHeader />
      <Layout.Content className="bg-white">
        <MoodBoardForm />
      </Layout.Content>
    </Layout>
  );
}

export default MoodboardPage;
