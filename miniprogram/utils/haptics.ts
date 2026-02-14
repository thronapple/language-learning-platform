/**
 * 触觉反馈工具类
 * 提供统一的震动反馈接口
 */

export class Haptics {
  private static enabled = true;

  /**
   * 启用/禁用触觉反馈
   */
  static setEnabled(enabled: boolean) {
    this.enabled = enabled;
  }

  /**
   * 轻触反馈 - 用于普通按钮点击
   * 使用场景：列表项点击、普通按钮
   */
  static light() {
    if (!this.enabled) return;

    try {
      wx.vibrateShort({
        type: 'light',
        success: () => {
          console.log('[Haptics] Light vibration triggered');
        },
        fail: (err) => {
          console.warn('[Haptics] Light vibration failed:', err);
        }
      });
    } catch (error) {
      console.warn('[Haptics] Vibration not supported:', error);
    }
  }

  /**
   * 中等反馈 - 用于重要操作
   * 使用场景：提交表单、切换开关、重要确认
   */
  static medium() {
    if (!this.enabled) return;

    try {
      wx.vibrateShort({
        type: 'medium',
        success: () => {
          console.log('[Haptics] Medium vibration triggered');
        },
        fail: (err) => {
          console.warn('[Haptics] Medium vibration failed:', err);
        }
      });
    } catch (error) {
      console.warn('[Haptics] Vibration not supported:', error);
    }
  }

  /**
   * 强烈反馈 - 用于完成、成功等重要时刻
   * 使用场景：任务完成、等级提升、成就解锁
   */
  static heavy() {
    if (!this.enabled) return;

    try {
      wx.vibrateShort({
        type: 'heavy',
        success: () => {
          console.log('[Haptics] Heavy vibration triggered');
        },
        fail: (err) => {
          console.warn('[Haptics] Heavy vibration failed:', err);
        }
      });
    } catch (error) {
      console.warn('[Haptics] Vibration not supported:', error);
    }
  }

  /**
   * 成功反馈
   * 使用场景：操作成功、答题正确、完成学习
   */
  static success() {
    this.heavy();
  }

  /**
   * 警告反馈
   * 使用场景：重要提示、需要注意的操作
   */
  static warning() {
    this.medium();
  }

  /**
   * 错误反馈 - 长震动
   * 使用场景：操作失败、答题错误、表单验证失败
   */
  static error() {
    if (!this.enabled) return;

    try {
      wx.vibrateLong({
        success: () => {
          console.log('[Haptics] Long vibration triggered');
        },
        fail: (err) => {
          console.warn('[Haptics] Long vibration failed:', err);
        }
      });
    } catch (error) {
      console.warn('[Haptics] Vibration not supported:', error);
    }
  }

  /**
   * 选择反馈 - 用于滑动选择器等
   * 使用场景：picker滚动、slider滑动
   */
  static selection() {
    this.light();
  }

  /**
   * 通知反馈 - 两次轻触
   * 使用场景：收到新消息、提醒通知
   */
  static notification() {
    if (!this.enabled) return;

    this.light();
    setTimeout(() => {
      this.light();
    }, 100);
  }

  /**
   * 自定义反馈模式
   * @param pattern 震动模式数组 [震动时长, 间隔, 震动时长, ...]
   */
  static custom(pattern: number[]) {
    if (!this.enabled) return;

    let index = 0;
    const execute = () => {
      if (index >= pattern.length) return;

      const duration = pattern[index];
      if (index % 2 === 0) {
        // 震动
        if (duration < 15) {
          this.light();
        } else if (duration < 30) {
          this.medium();
        } else {
          this.heavy();
        }
      }

      index++;
      if (index < pattern.length) {
        setTimeout(execute, pattern[index - 1]);
      }
    };

    execute();
  }
}

// 导出单例
export const haptics = Haptics;

// 默认导出
export default haptics;
