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
  abilityDisplay: string;
  color: string;
  description: string;
  suggestions: string[];
}

Page({
  data: {
    result: null as AssessmentResult | null,
    dimensionList: [] as DimensionInfo[],
    showBadge: false,
    showDimensionDetail: false,
    selectedDimension: null as DimensionInfo | null,
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
    const dimensionColors: Record<string, string> = {
      listening: '#667eea',
      reading: '#764ba2',
      vocabulary: '#f093fb',
      grammar: '#4facfe'
    };

    const dimensionLabels: Record<string, string> = {
      listening: '听力理解',
      reading: '阅读理解',
      vocabulary: '词汇掌握',
      grammar: '语法运用'
    };

    const dimensionDescriptions: Record<string, string> = {
      listening: '听力理解能力衡量你对英语口语的理解程度，包括日常对话、广播通知、指令等不同场景下的听力水平。',
      reading: '阅读理解能力衡量你对英文文本的理解程度，包括文章主旨把握、细节捕捉和推理判断等。',
      vocabulary: '词汇掌握能力衡量你的英语词汇量和词义理解深度，包括常用词汇、近义词辨析和语境用词等。',
      grammar: '语法运用能力衡量你对英语语法规则的掌握程度，包括时态、语态、从句结构和介词搭配等。'
    };

    const dimensionSuggestions: Record<string, Record<string, string[]>> = {
      listening: {
        weak: [
          '每天收听15分钟英语播客（推荐BBC Learning English）',
          '看英文电影时先关字幕，再开英文字幕对照',
          '从场景对话开始练习，如机场、酒店场景'
        ],
        normal: [
          '尝试收听语速较快的新闻节目',
          '练习听写（dictation）训练精听能力',
          '参与英语角或在线对话练习'
        ],
        strong: [
          '挑战TED演讲和学术讲座听力',
          '练习听辩不同口音（英式、美式、澳式）',
          '尝试同声传译练习提升反应速度'
        ]
      },
      reading: {
        weak: [
          '从分级读物开始，选择适合当前水平的材料',
          '养成查词习惯，遇到生词先猜测再查证',
          '每天阅读一篇短文并总结大意'
        ],
        normal: [
          '阅读英文新闻网站（BBC、CNN）扩大阅读面',
          '尝试阅读英文原版小说',
          '练习快速阅读和精读相结合'
        ],
        strong: [
          '阅读学术论文和专业文献',
          '挑战文学作品赏析和评论写作',
          '尝试速读训练，提升阅读效率'
        ]
      },
      vocabulary: {
        weak: [
          '使用间隔重复法（SRS）每天学习10个新词',
          '在语境中学习词汇，而非死记硬背',
          '从高频词汇表开始，优先掌握常用词'
        ],
        normal: [
          '学习词根词缀提升词汇推导能力',
          '通过阅读自然积累词汇，做好生词笔记',
          '练习同义词和反义词辨析'
        ],
        strong: [
          '学习学术词汇和专业术语',
          '关注词汇的隐含义和文化内涵',
          '挑战高级词汇测试如GRE词汇'
        ]
      },
      grammar: {
        weak: [
          '复习基础语法框架：时态、主谓一致、简单句型',
          '通过造句练习巩固语法规则',
          '使用语法练习APP进行针对性训练'
        ],
        normal: [
          '学习复合句和从句结构',
          '练习虚拟语气和条件句',
          '通过写作练习应用高级语法结构'
        ],
        strong: [
          '研究语法的例外情况和高级用法',
          '通过学术写作训练精确的语法表达',
          '练习语法校对，提升语感'
        ]
      }
    };

    const isWeak = (name: string) => result.weak_areas?.includes(name);
    const isStrong = (name: string) => result.strong_areas?.includes(name);

    const dimensionList: DimensionInfo[] = Object.entries(result.dimensions).map(
      ([name, data]) => {
        const strength = isWeak(name) ? 'weak' : isStrong(name) ? 'strong' : 'normal';
        return {
          name,
          label: dimensionLabels[name] || name,
          level: data.level,
          accuracy: data.accuracy,
          accuracyPercent: Math.round(data.accuracy * 100),
          ability: data.ability,
          abilityDisplay: data.ability.toFixed(1),
          color: dimensionColors[name] || '#999',
          description: dimensionDescriptions[name] || '',
          suggestions: dimensionSuggestions[name]?.[strength] || []
        };
      }
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
      const height = 400;

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
    const centerY = height / 2 - 15;
    const radius = Math.min(width, height) * 0.25;
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
      const labelRadius = radius + 40;
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
    wx.showToast({
      title: '点击下方维度查看详情',
      icon: 'none'
    });
  },

  /**
   * 点击维度项查看详情
   */
  onDimensionTap(e: any) {
    const name = e.currentTarget.dataset.name;
    const dimension = this.data.dimensionList.find(d => d.name === name);
    if (dimension) {
      this.setData({
        selectedDimension: dimension,
        showDimensionDetail: true
      });
    }
  },

  /**
   * 关闭维度详情弹窗
   */
  closeDimensionDetail() {
    this.setData({ showDimensionDetail: false });
  },

  /**
   * 生成学习计划
   */
  async generatePlan() {
    const { result } = this.data;

    if (!result) {
      wx.showToast({ title: '数据异常', icon: 'none' });
      return;
    }

    wx.reportAnalytics('plan_generate_click', {
      overall_level: result.overall_level,
      estimated_days: result.recommendations.estimated_study_days
    });

    wx.showLoading({ title: '生成中...' });

    try {
      const { request } = require('../../../services/request');
      await request.post('/api/plan/generate', {
        overall_level: result.overall_level,
        weak_areas: result.weak_areas,
        strong_areas: result.strong_areas,
        daily_minutes: 30,
        focus_categories: [],
      });

      wx.hideLoading();
      wx.showToast({ title: '计划已生成', icon: 'success' });

      setTimeout(() => {
        wx.redirectTo({ url: '/pages/plan/index/index' });
      }, 1000);
    } catch (error) {
      wx.hideLoading();
      console.error('[Result] Plan generation failed:', error);
      wx.showToast({ title: '生成失败，请重试', icon: 'none' });
    }
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
