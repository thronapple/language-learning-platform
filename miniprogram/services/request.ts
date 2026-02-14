// miniprogram/services/request.ts

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

class RequestService {
  private baseURL: string;
  private timeout: number;

  constructor() {
    // 从环境变量或配置中获取API基础URL
    // 开发环境可以使用CloudBase云函数URL或本地测试URL
    this.baseURL = this.getBaseURL();
    this.timeout = 30000; // 30秒超时
  }

  /**
   * 获取API基础URL
   */
  private getBaseURL(): string {
    // 生产环境使用CloudBase云函数HTTP访问链接
    // 开发环境可以配置为本地测试地址
    const accountInfo = wx.getAccountInfoSync();
    const envVersion = accountInfo.miniProgram.envVersion;

    if (envVersion === 'develop') {
      // 开发版：可以配置为本地开发服务器
      return 'http://localhost:8000/api';
    } else if (envVersion === 'trial') {
      // 体验版：使用测试环境云函数
      return 'https://your-test-env.service.tcloudbase.com/api';
    } else {
      // 正式版：使用生产环境云函数
      return 'https://your-prod-env.service.tcloudbase.com/api';
    }
  }

  /**
   * 通用请求方法
   */
  private async request<T = any>(config: RequestConfig): Promise<T> {
    const { url, method = 'GET', data, header = {} } = config;

    // 获取token
    const token = this.getToken();
    if (token) {
      header['Authorization'] = `Bearer ${token}`;
    }

    header['Content-Type'] = 'application/json';

    return new Promise((resolve, reject) => {
      wx.request({
        url: `${this.baseURL}${url}`,
        method,
        data,
        header,
        timeout: this.timeout,

        success: (res: RequestResponse) => {
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve(res.data as T);
          } else if (res.statusCode === 401) {
            // Token过期，清除并跳转登录
            this.handleUnauthorized();
            reject(new Error('未授权，请重新登录'));
          } else {
            const errorMessage = (res.data as any)?.message || '请求失败';
            reject(new Error(errorMessage));
          }
        },

        fail: (error) => {
          console.error('请求失败:', error);

          if (error.errMsg.includes('timeout')) {
            reject(new Error('请求超时，请检查网络'));
          } else if (error.errMsg.includes('fail')) {
            reject(new Error('网络连接失败'));
          } else {
            reject(new Error(error.errMsg || '请求失败'));
          }
        }
      });
    });
  }

  /**
   * GET请求
   */
  async get<T = any>(url: string, params?: any): Promise<T> {
    let queryString = '';
    if (params) {
      queryString = '?' + Object.entries(params)
        .map(([key, value]) => `${key}=${encodeURIComponent(String(value))}`)
        .join('&');
    }

    return this.request<T>({
      url: url + queryString,
      method: 'GET'
    });
  }

  /**
   * POST请求
   */
  async post<T = any>(url: string, data?: any): Promise<T> {
    return this.request<T>({
      url,
      method: 'POST',
      data
    });
  }

  /**
   * PUT请求
   */
  async put<T = any>(url: string, data?: any): Promise<T> {
    return this.request<T>({
      url,
      method: 'PUT',
      data
    });
  }

  /**
   * DELETE请求
   */
  async delete<T = any>(url: string): Promise<T> {
    return this.request<T>({
      url,
      method: 'DELETE'
    });
  }

  /**
   * 获取Token
   */
  private getToken(): string | null {
    try {
      return wx.getStorageSync('auth_token');
    } catch (error) {
      console.error('获取token失败:', error);
      return null;
    }
  }

  /**
   * 设置Token
   */
  setToken(token: string): void {
    try {
      wx.setStorageSync('auth_token', token);
    } catch (error) {
      console.error('保存token失败:', error);
    }
  }

  /**
   * 清除Token
   */
  clearToken(): void {
    try {
      wx.removeStorageSync('auth_token');
    } catch (error) {
      console.error('清除token失败:', error);
    }
  }

  /**
   * 处理未授权
   */
  private handleUnauthorized(): void {
    this.clearToken();

    wx.showModal({
      title: '提示',
      content: '登录已过期，请重新登录',
      showCancel: false,
      success: () => {
        wx.reLaunch({
          url: '/pages/auth/login/login'
        });
      }
    });
  }

  /**
   * 上传文件
   */
  async uploadFile(filePath: string, name: string = 'file'): Promise<any> {
    const token = this.getToken();
    const header: any = {};

    if (token) {
      header['Authorization'] = `Bearer ${token}`;
    }

    return new Promise((resolve, reject) => {
      wx.uploadFile({
        url: `${this.baseURL}/upload`,
        filePath,
        name,
        header,

        success: (res) => {
          if (res.statusCode >= 200 && res.statusCode < 300) {
            const data = JSON.parse(res.data);
            resolve(data);
          } else {
            reject(new Error('上传失败'));
          }
        },

        fail: (error) => {
          reject(error);
        }
      });
    });
  }

  /**
   * 下载文件
   */
  async downloadFile(url: string): Promise<string> {
    return new Promise((resolve, reject) => {
      wx.downloadFile({
        url: `${this.baseURL}${url}`,

        success: (res) => {
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve(res.tempFilePath);
          } else {
            reject(new Error('下载失败'));
          }
        },

        fail: (error) => {
          reject(error);
        }
      });
    });
  }
}

// 导出单例
export const request = new RequestService();
