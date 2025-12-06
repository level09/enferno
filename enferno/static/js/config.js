/**
 * Enferno Framework - Central Configuration
 * Ember/Fire-inspired color palette
 */

const config = {
    // Common Vue settings
    delimiters: ['${', '}'],

    // Vuetify configuration
    vuetifyConfig: {
        defaults: {
            VTextField: {
                variant: 'outlined'
            },
            VSelect: {
                variant: 'outlined'
            },
            VTextarea: {
                variant: 'outlined'
            },
            VCombobox: {
                variant: 'outlined'
            },
            VChip: {
                size: 'small'
            },
            VCard: {
                elevation: 0,
                rounded: 'lg'
            },
            VMenu: {
                offset: 10
            },
            VBtn: {
                variant: 'elevated',
                size: 'small'
            },
            VDataTableServer: {
                itemsPerPage: 25,
                itemsPerPageOptions: [25, 50, 100]
            }
        },
        theme: {
            defaultTheme: window.__settings__?.dark ? 'dark' : 'light',
            themes: {
                light: {
                    dark: false,
                    colors: {
                        // Ember light theme
                        primary: '#EA580C',      // Ember Orange
                        secondary: '#1E293B',    // Slate (for contrast)
                        accent: '#F97316',       // Bright Orange
                        error: '#DC2626',        // Red
                        info: '#0EA5E9',         // Sky Blue
                        success: '#16A34A',      // Green
                        warning: '#EAB308',      // Yellow
                        background: '#FFFFFF',   // White
                        surface: '#F8FAFC',      // Slate 50
                        'surface-light': '#F1F5F9', // Slate 100
                        'on-surface': '#1E293B', // Slate 800
                    }
                },
                dark: {
                    dark: true,
                    colors: {
                        // Ember dark theme
                        primary: '#F97316',      // Bright Orange (more visible on dark)
                        secondary: '#CBD5E1',    // Slate 300
                        accent: '#FB923C',       // Orange 400
                        error: '#EF4444',        // Red 500
                        info: '#38BDF8',         // Sky 400
                        success: '#22C55E',      // Green 500
                        warning: '#FACC15',      // Yellow 400
                        background: '#0F172A',   // Slate 900
                        surface: '#1E293B',      // Slate 800
                        'surface-light': '#334155', // Slate 700
                        'on-surface': '#F1F5F9', // Slate 100
                    }
                }
            }
        }
    }
};
