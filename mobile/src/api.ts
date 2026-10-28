import * as SecureStore from "expo-secure-store";

// Set EXPO_PUBLIC_API_URL in mobile/.env, e.g. http://192.168.1.20:5000
// (use your computer's LAN IP, not localhost, when testing on a phone).
export const API_URL = (process.env.EXPO_PUBLIC_API_URL ?? "http://10.0.2.2:5000").replace(/\/$/, "");
const BASE = `${API_URL}/api/v1`;
const TOKEN_KEY = "roomfinder_token";

export type Role = "tenant" | "owner" | "admin";
export type User = { id: number; name: string; email: string; phone?: string | null; role: Role };

export type Property = {
  id: number;
  title: string;
  description?: string | null;
  location: string;
  address?: string | null;
  rent: number;
  room_type: string;
  furnished?: string | null;
  food_available?: string | null;
  gender_preference?: string | null;
  available: boolean;
  owner_name?: string | null;
  owner_email?: string;
  owner_phone?: string;
  image: string | null;
  images?: string[];
};

export type RentalRequest = {
  id: number;
  status: "pending" | "accepted" | "rejected";
  message: string | null;
  created_at: string | null;
  property: Pick<Property, "id" | "title" | "location" | "rent" | "image">;
};

export type OwnerProperty = Property & { image_items: { id: number; url: string }[] };

export type OwnerRequest = {
  id: number;
  status: "pending" | "accepted" | "rejected";
  message: string | null;
  created_at: string | null;
  tenant: { name: string; email: string; phone: string | null };
  property: Pick<Property, "id" | "title" | "location" | "rent" | "image">;
};

export type AdminRequest = {
  id: number;
  status: "pending" | "accepted" | "rejected";
  message: string | null;
  created_at: string | null;
  tenant_name: string;
  owner_name: string;
  property: Pick<Property, "id" | "title" | "location" | "rent">;
};

export type AdminUser = { id: number; name: string; email: string; phone: string | null; role: Role; created_at: string | null };

export type Profile = {
  id: number; name: string; email: string; phone: string | null; role: Role;
  country: string | null; id_status: string | null; id_verified: boolean; member_since: string | null;
};

export type PropertyFilters = {
  location?: string;
  min_rent?: string;
  max_rent?: string;
  room_type?: string;
  furnished?: string;
  limit?: number;
  offset?: number;
};

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
  }
}

let token: string | null = null;
let onUnauthorized: (() => void) | null = null;

export const setUnauthorizedHandler = (fn: () => void) => { onUnauthorized = fn; };
export const loadToken = async () => (token = await SecureStore.getItemAsync(TOKEN_KEY));
export const saveToken = async (t: string) => { token = t; await SecureStore.setItemAsync(TOKEN_KEY, t); };
export const clearToken = async () => { token = null; await SecureStore.deleteItemAsync(TOKEN_KEY); };

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json", ...(init.headers as Record<string, string>) };
  if (token) headers.Authorization = `Bearer ${token}`;

  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, { ...init, headers });
  } catch {
    throw new ApiError("Cannot reach the server. Check your connection.", 0);
  }

  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    if (res.status === 401 && token) onUnauthorized?.();
    throw new ApiError(body.error ?? `Request failed (${res.status})`, res.status);
  }
  return body as T;
}

const json = (method: string, data?: unknown): RequestInit => ({
  method,
  headers: { "Content-Type": "application/json" },
  body: data === undefined ? undefined : JSON.stringify(data),
});

export const api = {
  login: (email: string, password: string) =>
    request<{ token: string; user: User }>("/auth/login", json("POST", { email, password })),

  me: () => request<{ user: User }>("/auth/me"),

  countries: () => request<{ countries: string[] }>("/auth/countries"),

  register: (form: FormData) => request<{ message: string }>("/auth/register", { method: "POST", body: form }),

  properties: (f: PropertyFilters = {}) => {
    const qs = Object.entries(f)
      .filter(([, v]) => v !== undefined && v !== "")
      .map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`)
      .join("&");
    return request<{ properties: Property[] }>(`/properties${qs ? `?${qs}` : ""}`);
  },

  property: (id: number) => request<{ property: Property }>(`/properties/${id}`),

  favorites: () => request<{ properties: Property[] }>("/favorites"),
  addFavorite: (id: number) => request<{ favorite: boolean }>(`/favorites/${id}`, json("PUT")),
  removeFavorite: (id: number) => request<{ favorite: boolean }>(`/favorites/${id}`, json("DELETE")),

  requests: () => request<{ requests: RentalRequest[] }>("/requests"),
  sendRequest: (id: number, message: string) =>
    request<{ message: string }>(`/properties/${id}/request`, json("POST", { message })),

  profile: () => request<{ profile: Profile }>("/profile"),

  // ---- owner ----
  ownerDashboard: () =>
    request<{ property_count: number; available_count: number; pending_count: number }>("/owner/dashboard"),
  ownerProperties: () => request<{ properties: Property[] }>("/owner/properties"),
  ownerProperty: (id: number) => request<{ property: OwnerProperty }>(`/owner/properties/${id}`),
  ownerSaveProperty: (id: number | null, form: FormData) =>
    request<{ property: OwnerProperty; images_saved: number; images_rejected: string[] }>(
      id ? `/owner/properties/${id}` : "/owner/properties", { method: id ? "PUT" : "POST", body: form }),
  ownerDeleteProperty: (id: number) => request<{ deleted: boolean }>(`/owner/properties/${id}`, json("DELETE")),
  ownerRequests: () => request<{ requests: OwnerRequest[] }>("/owner/requests"),
  ownerDecide: (id: number, status: "accepted" | "rejected") =>
    request<{ status: string }>(`/owner/requests/${id}`, json("POST", { status })),

  // ---- admin ----
  adminDashboard: () =>
    request<{ users: number; tenants: number; owners: number; properties: number; requests: number }>("/admin/dashboard"),
  adminUsers: () => request<{ users: AdminUser[] }>("/admin/users"),
  adminDeleteUser: (id: number) => request<{ deleted: boolean }>(`/admin/users/${id}`, json("DELETE")),
  adminProperties: () => request<{ properties: Property[] }>("/admin/properties"),
  adminDeleteProperty: (id: number) => request<{ deleted: boolean }>(`/admin/properties/${id}`, json("DELETE")),
  adminRequests: () => request<{ requests: AdminRequest[] }>("/admin/requests"),
};
