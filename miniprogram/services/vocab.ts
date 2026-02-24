import { request } from './request';

export interface VocabItem {
  word: string;
  meaning?: string;
  nextReview?: string;
}

interface VocabListResponse {
  items: VocabItem[];
  total?: number;
}

export function add(item: { word: string }): Promise<any> {
  return request.post('/vocab', item);
}

export function list(params: Record<string, any> = {}): Promise<VocabListResponse> {
  return request.get<VocabListResponse>('/vocab', params);
}

export function remove(word: string): Promise<any> {
  return request.delete(`/vocab/${encodeURIComponent(word)}`);
}

export function review(word: string, rating: string): Promise<any> {
  return request.post('/vocab/review', { word, rating });
}

export function due(params: Record<string, any> = {}): Promise<VocabListResponse> {
  return request.get<VocabListResponse>('/vocab/due', params);
}
