"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  Button,
  Input,
  Spin,
  Alert,
  message,
  Tooltip,
  Breadcrumb,
} from "antd";
import {
  ArrowLeftOutlined,
  DownloadOutlined,
  SaveOutlined,
  SendOutlined,
  ReloadOutlined,
  EyeOutlined,
  EditOutlined,
  RobotOutlined,
} from "@ant-design/icons";
import { getProject, getBriefPdfUrl, type ProjectOut } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const TEMPLATE_LABELS: Record<string, string> = {
  gost: "ГОСТ 34.602-2020",
  standard: "Стандартное ТЗ",
  creative: "Креативный бриф",
};

type Mode = "split" | "preview" | "edit";

export default function EditorPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [project, setProject] = useState<ProjectOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [markdown, setMarkdown] = useState("");
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);

  const [aiInstruction, setAiInstruction] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);
  const [justUpdated, setJustUpdated] = useState(false);

  const [mode, setMode] = useState<Mode>("split");

  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    if (!id) return;
    getProject(id)
      .then((p) => {
        setProject(p);
        setMarkdown(p.brief_markdown || "");
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  const handleMarkdownChange = (val: string) => {
    setMarkdown(val);
    setDirty(true);
  };

  const handleSave = useCallback(async () => {
    if (!project) return;
    setSaving(true);
    try {
      const res = await fetch(`${API_BASE}/api/projects/${id}/markdown`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ markdown }),
      });
      if (!res.ok) throw new Error("Ошибка сохранения");
      setDirty(false);
      message.success("ТЗ сохранено и PDF обновлён");
    } catch (e: unknown) {
      message.error(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setSaving(false);
    }
  }, [id, markdown, project]);

  // Ctrl+S shortcut
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "s") {
        e.preventDefault();
        if (dirty) handleSave();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [dirty, handleSave]);

  const handleAiRefine = async () => {
    if (!aiInstruction.trim()) {
      message.warning("Введите инструкцию для AI");
      return;
    }
    setAiLoading(true);
    setAiError(null);
    try {
      const res = await fetch(`${API_BASE}/api/refine-brief`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_id: id,
          instruction: aiInstruction,
          current_markdown: markdown, // send live editor state
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `Ошибка ${res.status}`);
      setMarkdown(data.brief_markdown);
      setDirty(true); // mark dirty so user saves to DB
      setAiInstruction("");
      setJustUpdated(true);
      setTimeout(() => setJustUpdated(false), 1800);
      message.success("ТЗ обновлено AI — не забудьте сохранить!");
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Неизвестная ошибка";
      setAiError(msg);
    } finally {
      setAiLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "100vh", gap: "1rem" }}>
        <Spin size="large" />
        <span style={{ color: "#4b4b53" }}>Загрузка редактора…</span>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "100vh", gap: "1rem" }}>
        <Alert type="error" message="Ошибка" description={error || "Проект не найден"} showIcon />
        <Button onClick={() => router.push("/dashboard")}>На дашборд</Button>
      </div>
    );
  }

  const pdfUrl = getBriefPdfUrl(id);
  const templateLabel = TEMPLATE_LABELS[project.template_id] || project.template_id;

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        overflow: "hidden",
        background: "linear-gradient(135deg, #f5f5f7 0%, #e8e8ed 100%)",
        fontFamily: "'Inter', system-ui, sans-serif",
      }}
    >
      {/* ── Top toolbar ── */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.75rem",
          padding: "0.6rem 1.25rem",
          background: "rgba(255,255,255,0.85)",
          backdropFilter: "blur(20px)",
          borderBottom: "1px solid rgba(0,0,0,0.08)",
          flexShrink: 0,
          flexWrap: "wrap",
        }}
      >
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          onClick={() => router.back()}
          style={{ color: "#4b4b53" }}
        />

        <Breadcrumb
          style={{ flex: 1, fontSize: "0.85rem" }}
          items={[
            { title: <span style={{ cursor: "pointer" }} onClick={() => router.push("/dashboard")}>Дашборд</span> },
            { title: <span style={{ cursor: "pointer" }} onClick={() => router.push(`/brief/${id}`)}>{project.name}</span> },
            { title: "Редактор" },
          ]}
        />

        <span style={{ fontSize: "0.8rem", color: "#7d7d85", marginLeft: "auto" }}>
          {templateLabel}
        </span>

        {/* View mode toggle */}
        <div
          style={{
            display: "flex",
            background: "rgba(0,0,0,0.06)",
            borderRadius: "0.5rem",
            padding: "0.2rem",
            gap: "0.15rem",
          }}
        >
          {(["split", "edit", "preview"] as Mode[]).map((m) => (
            <Tooltip key={m} title={m === "split" ? "Разделить" : m === "edit" ? "Редактор" : "Просмотр"}>
              <button
                onClick={() => setMode(m)}
                style={{
                  padding: "0.3rem 0.6rem",
                  borderRadius: "0.35rem",
                  border: "none",
                  cursor: "pointer",
                  fontSize: "0.75rem",
                  background: mode === m ? "#fff" : "transparent",
                  color: mode === m ? "#1d1d1f" : "#7d7d85",
                  boxShadow: mode === m ? "0 1px 4px rgba(0,0,0,0.12)" : "none",
                  transition: "all 0.15s",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.25rem",
                }}
              >
                {m === "split" ? <><EditOutlined /><EyeOutlined /></> : m === "edit" ? <EditOutlined /> : <EyeOutlined />}
              </button>
            </Tooltip>
          ))}
        </div>

        <Tooltip title={dirty ? "Сохранить (Ctrl+S)" : "Сохранено"}>
          <Button
            type="primary"
            icon={<SaveOutlined />}
            loading={saving}
            disabled={!dirty}
            onClick={handleSave}
            style={{
              background: dirty ? "#1d1d1f" : "#e8e8ed",
              borderColor: dirty ? "#1d1d1f" : "#e8e8ed",
              color: dirty ? "#fff" : "#7d7d85",
              transition: "all 0.2s",
            }}
          >
            {dirty ? "Сохранить" : "Сохранено"}
          </Button>
        </Tooltip>

        {pdfUrl && (
          <Button icon={<DownloadOutlined />} href={pdfUrl} target="_blank" style={{ borderColor: "#1d1d1f" }}>
            PDF
          </Button>
        )}
      </div>

      {/* ── Main area ── */}
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        {/* Left: Editor */}
        {(mode === "edit" || mode === "split") && (
          <div
            style={{
              flex: 1,
              display: "flex",
              flexDirection: "column",
              borderRight: mode === "split" ? "1px solid rgba(0,0,0,0.08)" : "none",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                padding: "0.4rem 1rem",
                background: "rgba(255,255,255,0.6)",
                fontSize: "0.75rem",
                color: "#7d7d85",
                letterSpacing: "0.04em",
                fontWeight: 600,
                borderBottom: "1px solid rgba(0,0,0,0.06)",
                flexShrink: 0,
              }}
            >
              MARKDOWN-РЕДАКТОР
            </div>
            <textarea
              ref={textareaRef}
              value={markdown}
              onChange={(e) => handleMarkdownChange(e.target.value)}
              style={{
                flex: 1,
                width: "100%",
                padding: "1.25rem",
                border: "none",
                outline: "none",
                resize: "none",
                fontFamily: "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
                fontSize: "0.85rem",
                lineHeight: 1.7,
                background: "rgba(255,255,255,0.3)",
                color: "#1d1d1f",
                overflow: "auto",
              }}
              spellCheck={false}
              placeholder="Markdown-текст вашего ТЗ…"
            />
          </div>
        )}

        {/* Right: Preview */}
        {(mode === "preview" || mode === "split") && (
          <div
            style={{
              flex: 1,
              display: "flex",
              flexDirection: "column",
              overflow: "hidden",
              transition: "background 0.4s",
              background: justUpdated ? "#f0fdf4" : undefined,
            }}
          >
            <div
              style={{
                padding: "0.4rem 1rem",
                background: "rgba(255,255,255,0.6)",
                fontSize: "0.75rem",
                color: "#7d7d85",
                letterSpacing: "0.04em",
                fontWeight: 600,
                borderBottom: "1px solid rgba(0,0,0,0.06)",
                flexShrink: 0,
              }}
            >
              ПРЕДПРОСМОТР
            </div>
            <div
              style={{
                flex: 1,
                overflow: "auto",
                padding: "1.5rem 2rem",
                background: "#fff",
              }}
            >
              <div
                className="prose prose-sm max-w-none
                  prose-headings:text-[#1d1d1f] prose-headings:tracking-tight
                  prose-p:text-[#4b4b53] prose-p:leading-relaxed
                  prose-li:text-[#4b4b53]
                  prose-table:text-xs prose-th:font-semibold
                  prose-code:bg-black/5 prose-code:rounded prose-code:px-1"
                dangerouslySetInnerHTML={{ __html: markdownToHtml(markdown) }}
              />
            </div>
          </div>
        )}
      </div>

      {/* ── AI Refinement panel ── */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "0.5rem",
          padding: "0.75rem 1.25rem",
          background: "rgba(255,255,255,0.9)",
          backdropFilter: "blur(20px)",
          borderTop: "1px solid rgba(0,0,0,0.08)",
          flexShrink: 0,
        }}
      >
        {aiError && (
          <Alert
            type="error"
            message={aiError}
            closable
            onClose={() => setAiError(null)}
            style={{ borderRadius: "0.5rem", fontSize: "0.85rem" }}
          />
        )}
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <RobotOutlined style={{ fontSize: "1.1rem", color: "#7d7d85", flexShrink: 0 }} />
          <Input.TextArea
            value={aiInstruction}
            onChange={(e) => setAiInstruction(e.target.value)}
            placeholder='Инструкция: "Добавь раздел 5 подробнее", "Смени тон на более формальный"...'
            onPressEnter={(e) => {
              if (!e.shiftKey) {
                e.preventDefault();
                handleAiRefine();
              }
            }}
            autoSize={{ minRows: 1, maxRows: 6 }}
            style={{
              flex: 1,
              borderRadius: "0.75rem",
              paddingTop: "0.5rem",
              paddingBottom: "0.5rem",
              fontSize: "0.9rem",
            }}
            disabled={aiLoading}
          />
          <Tooltip title="Применить к ТЗ через AI">
            <Button
              type="primary"
              icon={aiLoading ? <ReloadOutlined spin /> : <SendOutlined />}
              loading={aiLoading}
              onClick={handleAiRefine}
              style={{
                background: "#1d1d1f",
                borderColor: "#1d1d1f",
                height: "2.5rem",
                padding: "0 1.25rem",
                borderRadius: "0.75rem",
              }}
            >
              {aiLoading ? "Обрабатываю…" : "Применить"}
            </Button>
          </Tooltip>
        </div>
      </div>
    </div>
  );
}

// ── Markdown → HTML (same as brief page) ──────────────────────────────────

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
      return "<tr>" + cells.map((c: string) => `<td style="padding:4px 8px;border:1px solid #e5e7eb">${c}</td>`).join("") + "</tr>";
    });

  html = html.replace(/((?:<li>.+<\/li>\n?)+)/g, "<ul>$1</ul>");
  html = html.replace(
    /((?:<tr>.+<\/tr>\n?)+)/g,
    '<table style="width:100%;border-collapse:collapse;margin-bottom:1rem">$1</table>',
  );

  html = html
    .split("\n")
    .map((line) => {
      const t = line.trim();
      if (!t) return "";
      if (/^<(h[1-4]|ul|li|table|tr|hr|strong|em)/.test(t)) return t;
      return `<p style="margin-bottom:0.5rem">${t}</p>`;
    })
    .join("\n");

  return html;
}
