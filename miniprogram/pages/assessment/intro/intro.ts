/**
 * 评估引导页 - 优化版
 * 添加触觉反馈和流畅交互
 */

import { haptics } from '../../../utils/haptics';
import { toast } from '../../../utils/toast';

Page({
  data: {
    loaded: false
  },

  onLoad() {
    console.log('[Intro] Page loaded');

    // 页面加载完成后触发动画
    setTimeout(() => {
      this.setData({ loaded: true });
    }, 100);

    // 检查是否已有评估记录
    this.checkExistingAssessment();
  },

  onShow() {
    // 页面显示时的轻微反馈
    haptics.light();
  },

  /**
   * 检查已有评估记录
   */
  async checkExistingAssessment() {
    try {
      const userInfo = wx.getStorageSync('userInfo');
      if (!userInfo || !userInfo.latest_assessment) {
        return;
      }

      // 如果已有评估,询问是否重新评估
      const confirmed = await toast.confirm({
        title: '发现评估记录',
        content: `上次评估等级: ${userInfo.latest_assessment.overall_level}\n是否重新评估?`,
        confirmText: '重新评估',
        cancelText: '查看记录'
      });

      if (!confirmed) {
        // 跳转到历史记录
        haptics.light();
        wx.navigateTo({
          url: '/pages/assessment/history/history'
        });
      }
    } catch (e) {
      console.error('[Intro] Check existing assessment failed:', e);
    }
  },

  /**
   * 开始评估
   */
  startAssessment() {
    console.log('[Intro] Start assessment');

    // 触觉反馈 - 重要操作
    haptics.medium();

    // 埋点
    try {
      wx.reportAnalytics('assessment_start', {
        source: 'intro',
        timestamp: Date.now()
      });
    } catch (e) {
      console.warn('[Intro] Analytics report failed:', e);
    }

    // 短暂延迟，让动画完成
    setTimeout(() => {
      wx.navigateTo({
        url: '/pages/assessment/test/test',
        success: () => {
          console.log('[Intro] Navigate to test page success');
        },
        fail: (err) => {
          console.error('[Intro] Navigate failed:', err);
          toast.error('页面跳转失败');
        }
      });
    }, 150);
  },

  /**
   * 跳过评估
   */
  async skipAssessment() {
    console.log('[Intro] Skip assessment clicked');

    // 轻触反馈
    haptics.light();

    // 二次确认
    const confirmed = await toast.confirm({
      title: '确认跳过?',
      content: '评估可以帮助我们为您定制专属学习计划，建议先完成评估',
      confirmText: '仍要跳过',
      cancelText: '继续评估',
      confirmColor: '#f59e0b'
    });

    if (confirmed) {
      // 警告反馈
      haptics.warning();

      // 埋点
      try {
        wx.reportAnalytics('assessment_skipped', {
          source: 'intro',
          timestamp: Date.now()
        });
      } catch (e) {
        console.warn('[Intro] Analytics report failed:', e);
      }

      // 返回首页或上一页
      if (getCurrentPages().length > 1) {
        wx.navigateBack({
          success: () => {
            toast.info('已跳过评估');
          }
        });
      } else {
        wx.switchTab({
          url: '/pages/index/index',
          success: () => {
            toast.info('已跳过评估');
          },
          fail: () => {
            // 如果没有tabBar页面，尝试跳转到首页
            wx.redirectTo({
              url: '/pages/index/index'
            });
          }
        });
      }
    } else {
      // 用户选择继续评估
      haptics.light();
    }
  },

  /**
   * 页面卸载
   */
  onUnload() {
    console.log('[Intro] Page unload');
  }
});
