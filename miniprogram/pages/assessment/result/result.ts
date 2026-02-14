// miniprogram/pages/assessment/result/result.ts

interface AssessmentResult {
  overall_level: string;
  ability_score: number;
  confidence: number;
  dimensions: {
    [key: string]: {
      level: string;
      accuracy: number;
      ability: number;
    };
  };
  weak_areas: string[];
  strong_areas: string[];
  recommendations: {
    suggested_scenarios: string[];
    focus_areas: string[];
    estimated_study_days: number;
  };
  duration?: number;
}

interface DimensionInfo {
  name: string;
  label: string;
  level: string;
  accuracy: number;
  accuracyPercent: number;
  ability: number;
  color: string;
}

Page({
  data: {
    result: null as AssessmentResult | null,
    dimensionList: [] as DimensionInfo[],
    showBadge: false
  },

  onLoad(options: any) {
    // 从URL参数中解析结果数据
    if (options.data) {
      try {
        const result = JSON.parse(decodeURIComponent(options.data)) as AssessmentResult;
        this.setData({ result });
        this.processDimensions(result);
        this.initAnimations();
        this.drawRadarChart();
      } catch (error) {
        console.error('解析结果数据失败:', error);
        wx.showToast({
          title: '数据加载失败',
          icon: 'none'
        });
      }
    }
  },

  /**
   * 处理维度数据
   */
  processDimensions(result: AssessmentResult) {
    const dimensionColors = {
      listening: '#667eea',
      reading: '#764ba2',
      vocabulary: '#f093fb',
      grammar: '#4facfe'
    };

    const dimensionLabels = {
      listening: '听力理解',
      reading: '阅读理解',
      vocabulary: '词汇掌握',
      grammar: '语法运用'
    };

    const dimensionList: DimensionInfo[] = Object.entries(result.dimensions).map(
      ([name, data]) => ({
        name,
        label: dimensionLabels[name as keyof typeof dimensionLabels] || name,
        level: data.level,
        accuracy: data.accuracy,
        accuracyPercent: Math.round(data.accuracy * 100),
        ability: data.ability,
        color: dimensionColors[name as keyof typeof dimensionColors] || '#999'
      })
    );

    this.setData({ dimensionList });
  },

  /**
   * 初始化动画
   */
  initAnimations() {
    // 延迟显示徽章动画
    setTimeout(() => {
      this.setData({ showBadge: true });
    }, 300);
  },

  /**
   * 绘制雷达图
   */
  drawRadarChart() {
    // 延迟执行，确保DOM已渲染
    setTimeout(() => {
      console.log('开始绘制雷达图，使用旧版API');
      this.drawRadarChartLegacy();
    }, 300);
  },

  /**
   * 旧版Canvas绘制(降级方案)
   */
  drawRadarChartLegacy() {
    try {
      const ctx = wx.createCanvasContext('radarCanvas', this);
      const systemInfo = wx.getSystemInfoSync();

      // 简化尺寸计算
      const width = systemInfo.windowWidth - 80;
      const height = 300;

      console.log('Canvas尺寸:', width, height);

      this.renderRadar(ctx, width, height);
      ctx.draw();
    } catch (error) {
      console.error('Canvas绘制失败:', error);
    }
  },

  /**
   * 渲染雷达图
   */
  renderRadar(ctx: any, width: number, height: number) {
    const { dimensionList } = this.data;
    if (!dimensionList || dimensionList.length === 0) return;

    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) * 0.35;
    const levels = 5; // 5个等级圈
    const angleStep = (Math.PI * 2) / dimensionList.length;

    // 绘制背景网格
    ctx.strokeStyle = '#e0e0e0';
    ctx.lineWidth = 1;

    for (let i = 1; i <= levels; i++) {
      const r = (radius / levels) * i;
      ctx.beginPath();

      for (let j = 0; j <= dimensionList.length; j++) {
        const angle = angleStep * j - Math.PI / 2;
        const x = centerX + r * Math.cos(angle);
        const y = centerY + r * Math.sin(angle);

        if (j === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }

      ctx.closePath();
      ctx.stroke();
    }

    // 绘制轴线
    ctx.strokeStyle = '#ccc';
    ctx.lineWidth = 1;

    dimensionList.forEach((_, index) => {
      const angle = angleStep * index - Math.PI / 2;
      const x = centerX + radius * Math.cos(angle);
      const y = centerY + radius * Math.sin(angle);

      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.lineTo(x, y);
      ctx.stroke();
    });

    // 绘制数据区域
    ctx.fillStyle = 'rgba(102, 126, 234, 0.2)';
    ctx.strokeStyle = '#667eea';
    ctx.lineWidth = 2;
    ctx.beginPath();

    dimensionList.forEach((dimension, index) => {
      const angle = angleStep * index - Math.PI / 2;
      // 将accuracy (0-1) 映射到半径
      const r = radius * dimension.accuracy;
      const x = centerX + r * Math.cos(angle);
      const y = centerY + r * Math.sin(angle);

      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }

      // 绘制数据点
      ctx.save();
      ctx.fillStyle = dimension.color;
      ctx.beginPath();
      ctx.arc(x, y, 6, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    });

    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    // 绘制维度标签
    ctx.fillStyle = '#333';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    dimensionList.forEach((dimension, index) => {
      const angle = angleStep * index - Math.PI / 2;
      const labelRadius = radius + 30;
      const x = centerX + labelRadius * Math.cos(angle);
      const y = centerY + labelRadius * Math.sin(angle);

      ctx.fillText(dimension.label, x, y);
    });
  },

  /**
   * 获取场景图标
   */
  getScenarioIcon(scenarioName: string): string {
    const iconMap: { [key: string]: string } = {
      '机场场景': '✈️',
      '酒店场景': '🏨',
      '商务会议': '💼',
      '餐厅用餐': '🍽️',
      '购物场景': '🛍️',
      '交通出行': '🚕',
      '医疗急救': '🏥',
      '社交场合': '🎉'
    };

    return iconMap[scenarioName] || '📚';
  },

  /**
   * 点击雷达图
   */
  onRadarTap() {
    // 可以添加交互效果，比如显示详细数据
    wx.showToast({
      title: '点击维度查看详情',
      icon: 'none'
    });
  },

  /**
   * 生成学习计划
   */
  generatePlan() {
    const { result } = this.data;

    if (!result) {
      wx.showToast({
        title: '数据异常',
        icon: 'none'
      });
      return;
    }

    // 埋点
    wx.reportAnalytics('plan_generate_click', {
      overall_level: result.overall_level,
      estimated_days: result.recommendations.estimated_study_days
    });

    // TODO: 调用计划生成API
    wx.showLoading({ title: '生成中...' });

    setTimeout(() => {
      wx.hideLoading();

      // 跳转到学习计划页面
      wx.redirectTo({
        url: '/pages/plan/index/index'
      });
    }, 1500);
  },

  /**
   * 查看历史评估
   */
  async viewHistory() {
    wx.navigateTo({
      url: '/pages/assessment/history/history'
    });
  }
});
