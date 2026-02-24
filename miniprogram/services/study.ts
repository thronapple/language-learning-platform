import { request } from './request';

interface SaveProgressPayload {
  contentId: string;
  secs: number;
  step: string;
}

export function saveProgress(payload: SaveProgressPayload): Promise<any> {
  return request.post('/study/progress', payload);
}
