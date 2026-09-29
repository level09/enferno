/**
 * Enferno Components Registration
 * Registers all custom components globally on a Vue app
 */

function registerEnfernoComponents(app) {
  // Register transition component
  app.component('transition-expand', TransitionExpand);

  // Register navigation components
  app.component('vertical-nav-link', VerticalNavLink);
  app.component('vertical-nav-group', VerticalNavGroup);
  app.component('vertical-nav-section-title', VerticalNavSectionTitle);

  // Register UI components
  app.component('notification-dropdown', NotificationDropdown);
  app.component('theme-switcher', ThemeSwitcher);

  return app;
}

/**
 * Helper to resolve which component to use for a nav item
 */
function resolveNavComponent(item) {
  if ('heading' in item) return 'vertical-nav-section-title';
  if ('children' in item) return 'vertical-nav-group';
  return 'vertical-nav-link';
}

/**
 * Filter navigation items by user role
 * @param {Array} items - Navigation items
 * @param {Array} userRoles - User's roles (e.g., ['admin', 'user'])
 * @returns {Array} Filtered navigation items
 */
function filterNavByRole(items, userRoles = []) {
  // Return copies: mutating reactive items inside a computed re-triggers it forever
  return items
    .filter(item => !item.role || userRoles.includes(item.role))
    .map(item => item.children
      ? { ...item, children: filterNavByRole(item.children, userRoles) }
      : item);
}
