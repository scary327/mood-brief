"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button, Spin, Alert, message, Rate, Input, Breadcrumb } from "antd";
import {
  ArrowLeftOutlined,
  DownloadOutlined,
  HomeOutlined,
  CopyOutlined,
  SendOutlined,
  EditOutlined,
} from "@ant-design/icons";
import { apiFetch, getProject, downloadBriefPdf, type ProjectOut } from "@/lib/api";

const TEMPLATE_LABELS: Record<string, string> = {
  gost: "ГОСТ 34.602-2020",
  standard: "Стандартное ТЗ",
  creative: "Креативный бриф",
};

export default function BriefPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [project, setProject] = useState<ProjectOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Feedback state
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");
  const [feedbackSent, setFeedbackSent] = useState(false);
  const [feedbackLoading, setFeedbackLoading] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);
  const [downloadingPdf, setDownloadingPdf] = useState(false);

  useEffect(() => {
    if (!id) return;
    getProject(id)
      .then(setProject)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  const handleCopy = () => {
    if (project?.brief_markdown) {
      navigator.clipboard.writeText(project.brief_markdown);
      message.success("Markdown скопирован в буфер обмена");
    }
  };

  const handleDownloadPdf = async () => {
    if (!project?.pdf_filename) return;
    setDownloadingPdf(true);
    try {
      await downloadBriefPdf(id, project.pdf_filename);
    } catch (e) {
      message.error(e instanceof Error ? e.message : "Не удалось скачать PDF");
    } finally {
      setDownloadingPdf(false);
    }
  };

  const handleSubmitFeedback = async () => {
    if (rating === 0) {
      message.warning("Поставьте оценку (1–5 звёзд)");
      return;
    }
    setFeedbackLoading(true);
    try {
      const res = await apiFetch(`/api/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ project_id: id, rating, comment }),
      });
      const data = await res.json();
      setFeedbackMessage(
        data.message || "Мы учтём ваши пожелания. Спасибо за обратную связь!",
      );
    } catch {
      setFeedbackMessage("Мы учтём ваши пожелания. Спасибо за обратную связь!");
    } finally {
      setFeedbackSent(true);
      setFeedbackLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="container" style={{ justifyContent: "center", alignItems: "center", minHeight: "100vh" }}>
        <Spin size="large" />
        <p style={{ color: "#4b4b53", marginTop: "1rem" }}>Загрузка…</p>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="container" style={{ justifyContent: "center", alignItems: "center", minHeight: "100vh" }}>
        <Alert type="error" message="Ошибка загрузки" description={error || "Проект не найден"} showIcon style={{ borderRadius: "1rem", maxWidth: 400 }} />
        <Button className="mt-4" icon={<HomeOutlined />} onClick={() => router.push("/dashboard")}>На дашборд</Button>
      </div>
    );
  }

  const hasPdf = Boolean(project.pdf_filename);
  const templateLabel = TEMPLATE_LABELS[project.template_id] || project.template_id;

  return (
    <div className="container" style={{ gap: "2rem" }}>
      {/* Breadcrumbs + back */}
      <div>
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          style={{ color: "#4b4b53", marginBottom: "0.75rem" }}
          onClick={() => router.back()}
        >
          Назад
        </Button>
        <Breadcrumb
          items={[
            { title: <span style={{ cursor: "pointer" }} onClick={() => router.push("/dashboard")}>Дашборд</span> },
            { title: project.name },
          ]}
          style={{ fontSize: "0.85rem", color: "#4b4b53" }}
        />
      </div>

      {/* Header */}
      <div className="text-center">
        <h1
          className="text-3xl sm:text-4xl md:text-[2.2rem]"
          style={{
            fontWeight: 800,
            background: "linear-gradient(to right, #1d1d1f, #7d7d85)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            letterSpacing: "-0.04em",
            lineHeight: 1.2,
            marginBottom: "0.5rem",
          }}
        >
          {project.name}
        </h1>
        <p className="text-base sm:text-[1.05rem]" style={{ color: "#4b4b53" }}>
          Техническое задание •{" "}
          <span style={{ fontWeight: 600 }}>{templateLabel}</span>
        </p>
      </div>

      {/* Brief content */}
      {project.brief_markdown && (
        <div
          className="p-4 sm:p-8 rounded-2xl sm:rounded-3xl"
          style={{
            background: "rgba(255,255,255,0.4)",
            backdropFilter: "blur(24px)",
            boxShadow: "0 2px 16px rgba(0,0,0,0.04)",
            overflowX: "auto",
          }}
        >
          <div
            className="prose prose-sm sm:prose-lg max-w-none
              prose-headings:text-[#1d1d1f] prose-headings:tracking-[-0.02em]
              prose-p:text-[#4b4b53] prose-p:leading-relaxed
              prose-li:text-[#4b4b53]
              prose-table:text-sm
              prose-th:text-left prose-th:font-semibold
              prose-code:bg-black/5 prose-code:rounded prose-code:px-1.5"
            dangerouslySetInnerHTML={{ __html: markdownToHtml(project.brief_markdown) }}
          />
        </div>
      )}

      {/* Action buttons */}
      <div className="flex flex-col sm:flex-row sm:flex-wrap justify-center items-stretch sm:items-center gap-2 sm:gap-3">
        {project.brief_markdown && (
          <>
            <Button
              size="large"
              shape="round"
              icon={<EditOutlined />}
              className="!h-12 sm:!h-[3.25rem] !px-5 sm:!px-7 !text-sm sm:!text-base"
              style={{ background: "rgba(255,255,255,0.8)", border: "none" }}
              onClick={() => router.push(`/brief/${id}/editor`)}
            >
              Редактировать
            </Button>
            <Button
              size="large"
              shape="round"
              icon={<CopyOutlined />}
              className="!h-12 sm:!h-[3.25rem] !px-5 sm:!px-7 !text-sm sm:!text-base"
              style={{ background: "rgba(255,255,255,0.8)", border: "none" }}
              onClick={handleCopy}
            >
              Скопировать
            </Button>
          </>
        )}
        {hasPdf && (
          <Button
            type="primary"
            size="large"
            shape="round"
            icon={<DownloadOutlined />}
            loading={downloadingPdf}
            className="!h-12 sm:!h-[3.25rem] !px-6 sm:!px-8 !text-sm sm:!text-base"
            style={{ background: "#1d1d1f", borderColor: "#1d1d1f", boxShadow: "0 8px 24px rgba(29,29,31,0.2)" }}
            onClick={handleDownloadPdf}
          >
            Скачать PDF
          </Button>
        )}
        <Button
          size="large"
          shape="round"
          icon={<HomeOutlined />}
          className="!h-12 sm:!h-[3.25rem] !px-5 sm:!px-7 !text-sm sm:!text-base"
          style={{ background: "rgba(255,255,255,0.5)", border: "none" }}
          onClick={() => router.push("/dashboard")}
        >
          Дашборд
        </Button>
      </div>

      {/* Feedback */}
      {project.brief_markdown && (
        <div
          style={{
            background: "rgba(255,255,255,0.5)",
            backdropFilter: "blur(20px)",
            borderRadius: "1.5rem",
            padding: "2rem",
            textAlign: "center",
            maxWidth: 600,
            margin: "0 auto",
            width: "100%",
          }}
        >
          <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#1d1d1f", marginBottom: "0.4rem" }}>
            Насколько ТЗ совпало с вашим видением?
          </h3>
          <p style={{ color: "#4b4b53", marginBottom: "1.25rem", fontSize: "0.9rem" }}>
            Ваша обратная связь помогает улучшить качество генерации
          </p>
          {feedbackSent ? (
            <Alert type="success" message={feedbackMessage || "Спасибо!"} showIcon style={{ borderRadius: "1rem" }} />
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.9rem", alignItems: "center" }}>
              <Rate value={rating} onChange={setRating} style={{ fontSize: "1.75rem" }} />
              <Input.TextArea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Комментарий (необязательно)…"
                rows={3}
                maxLength={1000}
                showCount
                style={{ borderRadius: "0.75rem", fontSize: "0.9rem", resize: "none", width: "100%" }}
              />
              <Button
                type="primary"
                size="large"
                shape="round"
                icon={<SendOutlined />}
                loading={feedbackLoading}
                onClick={handleSubmitFeedback}
                style={{ background: "#1d1d1f", borderColor: "#1d1d1f", height: "2.75rem", padding: "0 2rem" }}
              >
                Отправить отзыв
              </Button>
            </div>
          )}
        </div>
      )}

      <div style={{ paddingBottom: "3rem" }} />
    </div>
  );
}

// ─── Markdown → HTML ─────────────────────────────────────────────────────────

function markdownToHtml(md: string): string {
  let html = md
    .replace(/^####\s+(.+)$/gm, "<h4>$1</h4>")
    .replace(/^###\s+(.+)$/gm, "<h3>$1</h3>")
    .replace(/^##\s+(.+)$/gm, "<h2>$1</h2>")
    .replace(/^#\s+(.+)$/gm, "<h1>$1</h1>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/(?<!\w)_(.+?)_(?!\w)/g, "<em>$1</em>")
    .replace(/`(.+?)`/g, "<code>$1</code>")
    .replace(/^---+$/gm, "<hr/>")
    .replace(/^[-*]\s+(.+)$/gm, "<li>$1</li>")
    .replace(/^\d+\.\s+(.+)$/gm, "<li>$1</li>")
    .replace(/^\|(.+)\|$/gm, (_: string, row: string) => {
      if (row.replace(/[\s\-:|]/g, "").length === 0) return "";
      const cells = row.split("|").map((c: string) => c.trim()).filter(Boolean);
      return "<tr>" + cells.map((c: string) => `<td>${c}</td>`).join("") + "</tr>";
    });

  html = html.replace(/((?:<li>.+<\/li>\n?)+)/g, "<ul>$1</ul>");
  html = html.replace(
    /((?:<tr>.+<\/tr>\n?)+)/g,
    '<table class="w-full border-collapse mb-4">$1</table>',
  );

  html = html
    .split("\n")
    .map((line) => {
      const t = line.trim();
      if (!t) return "";
      if (/^<(h[1-4]|ul|li|table|tr|hr|strong|em)/.test(t)) return t;
      return `<p>${t}</p>`;
    })
    .join("\n");

  return html;
}
