"use client";

import { useState } from "react";
import { Button, Input, Popover, Tooltip } from "antd";
import {
  PlusOutlined,
  LinkOutlined,
  UploadOutlined,
  CheckOutlined,
  FontSizeOutlined,
  BgColorsOutlined,
  PictureOutlined,
  FileTextOutlined,
  ArrowRightOutlined,
} from "@ant-design/icons";

const { TextArea } = Input;

/* ───────── mock data ───────── */
const MOCK_REFERENCES = Array.from({ length: 6 }, (_, i) => ({
  id: `ref-${i}`,
  selected: i < 3,
}));

const MOCK_FONTS = [
  { name: "Inter", style: "font-sans", category: "Sans-serif" },
  { name: "Playfair Display", style: "font-serif", category: "Serif" },
  { name: "Space Grotesk", style: "font-mono", category: "Sans-serif" },
  { name: "DM Sans", style: "font-sans", category: "Sans-serif" },
  { name: "Lora", style: "font-serif", category: "Serif" },
  { name: "JetBrains Mono", style: "font-mono", category: "Monospace" },
];

const MOCK_COLORS = [
  "#1d1d1f",
  "#3b82f6",
  "#8b5cf6",
  "#ec4899",
  "#f97316",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#06b6d4",
  "#84cc16",
];

/* ───────── section header ───────── */
function SectionHeader({
  icon,
  title,
  subtitle,
}: {
  icon: React.ReactNode;
  title: string;
  subtitle: string;
}) {
  return (
    <div className="mb-5">
      <div className="flex items-center gap-3 mb-1">
        <span className="text-xl text-[#4b4b53]">{icon}</span>
        <h3 className="text-lg font-semibold m-0 tracking-[-0.02em]">
          {title}
        </h3>
      </div>
      <p className="text-sm text-[#4b4b53]/70 m-0 ml-[35px]">{subtitle}</p>
    </div>
  );
}

