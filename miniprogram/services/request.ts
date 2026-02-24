// miniprogram/services/request.ts

// Environment-based API URL configuration
const CLOUD_URL = 'https://lang-learning-225978-7-1404758981.sh.run.tcloudbase.com';

const ENV_URLS: Record<string, string> = {
  develop: CLOUD_URL,
  trial: CLOUD_URL,
  release: CLOUD_URL,
};

function getBaseUrl(): string {
  try {
    const info = wx.getAccountInfoSync();
    const env = info.miniProgram.envVersion || 'release';
    console.log('[Request] envVersion:', env, '-> BASE_URL:', ENV_URLS[env] || ENV_URLS.release);
    return ENV_URLS[env] || ENV_URLS.release;
  } catch (e) {
    console.warn('[Request] getAccountInfoSync failed, using release URL', e);
    return ENV_URLS.release;
  }
}

const BASE_URL = getBaseUrl();

interface RequestConfig {
  url: string;
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  data?: any;
  header?: any;
}

interface RequestResponse<T = any> {
  data: T;
  statusCode: number;
  header: any;
}

// 可缓存的 GET 路径（支持离线访问）
const CACHEABLE_PATHS = [
  '/vocab',
  '/vocab/due',
  '/plan/stats',
  '/content',
  '/api/scenarios',
];

function cacheKey(url: string): string {
  return 'cache_' + url.replace(/[^a-zA-Z0-9]/g, '_').slice(0, 100);
}

class RequestService {
  private timeout: number;
  private maxRetries: number;
  private refreshing: Promise<boolean> | null = null;

  constructor() {
    this.timeout = 30000;
    this.maxRetries = 2;
  }

  getBaseUrl(): string {
    return BASE_URL;
  }

  /**
   * 核心请求方法（含自动重试）
   */
  private async request<T = any>(config: RequestConfig, retryCount = 0): Promise<T> {
    const { url, method = 'GET', data, header = {} } = config;

    const token = this.getToken();
    if (token) {
      header['Authorization'] = `Bearer ${token}`;
    }
    const openid = this.getOpenid();
    if (openid) {
      header['x-openid'] = openid;
    }
    header['Content-Type'] = 'application/json';

    const fullUrl = `${BASE_URL}${url}`;

    return new Promise((resolve, reject) => {
      wx.request({
        url: fullUrl,
        method,
        data,
        header,
        timeout: this.timeout,

        success: (res: RequestResponse) => {
          if (res.statusCode >= 200 && res.statusCode < 300) {
            // 缓存成功的 GET 响应
            if (method === 'GET') {
              this.setCache(url, res.data);
            }
            resolve(res.data as T);
          } else if (res.statusCode === 401) {
            // Try token refresh before giving up
            this.tryRefreshToken().then((refreshed) => {
              if (refreshed && retryCount === 0) {
                // Retry the original request with new token
                this.request<T>(config, retryCount + 1).then(resolve).catch(reject);
              } else {
                this.handleUnauthorized();
                reject(new Error('未授权，请重新登录'));
              }
            });
          } else if (res.statusCode >= 500 && retryCount < this.maxRetries) {
            // 5xx 自动重试
            console.warn(`[Request] ${method} ${fullUrl} -> ${res.statusCode}, retry ${retryCount + 1}/${this.maxRetries}`);
            setTimeout(() => {
              this.request<T>(config, retryCount + 1).then(resolve).catch(reject);
            }, 1000 * (retryCount + 1));
          } else {
            const errorMessage = (res.data as any)?.message || (res.data as any)?.detail || '请求失败';
            console.error(`[Request] ${method} ${fullUrl} -> ${res.statusCode}`, res.data);
            reject(new Error(errorMessage));
          }
        },

        fail: (error) => {
          console.error(`[Request] ${method} ${fullUrl} FAIL:`, error.errMsg);

          // 网络错误时自动重试
          if (retryCount < this.maxRetries) {
            console.warn(`[Request] Network fail, retry ${retryCount + 1}/${this.maxRetries}`);
            setTimeout(() => {
              this.request<T>(config, retryCount + 1).then(resolve).catch(reject);
            }, 1000 * (retryCount + 1));
            return;
          }

          // 重试用尽，尝试返回缓存（仅 GET）
          if (method === 'GET') {
            const cached = this.getCache(url);
            if (cached !== null) {
              console.log(`[Request] Returning cached data for ${url}`);
              resolve(cached as T);
              return;
            }
          }

          if (error.errMsg?.includes('timeout')) {
            reject(new Error('请求超时，请检查网络'));
          } else if (error.errMsg?.includes('url not in domain list')) {
            reject(new Error(`域名未配置: ${BASE_URL}，请在开发者工具中勾选"不校验合法域名"`));
          } else {
            reject(new Error(`网络错误，请检查网络连接`));
          }
        }
      });
    });
  }

