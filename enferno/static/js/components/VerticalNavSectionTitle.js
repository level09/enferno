/**
 * VerticalNavSectionTitle Component
 * Renders a section heading/divider in the navigation
 */

const VerticalNavSectionTitle = {
  name: 'VerticalNavSectionTitle',

  props: {
    item: {
      type: Object,
      required: true
    }
  },

  template: `
    <li class="nav-section-title">
      <span>{{ item.heading }}</span>
    </li>
  `
};
