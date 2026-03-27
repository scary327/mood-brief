import { useAuthStore } from "@/store/authStore";

export const getApiBase = () => {
  const envUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!envUrl) return "http://localhost:8000";
  return envUrl.replace(/\/$/, "");
};

export const API_BASE = getApiBase();

// Flag to prevent infinite refresh loops
let isRefreshing = false;
let refreshSubscribers: ((token: string) => void)[] = [];

function onRefreshed(token: string) {
  refreshSubscribers.forEach((subscriber) => subscriber(token));
  refreshSubscribers = [];
}

/** Wrapper around fetch with auth interceptor */
export async function apiFetch(
  endpoint: string,
  options: RequestInit = {},
): Promise<Response> {
  // Add auth header if token exists
  const token = useAuthStore.getState().accessToken;
  const headers: Record<string, string> = {
    ...(typeof options.headers === "object" && options.headers !== null
      ? Object.fromEntries(
          options.headers instanceof Headers
            ? options.headers.entries()
            : Object.entries(options.headers as Record<string, string>),
        )
      : {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
      credentials: "include", // Send cookies (for refresh token)
    });
    console.log(`[apiFetch] ${endpoint} -> ${response.status}`);
  } catch (e) {
    console.error(`[apiFetch] ${endpoint} NETWORK ERROR:`, e);
    throw new Error(
      `Network error: ${e instanceof Error ? e.message : "Failed to connect to server"}`,
    );
  }

  // If 401, try to refresh token
  if (response.status === 401 && !isRefreshing) {
    isRefreshing = true;
    try {
      const store = useAuthStore.getState();
      const refreshed = await store.refreshToken();
      isRefreshing = false;

      if (refreshed) {
        const newToken = store.accessToken;
        if (newToken) {
          // Retry original request with new token
          headers["Authorization"] = `Bearer ${newToken}`;
          response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers,
            credentials: "include",
          });
          onRefreshed(newToken);
          return response;
        }
      } else {
        // Refresh failed - logout
        store.logout();
        if (typeof window !== "undefined") {
          window.location.href = "/auth/login";
        }
        throw new Error("Session expired. Please login again.");
      }
    } catch (e) {
      isRefreshing = false;
      const store = useAuthStore.getState();
      store.logout();
      if (typeof window !== "undefined") {
        window.location.href = "/auth/login";
      }
      throw e;
    }
  }

  return response;
}

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
  template_id: string;
  created_at: string;
}

export async function analyzeImages(
  files: File[],
  projectName: string,
  description: string,
): Promise<AnalyzeImagesResponse> {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  form.append("project_name", projectName);
  form.append("description", description);

  const res = await apiFetch("/api/analyze-images", {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    let errorMessage = `Analyze failed: ${res.status}`;
    try {
      const err = await res.json();
      errorMessage = err.detail || errorMessage;
    } catch {
      // ignore
    }
    throw new Error(errorMessage);
  }
  return res.json();
}

export async function generateBrief(
  projectId: string,
  confirmedTags: ImageTagSet[],
  templateId: string,
  userNotes: string,
  selectedFonts: string[],
  selectedColors: string[],
): Promise<GenerateBriefResponse> {
  const res = await apiFetch("/api/generate-brief", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      project_id: projectId,
      confirmed_tags: confirmedTags,
      template_id: templateId,
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

export async function getProject(id: string): Promise<ProjectOut> {
  const res = await apiFetch(`/api/projects/${id}`);
  if (!res.ok) throw new Error("Project not found");
  return res.json();
}

export async function getHistory(): Promise<ProjectOut[]> {
  const res = await apiFetch("/api/projects");
  if (!res.ok) throw new Error("Failed to fetch history");
  return res.json();
}

export function getBriefPdfUrl(projectId: string): string {
  return `${API_BASE}/api/brief/${projectId}/pdf`;
}
