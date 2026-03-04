"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button, Card, Spin, Alert, Empty } from "antd";
import {
  ArrowLeftOutlined,
  FileTextOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  SyncOutlined,
  PlusOutlined,
} from "@ant-design/icons";
import { getHistory, type ProjectOut } from "@/lib/api";

const STATUS_CONFIG: Record<
  string,
  { icon: React.ReactNode; color: string; label: string }
> = {
  draft: {
    icon: <FileTextOutlined />,
    color: "#a1a1aa",
    label: "Черновик",
  },
  analyzing: {
    icon: <SyncOutlined spin />,
    color: "#3b82f6",
    label: "Анализ",
  },
  analyzed: {
    icon: <ClockCircleOutlined />,
    color: "#f59e0b",
    label: "Проанализирован",
  },
  ready: {
    icon: <CheckCircleOutlined />,
    color: "#10b981",
    label: "Готов",
  },
};

export default function DashboardPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<ProjectOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHistory()
      .then(setProjects)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="container !justify-center !items-center !min-h-screen">
        <Spin size="large" />
        <p className="text-[#4b4b53]/60 mt-4">Загрузка проектов...</p>
      </div>
    );
  }

  return (
    <div className="container !gap-8">
      {/* Header */}
      <div>
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          className="!text-[#4b4b53] !mb-4"
          onClick={() => router.push("/")}
        >
          На главную
        </Button>
        <div className="text-center">
          <h1 className="text-[2.5rem] font-extrabold bg-gradient-to-r from-[#1d1d1f] to-[#7d7d85] bg-clip-text text-transparent tracking-[-0.04em] leading-tight mb-2">
            Дашборд
          </h1>
          <p className="text-[1.1rem] text-[#4b4b53] max-w-[600px] mx-auto">
            Все ваши проекты и сгенерированные ТЗ
          </p>
        </div>
      </div>

      {error && (
        <Alert
          type="error"
          message="Ошибка загрузки"
          description={error}
          showIcon
          className="!rounded-2xl"
        />
      )}

      {/* Projects grid */}
      {projects.length === 0 ? (
        <div className="bg-white/40 backdrop-blur-xl rounded-3xl p-12 shadow-[0_2px_16px_rgba(0,0,0,0.04)] text-center">
          <Empty
            description={
              <span className="text-[#4b4b53]/60">
                Пока нет проектов. Создайте первый!
              </span>
            }
          >
            <Button
              type="primary"
              shape="round"
              icon={<PlusOutlined />}
              className="!bg-[#1d1d1f] !border-[#1d1d1f] !mt-4"
              onClick={() => router.push("/moodboard")}
            >
              Новый проект
            </Button>
          </Empty>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((project) => {
            const statusCfg =
              STATUS_CONFIG[project.status] || STATUS_CONFIG.draft;
            const date = new Date(project.created_at).toLocaleDateString(
              "ru-RU",
              {
                day: "numeric",
                month: "long",
                year: "numeric",
              },
            );

            return (
              <Card
                key={project.id}
                hoverable
                variant="borderless"
                className="!rounded-3xl !bg-white/30 !shadow-[0_2px_16px_rgba(0,0,0,0.04)] !transition-all !duration-200 hover:!shadow-[0_8px_32px_rgba(0,0,0,0.08)] hover:!scale-[1.01]"
                onClick={() => {
                  if (project.status === "ready") {
                    router.push(`/brief/${project.id}`);
                  }
                }}
              >
                {/* Color preview bar */}
                {project.selected_colors &&
                  project.selected_colors.length > 0 && (
                    <div className="flex rounded-xl overflow-hidden h-3 mb-4">
                      {project.selected_colors.map((c: string, i: number) => (
                        <div
                          key={i}
                          className="flex-1"
                          style={{ backgroundColor: c }}
                        />
                      ))}
                    </div>
                  )}

                <h3 className="text-lg font-semibold mb-1 tracking-[-0.02em]">
                  {project.name}
                </h3>

                <p className="text-sm text-[#4b4b53]/50 mb-3">{date}</p>

                <div className="flex items-center gap-2">
                  <span style={{ color: statusCfg.color }}>
                    {statusCfg.icon}
                  </span>
                  <span
                    className="text-sm font-medium"
                    style={{ color: statusCfg.color }}
                  >
                    {statusCfg.label}
                  </span>
                </div>

                {project.description && (
                  <p className="text-sm text-[#4b4b53]/60 mt-3 line-clamp-2">
                    {project.description}
                  </p>
                )}
              </Card>
            );
          })}
        </div>
      )}

      {/* New project button */}
      {projects.length > 0 && (
        <div className="text-center pb-4">
          <Button
            size="large"
            shape="round"
            icon={<PlusOutlined />}
            className="!h-14 !px-10 !text-[1.1rem] !bg-white/50 !border-transparent"
            onClick={() => router.push("/moodboard")}
          >
            Новый проект
          </Button>
        </div>
      )}
    </div>
  );
}
