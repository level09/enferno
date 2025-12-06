/**
 * TransitionExpand Component
 * Provides smooth height-based expand/collapse animation
 */

const TransitionExpand = {
  name: 'TransitionExpand',

  methods: {
    onEnter(el) {
      const width = getComputedStyle(el).width;
      el.style.width = width;
      el.style.position = 'absolute';
      el.style.visibility = 'hidden';
      el.style.height = 'auto';

      const height = getComputedStyle(el).height;

      el.style.width = '';
      el.style.position = '';
      el.style.visibility = '';
      el.style.height = '0px';

      getComputedStyle(el).height; // Force repaint

      requestAnimationFrame(() => {
        el.style.height = height;
      });
    },

    onAfterEnter(el) {
      el.style.height = 'auto';
    },

    onLeave(el) {
      const height = getComputedStyle(el).height;
      el.style.height = height;

      getComputedStyle(el).height; // Force repaint

      requestAnimationFrame(() => {
        el.style.height = '0px';
      });
    },

    onAfterLeave(el) {
      el.style.height = '';
    }
  },

  render() {
    return Vue.h(
      Vue.Transition,
      {
        name: 'expand',
        onEnter: this.onEnter,
        onAfterEnter: this.onAfterEnter,
        onLeave: this.onLeave,
        onAfterLeave: this.onAfterLeave
      },
      this.$slots.default
    );
  }
};
