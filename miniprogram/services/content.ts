import { request } from './request';

export interface ContentItem {
  id: string;
  type: string;
  text: string;
  audio_url?: string;
  segments?: string[];
  segments_audio?: string[];
  level?: string;
  tags?: string[];
}

interface ContentListResponse {
  items: ContentItem[];
  total: number;
}

export function list(params: Record<string, any> = {}): Promise<ContentListResponse> {
  return request.get<ContentListResponse>('/content', params);
}

export function get(id: string): Promise<ContentItem> {
  return request.get<ContentItem>(`/content/${id}`);
}
