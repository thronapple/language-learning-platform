/**
 * 加载状态管理工具类
 * 统一管理加载状态和骨架屏
 */

export class Loading {
  private static loadingCount = 0;

  /**
   * 显示加载提示
   * @param title 加载文字
   * @param mask 是否显示遮罩
   */
  static show(title = '加载中...', mask = true) {
    this.loadingCount++;

    wx.showLoading({
      title,
      mask,
      success: () => {
        console.log('[Loading] Show loading:', title);
      },
      fail: (err) => {
        console.warn('[Loading] Show loading failed:', err);
      }
    });
  }

  /**
   * 隐藏加载提示
   * 支持多次调用show后统一隐藏
   */
  static hide() {
    this.loadingCount = Math.max(0, this.loadingCount - 1);

    if (this.loadingCount === 0) {
      wx.hideLoading({
        success: () => {
          console.log('[Loading] Hide loading');
        },
        fail: (err) => {
          console.warn('[Loading] Hide loading failed:', err);
        }
      });
    }
  }

  /**
   * 强制隐藏加载提示
   */
  static forceHide() {
    this.loadingCount = 0;
    wx.hideLoading();
  }

  /**
   * 包装异步操作，自动显示和隐藏加载
   * @param promise 异步操作
   * @param title 加载文字
   * @param mask 是否显示遮罩
   */
  static async wrap<T>(
    promise: Promise<T>,
    title = '加载中...',
    mask = true
  ): Promise<T> {
    this.show(title, mask);

    try {
      const result = await promise;
      this.hide();
      return result;
    } catch (error) {
      this.hide();
      throw error;
    }
  }

  /**
   * 延迟显示加载（避免闪烁）
   * 如果操作很快完成，不显示加载提示
   * @param promise 异步操作
   * @param title 加载文字
   * @param delay 延迟时间（毫秒）
   */
  static async delayWrap<T>(
    promise: Promise<T>,
    title = '加载中...',
    delay = 300
  ): Promise<T> {
    let showLoading = false;
    let resolved = false;

    // 延迟显示加载
    const timer = setTimeout(() => {
      if (!resolved) {
        showLoading = true;
        this.show(title);
      }
    }, delay);

    try {
      const result = await promise;
      resolved = true;
      clearTimeout(timer);

      if (showLoading) {
        this.hide();
      }

      return result;
    } catch (error) {
      resolved = true;
      clearTimeout(timer);

      if (showLoading) {
        this.hide();
      }

      throw error;
    }
  }

  /**
   * 批量异步操作
   * @param promises 异步操作数组
   * @param title 加载文字
   */
  static async all<T>(
    promises: Promise<T>[],
    title = '加载中...'
  ): Promise<T[]> {
    return this.wrap(Promise.all(promises), title);
  }

  /**
   * 获取当前加载计数
   */
  static getCount(): number {
    return this.loadingCount;
  }

  /**
   * 是否正在加载
   */
  static isLoading(): boolean {
    return this.loadingCount > 0;
  }
}

// 导出单例
export const loading = Loading;

// 默认导出
export default loading;
