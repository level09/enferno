/**
 * VerticalNavGroup Component
 * Renders a collapsible navigation group with children
 * Supports recursive nesting for unlimited depth
 */

const VerticalNavGroup = {
  name: 'VerticalNavGroup',

  props: {
    item: {
      type: Object,
      required: true
    },
    depth: {
      type: Number,
      default: 0
    }
  },

  template: `
    <li class="nav-group" :class="{ 'open': isOpen, 'active': isActive }">
      <div class="nav-group-label" @click="toggle">
        <i v-if="item.icon" :class="item.icon" class="nav-item-icon"></i>
        <span class="nav-item-title">{{ item.title }}</span>
        <span v-if="item.badge" class="nav-item-badge" :class="item.badgeClass || ''">
          {{ item.badge }}
        </span>
        <i class="ti ti-chevron-right nav-group-arrow" :class="{ 'rotate-90': isOpen }"></i>
      </div>
      <transition-expand>
        <ul v-show="isOpen" class="nav-group-children">
          <component
            v-for="child in item.children"
            :key="child.title || child.heading"
            :is="resolveNavComponent(child)"
            :item="child"
            :depth="depth + 1"
          />
        </ul>
      </transition-expand>
    </li>
  `,

  data() {
    return {
      isOpen: false
    };
  },

  computed: {
    isActive() {
      return this.hasActiveChild(this.item.children);
    }
  },

  methods: {
    resolveNavComponent(item) {
      if ('heading' in item) return 'vertical-nav-section-title';
      if ('children' in item) return 'vertical-nav-group';
      return 'vertical-nav-link';
    },

    toggle() {
      this.isOpen = !this.isOpen;
      this.saveState();
    },

    hasActiveChild(children) {
      if (!children) return false;
      const currentPath = window.location.pathname;

      return children.some(child => {
        if (child.to) {
          // Check if this child's route matches
          if (currentPath === child.to ||
              (child.to !== '/' && currentPath.startsWith(child.to + '/'))) {
            return true;
          }
        }
        // Recursively check nested children
        if (child.children) {
          return this.hasActiveChild(child.children);
        }
        return false;
      });
    },

    saveState() {
      const key = 'enferno-nav-groups';
      let openGroups = JSON.parse(localStorage.getItem(key) || '[]');
      const groupId = this.item.title;

      if (this.isOpen && !openGroups.includes(groupId)) {
        openGroups.push(groupId);
      } else if (!this.isOpen) {
        openGroups = openGroups.filter(g => g !== groupId);
      }

      localStorage.setItem(key, JSON.stringify(openGroups));
    },

    loadState() {
      const key = 'enferno-nav-groups';
      const openGroups = JSON.parse(localStorage.getItem(key) || '[]');
      return openGroups.includes(this.item.title);
    }
  },

  mounted() {
    // Auto-open if contains active route
    if (this.isActive) {
      this.isOpen = true;
    } else {
      // Otherwise, restore from localStorage
      this.isOpen = this.loadState();
    }
  }
};
