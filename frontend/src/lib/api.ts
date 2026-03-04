const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/* ── Types ─────────────────────────────────────────────────────────────── */

export interface ImageTagSet {
  style: string[];
  color_palette: string[];
  typography: string[];
  composition: string[];
  ui_elements: string[];
  visual_hooks: string[];
  filename: string;
}

export interface AnalyzeImagesResponse {
  project_id: string;
  tags: ImageTagSet[];
}

export interface GenerateBriefResponse {
  project_id: string;
  brief_markdown: string;
  pdf_url: string;
}

export interface ProjectOut {
  id: string;
  name: string;
  description: string;
  selected_fonts: string[];
  selected_colors: string[];
  image_tags: ImageTagSet[];
  brief_markdown: string;
  pdf_filename: string;
  status: string;
  created_at: string;
}

/* ── API functions ─────────────────────────────────────────────────────── */

export async function analyzeImages(
  files: File[],
  projectName: string,
  description: string,
  selectedFonts: string[],
  selectedColors: string[],
): Promise<AnalyzeImagesResponse> {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  form.append("project_name", projectName);
  form.append("description", description);
  form.append("selected_fonts", JSON.stringify(selectedFonts));
  form.append("selected_colors", JSON.stringify(selectedColors));

  const res = await fetch(`${API_BASE}/api/analyze-images`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Analyze failed: ${res.status}`);
  }
  return res.json();
}

export async function generateBrief(
  projectId: string,
  confirmedTags: ImageTagSet[],
  userNotes: string,
  selectedFonts: string[],
  selectedColors: string[],
): Promise<GenerateBriefResponse> {
  const res = await fetch(`${API_BASE}/api/generate-brief`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      project_id: projectId,
      confirmed_tags: confirmedTags,
      user_notes: userNotes,
      selected_fonts: selectedFonts,
      selected_colors: selectedColors,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Generate failed: ${res.status}`);
  }
  return res.json();
}

export async function getHistory(): Promise<ProjectOut[]> {
  const res = await fetch(`${API_BASE}/api/history`);
  if (!res.ok) throw new Error(`History fetch failed: ${res.status}`);
  return res.json();
}

export async function getProject(id: string): Promise<ProjectOut> {
  const res = await fetch(`${API_BASE}/api/history/${id}`);
  if (!res.ok) throw new Error(`Project fetch failed: ${res.status}`);
  return res.json();
}

export function getBriefPdfUrl(projectId: string): string {
  return `${API_BASE}/api/brief/${projectId}/pdf`;
}
