/**
 * 骨架屏组件
 */

Component({
  options: {
    multipleSlots: true,
    styleIsolation: 'apply-shared'
  },

  properties: {
    // 骨架屏类型: card | list | article | custom
    type: {
      type: String,
      value: 'card'
    },

    // 列表骨架的行数
    rows: {
      type: Number,
      value: 3
    },

    // 是否显示（用于条件渲染）
    show: {
      type: Boolean,
      value: true
    },

    // 自定义class
    customClass: {
      type: String,
      value: ''
    }
  },

  data: {},

  lifetimes: {
    attached() {
      console.log('[Skeleton] Component attached, type:', this.data.type);
    }
  },

  methods: {}
});
