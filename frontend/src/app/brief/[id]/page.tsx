"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button, Spin, Alert, message } from "antd";
import {
  ArrowLeftOutlined,
  DownloadOutlined,
  HomeOutlined,
  CopyOutlined,
} from "@ant-design/icons";
import { getProject, getBriefPdfUrl, type ProjectOut } from "@/lib/api";
import TagList from "@/components/moodboard/TagList";
import type { ImageTagSet } from "@/lib/api";

export default function BriefPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [project, setProject] = useState<ProjectOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    getProject(id)
      .then(setProject)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="container !justify-center !items-center !min-h-screen">
        <Spin size="large" />
        <p className="text-[#4b4b53]/60 mt-4">Загрузка проекта...</p>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="container !justify-center !items-center !min-h-screen">
        <Alert
          type="error"
          message="Ошибка загрузки"
          description={error || "Проект не найден"}
          showIcon
          className="!rounded-2xl !max-w-md"
        />
        <Button
          className="mt-4"
          icon={<HomeOutlined />}
          onClick={() => router.push("/")}
        >
          На главную
        </Button>
      </div>
    );
  }

  const pdfUrl = project.pdf_filename ? getBriefPdfUrl(id) : null;

  const handleCopyMarkdown = () => {
    if (project?.brief_markdown) {
      navigator.clipboard.writeText(project.brief_markdown);
      message.success("Markdown скопирован в буфер обмена!");
    }
  };

  return (
    <div className="container !gap-8">
      {/* Header */}
      <div>
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          className="!text-[#4b4b53] !mb-4"
          onClick={() => router.push("/moodboard")}
        >
          Назад к мудборду
        </Button>
        <div className="text-center">
          <h1 className="text-[2.5rem] font-extrabold bg-gradient-to-r from-[#1d1d1f] to-[#7d7d85] bg-clip-text text-transparent tracking-[-0.04em] leading-tight mb-2">
            {project.name}
          </h1>
          <p className="text-[1.1rem] text-[#4b4b53]">
            Техническое задание • статус:{" "}
            <span className="font-semibold capitalize">{project.status}</span>
          </p>
        </div>
      </div>

      {/* Brief content */}
      {project.brief_markdown && (
        <div className="bg-white/40 backdrop-blur-xl rounded-3xl p-8 shadow-[0_2px_16px_rgba(0,0,0,0.04)]">
          <div
            className="prose prose-lg max-w-none
              prose-headings:text-[#1d1d1f] prose-headings:tracking-[-0.02em]
              prose-p:text-[#4b4b53] prose-p:leading-relaxed
              prose-li:text-[#4b4b53]
              prose-table:text-sm
              prose-th:text-left prose-th:font-semibold
              prose-td:py-1 prose-th:py-1
              prose-code:bg-black/5 prose-code:rounded prose-code:px-1.5 prose-code:py-0.5 prose-code:text-[#1d1d1f] prose-code:before:content-none prose-code:after:content-none
              prose-hr:border-black/6"
            dangerouslySetInnerHTML={{
              __html: markdownToHtml(project.brief_markdown),
            }}
          />
        </div>
      )}

      {/* Tags summary */}
      {project.image_tags && project.image_tags.length > 0 && (
        <div className="bg-white/40 backdrop-blur-xl rounded-3xl p-6 shadow-[0_2px_16px_rgba(0,0,0,0.04)]">
          <h3 className="text-lg font-semibold mb-4 tracking-[-0.02em]">
            Теги изображений
          </h3>
          <TagList tags={project.image_tags as ImageTagSet[]} readOnly />
        </div>
      )}

      {/* Actions */}
      <div className="flex justify-center gap-4 pb-8">
        {project.brief_markdown && (
          <Button
            size="large"
            shape="round"
            icon={<CopyOutlined />}
            className="!h-14 !px-8 !text-[1.1rem] !bg-white/80 !border-transparent hover:!bg-white"
            onClick={handleCopyMarkdown}
          >
            Скопировать Markdown
          </Button>
        )}
        {pdfUrl && (
          <Button
            type="primary"
            size="large"
            shape="round"
            icon={<DownloadOutlined />}
            className="!h-14 !px-10 !text-[1.1rem] !bg-[#1d1d1f] !border-[#1d1d1f] !shadow-[0_8px_24px_rgba(29,29,31,0.2)]"
            href={pdfUrl}
            target="_blank"
          >
            Скачать PDF
          </Button>
        )}
        <Button
          size="large"
          shape="round"
          icon={<HomeOutlined />}
          className="!h-14 !px-10 !text-[1.1rem] !bg-white/50 !border-transparent hover:!bg-white"
          onClick={() => router.push("/dashboard")}
        >
          К дашборду
        </Button>
      </div>
    </div>
  );
}

/* ── Minimal Markdown → HTML ─────────────────────────────────────────── */

function markdownToHtml(md: string): string {
  let html = md
    // Headings
    .replace(/^### (.+)$/gm, "<h3>$1</h3>")
    .replace(/^## (.+)$/gm, "<h2>$1</h2>")
    .replace(/^# (.+)$/gm, "<h1>$1</h1>")
    // Bold
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    // Italic (underscores)
    .replace(/(?<!\w)_(.+?)_(?!\w)/g, "<em>$1</em>")
    // Inline code
    .replace(/`(.+?)`/g, "<code>$1</code>")
    // Horizontal rule
    .replace(/^---+$/gm, "<hr/>")
    // Unordered list items
    .replace(/^- (.+)$/gm, "<li>$1</li>")
    // Table rows (simple)
    .replace(/^\|(.+)\|$/gm, (_, row: string) => {
      if (row.includes("---")) return "";
      const cells = row
        .split("|")
        .map((c: string) => c.trim())
        .filter(Boolean);
      return (
        "<tr>" + cells.map((c: string) => `<td>${c}</td>`).join("") + "</tr>"
      );
    });

  // Wrap consecutive <li> in <ul>
  html = html.replace(/((?:<li>.+<\/li>\n?)+)/g, "<ul>$1</ul>");

  // Wrap consecutive <tr> in <table>
  html = html.replace(
    /((?:<tr>.+<\/tr>\n?)+)/g,
    '<table class="w-full">$1</table>',
  );

  // Paragraphs for remaining lines
  html = html
    .split("\n")
    .map((line) => {
      const trimmed = line.trim();
      if (!trimmed) return "";
      if (
        trimmed.startsWith("<h") ||
        trimmed.startsWith("<ul") ||
        trimmed.startsWith("<li") ||
        trimmed.startsWith("<table") ||
        trimmed.startsWith("<tr") ||
        trimmed.startsWith("<hr") ||
        trimmed.startsWith("<strong") ||
        trimmed.startsWith("<em")
      ) {
        return trimmed;
      }
      return `<p>${trimmed}</p>`;
    })
    .join("\n");

  return html;
}
