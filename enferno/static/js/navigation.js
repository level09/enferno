/**
 * Enferno Navigation Configuration
 * Define your sidebar navigation structure here
 */

const enfernoNavigation = [
  {
    heading: 'Main'
  },
  {
    title: 'Dashboard',
    icon: 'ti ti-home',
    to: '/dashboard'
  },
  {
    heading: 'Account'
  },
  {
    title: 'Change Password',
    icon: 'ti ti-key',
    to: '/change'
  },
  {
    title: 'Two-Factor Auth',
    icon: 'ti ti-shield-lock',
    to: '/tf-setup'
  },
  {
    title: 'Recovery Codes',
    icon: 'ti ti-lifebuoy',
    to: '/mf-recovery-codes'
  },
  {
    heading: 'Administration'
  },
  {
    title: 'User Management',
    icon: 'ti ti-users-group',
    role: 'admin',
    children: [
      {
        title: 'Users',
        icon: 'ti ti-users',
        to: '/users'
      },
      {
        title: 'Roles',
        icon: 'ti ti-shield',
        to: '/roles'
      }
    ]
  },
  {
    title: 'Activity Logs',
    icon: 'ti ti-history',
    to: '/activities',
    role: 'admin'
  }
];