  async get<T = any>(url: string, params?: any): Promise<T> {
    let queryString = '';
    if (params) {
      queryString = '?' + Object.entries(params)
        .map(([key, value]) => `${key}=${encodeURIComponent(String(value))}`)
        .join('&');
    }
    return this.request<T>({ url: url + queryString, method: 'GET' });
  }

  async post<T = any>(url: string, data?: any): Promise<T> {
    return this.request<T>({ url, method: 'POST', data });
  }

  async put<T = any>(url: string, data?: any): Promise<T> {
    return this.request<T>({ url, method: 'PUT', data });
  }

  async delete<T = any>(url: string): Promise<T> {
    return this.request<T>({ url, method: 'DELETE' });
  }

  // --- Token management ---

  private getToken(): string | null {
    try {
      return wx.getStorageSync('auth_token') || null;
    } catch (error) {
      return null;
    }
  }

  setToken(token: string): void {
    try {
      wx.setStorageSync('auth_token', token);
    } catch (error) {
      console.error('保存token失败:', error);
    }
  }

  private getOpenid(): string | null {
    try {
      return wx.getStorageSync('user_openid') || null;
    } catch (error) {
      return null;
    }
  }

  setOpenid(openid: string): void {
    try {
      wx.setStorageSync('user_openid', openid);
    } catch (error) {
      console.error('保存openid失败:', error);
    }
  }

  clearToken(): void {
    try {
      wx.removeStorageSync('auth_token');
      wx.removeStorageSync('user_openid');
    } catch (error) {
      console.error('清除token失败:', error);
    }
  }

  // --- Cache management ---

  private setCache(url: string, data: any): void {
    const isCacheable = CACHEABLE_PATHS.some((p) => url.startsWith(p));
    if (!isCacheable) return;
    try {
      wx.setStorageSync(cacheKey(url), JSON.stringify({
        data,
        ts: Date.now(),
      }));
    } catch (e) {}
  }

  private getCache(url: string): any | null {
    try {
      const raw = wx.getStorageSync(cacheKey(url));
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      // 缓存有效期 24 小时
      if (Date.now() - parsed.ts > 24 * 60 * 60 * 1000) return null;
      return parsed.data;
    } catch (e) {
      return null;
    }
  }

  // --- Auth ---

  /**
   * Attempt to refresh the JWT token. Deduplicates concurrent refresh calls.
   * Returns true if a new token was obtained.
   */
  private tryRefreshToken(): Promise<boolean> {
    if (this.refreshing) return this.refreshing;

    const token = this.getToken();
    if (!token) return Promise.resolve(false);

    this.refreshing = new Promise<boolean>((resolve) => {
      wx.request({
        url: `${BASE_URL}/auth/refresh`,
        method: 'POST',
        data: { token },
        header: { 'Content-Type': 'application/json' },
        timeout: 10000,
        success: (res: any) => {
          if (res.statusCode === 200 && res.data?.token) {
            this.setToken(res.data.token);
            if (res.data.openid) this.setOpenid(res.data.openid);
            console.log('[Request] Token refreshed successfully');
            resolve(true);
          } else {
            resolve(false);
          }
        },
        fail: () => resolve(false),
      });
    }).finally(() => {
      this.refreshing = null;
    });

    return this.refreshing;
  }

  private handleUnauthorized(): void {
    this.clearToken();
    wx.showModal({
      title: '提示',
      content: '登录已过期，请重新登录',
      showCancel: false,
      success: () => {
        wx.reLaunch({ url: '/pages/index/index' });
      }
    });
  }
}

export const request = new RequestService();
