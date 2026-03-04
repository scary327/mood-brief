"use client";

import { Tag } from "antd";
import {
  BgColorsOutlined,
  FormatPainterOutlined,
  FontSizeOutlined,
  LayoutOutlined,
  SmileOutlined,
  AppstoreOutlined,
} from "@ant-design/icons";
import type { ImageTagSet } from "@/lib/api";

const CATEGORIES: {
  key: keyof ImageTagSet;
  label: string;
  icon: React.ReactNode;
  color: string;
}[] = [
  {
    key: "style",
    label: "Стиль",
    icon: <FormatPainterOutlined />,
    color: "purple",
  },
  {
    key: "color_palette",
    label: "Палитра",
    icon: <BgColorsOutlined />,
    color: "magenta",
  },
  {
    key: "typography",
    label: "Типографика",
    icon: <FontSizeOutlined />,
    color: "blue",
  },
  {
    key: "composition",
    label: "Композиция",
    icon: <LayoutOutlined />,
    color: "cyan",
  },
  {
    key: "ui_elements",
    label: "UI/UX",
    icon: <AppstoreOutlined />,
    color: "orange",
  },
  {
    key: "visual_hooks",
    label: "Детали / Эффекты",
    icon: <SmileOutlined />,
    color: "green",
  },
];

interface TagListProps {
  tags: ImageTagSet[];
  onRemove?: (
    tagIndex: number,
    category: keyof ImageTagSet,
    valueIndex: number,
  ) => void;
  readOnly?: boolean;
}

export default function TagList({
  tags,
  onRemove,
  readOnly = false,
}: TagListProps) {
  if (!tags.length) return null;

  // Merge all tags across images, keeping track of source
  const merged: Record<
    string,
    { values: { value: string; tagIdx: number; valIdx: number }[] }
  > = {};
  for (const cat of CATEGORIES) {
    merged[cat.key] = { values: [] };
    tags.forEach((t, tagIdx) => {
      const arr = t[cat.key] as string[];
      arr.forEach((value, valIdx) => {
        // Avoid duplicates in display
        if (!merged[cat.key].values.some((v) => v.value === value)) {
          merged[cat.key].values.push({ value, tagIdx, valIdx });
        }
      });
    });
  }

  return (
    <div className="flex flex-col gap-4">
      {CATEGORIES.map((cat) => {
        const items = merged[cat.key]?.values || [];
        if (!items.length) return null;

        return (
          <div key={cat.key}>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-base text-[#4b4b53]">{cat.icon}</span>
              <span className="text-sm font-semibold text-[#4b4b53]">
                {cat.label}
              </span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {items.map((item, i) => {
                const hexMatch = item.value.match(/#[0-9a-fA-F]{3,6}/);
                const hex =
                  cat.key === "color_palette" && hexMatch ? hexMatch[0] : null;

                return (
                  <Tag
                    key={`${cat.key}-${i}`}
                    color={hex ? undefined : cat.color}
                    closable={!readOnly}
                    onClose={() =>
                      onRemove?.(item.tagIdx, cat.key, item.valIdx)
                    }
                    className="!rounded-lg !px-3 !py-0.5 !text-sm !m-0"
                    style={
                      hex
                        ? {
                            backgroundColor: hex,
                            color: isLightColor(hex) ? "#1d1d1f" : "#ffffff",
                            border: "1px solid rgba(0,0,0,0.08)",
                          }
                        : undefined
                    }
                  >
                    {item.value}
                  </Tag>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function isLightColor(hex: string): boolean {
  const c = hex.replace("#", "");
  const r = parseInt(c.substring(0, 2), 16);
  const g = parseInt(c.substring(2, 4), 16);
  const b = parseInt(c.substring(4, 6), 16);
  return (r * 299 + g * 587 + b * 114) / 1000 > 128;
}
