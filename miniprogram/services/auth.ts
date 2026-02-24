import { request } from './request';

interface AuthResponse {
  token?: string;
  user: {
    openid: string;
    [key: string]: any;
  };
}

export function me(code: string): Promise<AuthResponse> {
  return request.post<AuthResponse>('/auth/me', { code }).then((data) => {
    if (data.token) {
      request.setToken(data.token);
    }
    if (data.user?.openid) {
      request.setOpenid(data.user.openid);
    }
    return data;
  });
}
