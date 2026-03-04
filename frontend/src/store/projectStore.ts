import { create } from "zustand";
import {
  analyzeImages,
  generateBrief,
  type ImageTagSet,
  type AnalyzeImagesResponse,
  type GenerateBriefResponse,
} from "@/lib/api";

interface ProjectStore {
  /* ── state ── */
  uploadedFiles: File[];
  tags: ImageTagSet[];
  projectId: string | null;
  projectName: string;
  description: string;
  selectedFonts: Set<string>;
  selectedColors: Set<string>;
  isAnalyzing: boolean;
  isGenerating: boolean;
  briefMarkdown: string | null;
  pdfUrl: string | null;
  error: string | null;

  /* ── actions ── */
  setProjectName: (name: string) => void;
  setDescription: (desc: string) => void;
  toggleFont: (font: string) => void;
  toggleColor: (hex: string) => void;
  addColor: (hex: string) => void;
  setUploadedFiles: (files: File[]) => void;
  removeTag: (
    tagIndex: number,
    category: keyof ImageTagSet,
    valueIndex: number,
  ) => void;
  uploadAndAnalyze: () => Promise<AnalyzeImagesResponse | null>;
  doGenerateBrief: (userNotes: string) => Promise<GenerateBriefResponse | null>;
  reset: () => void;
}

const initialState = {
  uploadedFiles: [] as File[],
  tags: [] as ImageTagSet[],
  projectId: null as string | null,
  projectName: "",
  description: "",
  selectedFonts: new Set(["Inter", "Playfair Display"]),
  selectedColors: new Set(["#1d1d1f", "#3b82f6", "#8b5cf6"]),
  isAnalyzing: false,
  isGenerating: false,
  briefMarkdown: null as string | null,
  pdfUrl: null as string | null,
  error: null as string | null,
};

export const useProjectStore = create<ProjectStore>((set, get) => ({
  ...initialState,

  setProjectName: (name) => set({ projectName: name }),
  setDescription: (desc) => set({ description: desc }),

  toggleFont: (font) =>
    set((s) => {
      const next = new Set(s.selectedFonts);
      next.has(font) ? next.delete(font) : next.add(font);
      return { selectedFonts: next };
    }),

  toggleColor: (hex) =>
    set((s) => {
      const next = new Set(s.selectedColors);
      next.has(hex) ? next.delete(hex) : next.add(hex);
      return { selectedColors: next };
    }),

  addColor: (hex) =>
    set((s) => {
      const next = new Set(s.selectedColors);
      next.add(hex);
      return { selectedColors: next };
    }),

  setUploadedFiles: (files) => set({ uploadedFiles: files }),

  removeTag: (tagIndex, category, valueIndex) =>
    set((s) => {
      const next = s.tags.map((t, i) => {
        if (i !== tagIndex) return t;
        const arr = [...(t[category] as string[])];
        arr.splice(valueIndex, 1);
        return { ...t, [category]: arr };
      });
      return { tags: next };
    }),

  uploadAndAnalyze: async () => {
    const {
      uploadedFiles,
      projectName,
      description,
      selectedFonts,
      selectedColors,
    } = get();
    if (uploadedFiles.length === 0) return null;

    set({ isAnalyzing: true, error: null });
    try {
      const result = await analyzeImages(
        uploadedFiles,
        projectName || "Untitled Project",
        description,
        [...selectedFonts],
        [...selectedColors],
      );
      set({
        projectId: result.project_id,
        tags: result.tags,
        isAnalyzing: false,
      });
      return result;
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Analysis failed";
      set({ isAnalyzing: false, error: msg });
      return null;
    }
  },

  doGenerateBrief: async (userNotes) => {
    const { projectId, tags, selectedFonts, selectedColors } = get();
    if (!projectId) return null;

    set({ isGenerating: true, error: null });
    try {
      const result = await generateBrief(
        projectId,
        tags,
        userNotes,
        [...selectedFonts],
        [...selectedColors],
      );
      set({
        briefMarkdown: result.brief_markdown,
        pdfUrl: result.pdf_url,
        isGenerating: false,
      });
      return result;
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Brief generation failed";
      set({ isGenerating: false, error: msg });
      return null;
    }
  },

  reset: () => set(initialState),
}));
