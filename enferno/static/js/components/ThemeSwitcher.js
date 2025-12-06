/**
 * ThemeSwitcher Component
 * Toggle between light and dark themes
 */

const ThemeSwitcher = {
  name: 'ThemeSwitcher',

  template: `
    <v-btn icon variant="text" size="small" @click="toggleTheme" :title="isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'">
      <i :class="isDark ? 'ti ti-sun' : 'ti ti-moon'" style="font-size: 22px;"></i>
    </v-btn>
  `,

  data() {
    return {
      isDark: false
    };
  },

  methods: {
    toggleTheme() {
      this.isDark = !this.isDark;

      // Update Vuetify theme
      if (this.$vuetify) {
        this.$vuetify.theme.global.name = this.isDark ? 'dark' : 'light';
      }

      // Toggle body class for CSS targeting
      document.body.classList.toggle('dark-mode', this.isDark);

      // Save preference
      localStorage.setItem('enferno-theme', this.isDark ? 'dark' : 'light');

      // Update window settings if available
      if (window.__settings__) {
        window.__settings__.dark = this.isDark;
      }
    },

    loadTheme() {
      // Check localStorage first
      const saved = localStorage.getItem('enferno-theme');
      if (saved) {
        this.isDark = saved === 'dark';
      } else if (window.__settings__?.dark !== undefined) {
        // Fall back to server-provided setting
        this.isDark = window.__settings__.dark;
      } else {
        // Fall back to system preference
        this.isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      }

      // Apply theme
      if (this.$vuetify) {
        this.$vuetify.theme.global.name = this.isDark ? 'dark' : 'light';
      }

      // Apply body class for CSS targeting
      document.body.classList.toggle('dark-mode', this.isDark);
    }
  },

  mounted() {
    this.loadTheme();
  }
};
