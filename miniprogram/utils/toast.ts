/**
 * Toast提示工具类
 * 统一管理各类提示消息
 */

import { haptics } from './haptics';

export interface ToastOptions {
  title: string;
  duration?: number;
  mask?: boolean;
  icon?: 'success' | 'error' | 'loading' | 'none';
}

export class Toast {
  private static defaultDuration = 2000;
  private static queue: ToastOptions[] = [];
  private static showing = false;

  /**
   * 成功提示
   * @param title 提示文字
   * @param duration 显示时长（毫秒）
   */
  static success(title: string, duration = this.defaultDuration) {
    haptics.success();

    wx.showToast({
      title,
      icon: 'success',
      duration,
      mask: false
    });
  }

  /**
   * 错误提示
   * @param title 错误信息
   * @param duration 显示时长（毫秒）
   */
  static error(title: string, duration = this.defaultDuration) {
    haptics.error();

    wx.showToast({
      title,
      icon: 'error',
      duration,
      mask: false
    });
  }

  /**
   * 普通提示（无图标）
   * @param title 提示文字
   * @param duration 显示时长（毫秒）
   */
  static info(title: string, duration = this.defaultDuration) {
    wx.showToast({
      title,
      icon: 'none',
      duration,
      mask: false
    });
  }

  /**
   * 警告提示
   * @param title 警告信息
   * @param duration 显示时长（毫秒）
   */
  static warning(title: string, duration = this.defaultDuration) {
    haptics.warning();

    wx.showToast({
      title,
      icon: 'none',
      duration,
      mask: false
    });
  }

  /**
   * 加载提示
   * @param title 加载文字
   * @param mask 是否显示透明蒙层，防止触摸穿透
   */
  static loading(title = '加载中...', mask = true) {
    wx.showLoading({
      title,
      mask
    });
  }

  /**
   * 隐藏提示
   */
  static hide() {
    wx.hideToast();
  }

  /**
   * 隐藏加载提示
   */
  static hideLoading() {
    wx.hideLoading();
  }

  /**
   * 包装异步操作，自动显示加载和结果
   * @param promise 异步操作
   * @param loadingText 加载文字
   * @param successText 成功文字
   * @param errorText 错误文字
   */
  static async wrap<T>(
    promise: Promise<T>,
    loadingText = '处理中...',
    successText?: string,
    errorText?: string
  ): Promise<T> {
    this.loading(loadingText);

    try {
      const result = await promise;
      this.hideLoading();

      if (successText) {
        this.success(successText);
      }

      return result;
    } catch (error: any) {
      this.hideLoading();

      const message = errorText || error.message || '操作失败';
      this.error(message);

      throw error;
    }
  }

  /**
   * 显示确认对话框
   * @param options 对话框选项
   */
  static confirm(options: {
    title?: string;
    content: string;
    confirmText?: string;
    cancelText?: string;
    confirmColor?: string;
    cancelColor?: string;
  }): Promise<boolean> {
    return new Promise((resolve) => {
      wx.showModal({
        title: options.title || '提示',
        content: options.content,
        confirmText: options.confirmText || '确定',
        cancelText: options.cancelText || '取消',
        confirmColor: options.confirmColor || '#576B95',
        cancelColor: options.cancelColor || '#000000',
        success: (res) => {
          if (res.confirm) {
            haptics.medium();
            resolve(true);
          } else if (res.cancel) {
            haptics.light();
            resolve(false);
          }
        },
        fail: () => {
          resolve(false);
        }
      });
    });
  }

  /**
   * 显示操作菜单
   * @param items 菜单项
   */
  static showActionSheet(items: string[]): Promise<number> {
    return new Promise((resolve, reject) => {
      wx.showActionSheet({
        itemList: items,
        success: (res) => {
          haptics.light();
          resolve(res.tapIndex);
        },
        fail: (err) => {
          if (err.errMsg !== 'showActionSheet:fail cancel') {
            reject(err);
          } else {
            resolve(-1);
          }
        }
      });
    });
  }

  /**
   * 队列式显示toast（避免重叠）
   * @param options Toast选项
   */
  static queue(options: ToastOptions) {
    this.queue.push(options);

    if (!this.showing) {
      this.processQueue();
    }
  }

  private static async processQueue() {
    if (this.queue.length === 0) {
      this.showing = false;
      return;
    }

    this.showing = true;
    const options = this.queue.shift()!;
    const duration = options.duration || this.defaultDuration;

    wx.showToast({
      title: options.title,
      icon: options.icon || 'none',
      duration,
      mask: options.mask || false
    });

    await new Promise(resolve => setTimeout(resolve, duration + 300));
    this.processQueue();
  }
}

// 导出单例
export const toast = Toast;

// 默认导出
export default toast;
