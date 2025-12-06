/**
 * VerticalNavLink Component
 * Renders a single navigation link item
 */

const VerticalNavLink = {
  name: 'VerticalNavLink',

  props: {
    item: {
      type: Object,
      required: true
    }
  },

  template: `
    <li class="nav-link" :class="{ 'active': isActive }">
      <a :href="item.to" :target="item.target || '_self'">
        <i v-if="item.icon" :class="item.icon" class="nav-item-icon"></i>
        <span class="nav-item-title">{{ item.title }}</span>
        <span v-if="item.badge" class="nav-item-badge" :class="item.badgeClass || ''">
          {{ item.badge }}
        </span>
      </a>
    </li>
  `,

  computed: {
    isActive() {
      const currentPath = window.location.pathname;
      // Exact match or starts with (for nested routes)
      return currentPath === this.item.to ||
             (this.item.to !== '/' && currentPath.startsWith(this.item.to + '/'));
    }
  }
};