/* ───────── main form ───────── */
export default function MoodBoardForm() {
  const [selectedRefs, setSelectedRefs] = useState<Set<string>>(
    new Set(MOCK_REFERENCES.filter((r) => r.selected).map((r) => r.id)),
  );
  const [selectedFonts, setSelectedFonts] = useState<Set<string>>(
    new Set(["Inter", "Playfair Display"]),
  );
  const [selectedColors, setSelectedColors] = useState<Set<string>>(
    new Set(["#1d1d1f", "#3b82f6", "#8b5cf6"]),
  );
  const [customColors, setCustomColors] = useState<string[]>([]);
  const [pickerColor, setPickerColor] = useState("#6366f1");
  const [pickerOpen, setPickerOpen] = useState(false);
  const [pinterestLink, setPinterestLink] = useState("");
  const [projectName, setProjectName] = useState("");
  const [description, setDescription] = useState("");

  const addCustomColor = () => {
    setCustomColors((prev) =>
      prev.includes(pickerColor) ? prev : [...prev, pickerColor],
    );
    setPickerOpen(false);
  };

  const toggleRef = (id: string) =>
    setSelectedRefs((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });

  const toggleFont = (name: string) =>
    setSelectedFonts((prev) => {
      const next = new Set(prev);
      next.has(name) ? next.delete(name) : next.add(name);
      return next;
    });

  const toggleColor = (hex: string) =>
    setSelectedColors((prev) => {
      const next = new Set(prev);
      next.has(hex) ? next.delete(hex) : next.add(hex);
      return next;
    });

  return (
    <div className="container !gap-8">
      {/* Title */}
      <div className="text-center">
        <h1 className="text-[2.5rem] font-extrabold bg-gradient-to-r from-[#1d1d1f] to-[#7d7d85] bg-clip-text text-transparent tracking-[-0.04em] leading-tight mb-2">
          Новый мудборд
        </h1>
        <p className="text-[1.1rem] text-[#4b4b53] max-w-[600px] mx-auto">
          Соберите визуальные предпочтения для генерации ТЗ
        </p>
      </div>

      {/* Project name */}
      <div className="bg-white/40 backdrop-blur-xl rounded-3xl p-6 shadow-[0_2px_16px_rgba(0,0,0,0.04)]">
        <SectionHeader
          icon={<FileTextOutlined />}
          title="Название проекта"
          subtitle="Укажите рабочее название"
        />
        <Input
          size="large"
          placeholder="Например: Редизайн корпоративного сайта"
          value={projectName}
          onChange={(e) => setProjectName(e.target.value)}
          className="!rounded-xl !bg-white/60 !border-black/6 !h-12 !text-base"
        />
      </div>

      {/* ── References / images ── */}
      <div className="bg-white/40 backdrop-blur-xl rounded-3xl p-6 shadow-[0_2px_16px_rgba(0,0,0,0.04)]">
        <SectionHeader
          icon={<PictureOutlined />}
          title="Референсы"
          subtitle="Выберите подходящие изображения, загрузите свои или вставьте ссылки"
        />

        {/* Image grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-5">
          {MOCK_REFERENCES.map((ref) => {
            const active = selectedRefs.has(ref.id);
            return (
              <button
                key={ref.id}
                type="button"
                onClick={() => toggleRef(ref.id)}
                className={`
                  relative aspect-[4/3] rounded-2xl transition-all duration-200 cursor-pointer border-2 overflow-hidden group
                  ${
                    active
                      ? "border-[#1d1d1f] shadow-[0_0_0_2px_rgba(29,29,31,0.15)]"
                      : "border-transparent hover:border-black/10"
                  }
                `}
              >
                {/* Grey placeholder */}
                <div
                  className={`
                    w-full h-full transition-colors duration-200
                    ${active ? "bg-[#d4d4d8]" : "bg-[#e4e4e7] group-hover:bg-[#d4d4d8]"}
                  `}
                />
                {/* Check badge */}
                {active && (
                  <div className="absolute top-2.5 right-2.5 w-7 h-7 rounded-full bg-[#1d1d1f] flex items-center justify-center shadow-lg">
                    <CheckOutlined className="text-white text-xs" />
                  </div>
                )}
              </button>
            );
          })}
        </div>

        {/* Actions row */}
        <div className="flex flex-wrap gap-2">
          <Button
            icon={<UploadOutlined />}
            shape="round"
            className="!bg-white/60 !border-black/6"
          >
            Загрузить изображения
          </Button>
          <div className="flex gap-2 flex-1 min-w-[250px]">
            <Input
              prefix={<LinkOutlined className="text-[#4b4b53]/50" />}
              placeholder="Ссылка на доску Pinterest"
              value={pinterestLink}
              onChange={(e) => setPinterestLink(e.target.value)}
              className="!rounded-full !bg-white/60 !border-black/6 !flex-1"
            />
            <Button
              shape="round"
              type="primary"
              className="!bg-[#1d1d1f] !border-[#1d1d1f]"
              disabled={!pinterestLink}
            >
              Добавить
            </Button>
          </div>
        </div>
      </div>

      {/* ── Fonts ── */}
      <div className="bg-white/40 backdrop-blur-xl rounded-3xl p-6 shadow-[0_2px_16px_rgba(0,0,0,0.04)]">
        <SectionHeader
          icon={<FontSizeOutlined />}
          title="Шрифты"
          subtitle="Выберите шрифты, отражающие стиль проекта"
        />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {MOCK_FONTS.map((font) => {
            const active = selectedFonts.has(font.name);
            return (
              <button
                key={font.name}
                type="button"
                onClick={() => toggleFont(font.name)}
                className={`
                  flex flex-col items-start p-4 rounded-2xl transition-all duration-200 cursor-pointer border-2 text-left
                  ${
                    active
                      ? "border-[#1d1d1f] bg-[#1d1d1f]/[0.03] shadow-[0_0_0_2px_rgba(29,29,31,0.1)]"
                      : "border-transparent bg-white/50 hover:bg-white/80 hover:border-black/6"
                  }
                `}
              >
                <div className="flex items-center justify-between w-full mb-2">
                  <span className="text-base font-semibold">{font.name}</span>
                  {active && (
                    <div className="w-5 h-5 rounded-full bg-[#1d1d1f] flex items-center justify-center">
                      <CheckOutlined className="text-white text-[10px]" />
                    </div>
                  )}
                </div>
                <span className={`text-2xl leading-tight mb-1.5 ${font.style}`}>
                  Aa Бб Вв
                </span>
                <span className="text-xs text-[#4b4b53]/60">
                  {font.category}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* ── Colors ── */}
      <div className="bg-white/40 backdrop-blur-xl rounded-3xl p-6 shadow-[0_2px_16px_rgba(0,0,0,0.04)]">
        <SectionHeader
          icon={<BgColorsOutlined />}
          title="Цветовая палитра"
          subtitle="Выберите основные цвета проекта"
        />

        {/* Color grid */}
        <div className="flex flex-wrap gap-3 mb-5">
          {[...MOCK_COLORS, ...customColors].map((hex) => {
            const active = selectedColors.has(hex);
            return (
              <Tooltip key={hex} title={hex}>
                <button
                  type="button"
                  onClick={() => toggleColor(hex)}
                  className={`
                    w-12 h-12 rounded-xl transition-all duration-200 cursor-pointer border-2 relative
                    ${
                      active
                        ? "border-[#1d1d1f] scale-110 shadow-[0_0_0_2px_rgba(29,29,31,0.15)]"
                        : "border-transparent hover:scale-105"
                    }
                  `}
                  style={{ backgroundColor: hex }}
                >
                  {active && (
                    <CheckOutlined className="text-white text-sm drop-shadow-[0_1px_2px_rgba(0,0,0,0.4)]" />
                  )}
                </button>
              </Tooltip>
            );
          })}
          {/* Add custom color */}
          <Popover
            open={pickerOpen}
            onOpenChange={setPickerOpen}
            trigger="click"
            placement="bottom"
            content={
              <div className="flex flex-col items-center gap-3 p-1">
                <input
                  type="color"
                  value={pickerColor}
                  onChange={(e) => setPickerColor(e.target.value)}
                  className="w-full h-32 rounded-xl border-none cursor-pointer"
                />
                <div className="flex items-center gap-2 w-full">
                  <span className="text-xs text-[#4b4b53]/60 font-mono">
                    {pickerColor}
                  </span>
                  <Button
                    type="primary"
                    size="small"
                    shape="round"
                    className="!bg-[#1d1d1f] !border-[#1d1d1f] ml-auto"
                    onClick={addCustomColor}
                  >
                    Добавить
                  </Button>
                </div>
              </div>
            }
          >
            <button
              type="button"
              className="w-12 h-12 rounded-xl border-2 border-dashed border-black/10 flex items-center justify-center cursor-pointer bg-white/40 hover:border-black/20 transition-all duration-200 hover:scale-105"
            >
              <PlusOutlined className="text-[#4b4b53]/50" />
            </button>
          </Popover>
        </div>

        {/* Selected palette preview */}
        {selectedColors.size > 0 && (
          <div>
            <p className="text-xs text-[#4b4b53]/60 mb-2 font-medium uppercase tracking-wider">
              Ваша палитра
            </p>
            <div className="flex rounded-2xl overflow-hidden h-10 shadow-sm">
              {[...selectedColors].map((hex) => (
                <div
                  key={hex}
                  className="flex-1 transition-all duration-300"
                  style={{ backgroundColor: hex }}
                />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ── Description ── */}
      <div className="bg-white/40 backdrop-blur-xl rounded-3xl p-6 shadow-[0_2px_16px_rgba(0,0,0,0.04)]">
        <SectionHeader
          icon={<FileTextOutlined />}
          title="Описание проекта"
          subtitle="Опишите дополнительные пожелания, ограничения и контекст"
        />
        <TextArea
          rows={5}
          placeholder="Расскажите подробнее о проекте: целевая аудитория, настроение, особые требования..."
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="!rounded-xl !bg-white/60 !border-black/6 !text-base !resize-none"
        />
      </div>

      {/* ── Submit ── */}
      <div className="text-center pb-4">
        <Button
          type="primary"
          size="large"
          shape="round"
          icon={<ArrowRightOutlined />}
          className="!h-14 !px-12 !text-[1.1rem] !bg-[#1d1d1f] !border-[#1d1d1f] !shadow-[0_8px_24px_rgba(29,29,31,0.2)]"
        >
          Сгенерировать ТЗ
        </Button>
      </div>
    </div>
  );
}
