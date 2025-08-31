/**
 * Enferno Framework - Central Configuration
 * Coinbase-inspired color palette
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
                elevation: 0
            },
            VBtn: {
                variant: 'elevated',
                size: 'small'
            },
            VDataTableServer: {
                itemsPerPage: 25 ,
                itemsPerPageOptions: [ 25, 50, 100]
            }
        },
        theme: {
            defaultTheme: window.__settings__?.dark ? 'dark' : 'light',
            themes: {
                light: {
                    dark: false,
                    colors: {
                        // Modern gradient-ready colors
                        primary: '#667eea',      // Purple-blue (matches gradient start)
                        secondary: '#764ba2',    // Purple (matches gradient end)
                        accent: '#06B6D4',       // Cyan
                        error: '#EF4444',        // Red
                        info: '#3B82F6',         // Blue
                        success: '#10B981',      // Emerald
                        warning: '#F59E0B',      // Amber
                        background: '#FFFFFF',   // White
                        surface: '#F9FBFD',      // Light Gray
                    }
                },
                dark: {
                    dark: true,
                    colors: {
                        // Next.js inspired dark palette with gradient support
                        primary: '#667eea',      // Purple-blue base color (gradient applied via CSS)
                        secondary: '#8B5CF6',    // Purple
                        accent: '#06B6D4',       // Cyan
                        error: '#EF4444',        // Red
                        info: '#3B82F6',         // Blue
                        success: '#10B981',      // Emerald
                        warning: '#F59E0B',      // Amber
                        background: '#0F0F0F',   // Almost black
                        surface: '#1A1A1A',      // Dark surface
                        'surface-variant': '#262626',  // Slightly lighter surface
                        'on-background': '#FAFAFA',    // Light text on dark background
                        'on-surface': '#E5E5E5',       // Light text on surface
                        'on-primary': '#FFFFFF',       // White text on primary
                    }
                }
            }
        },
        icons: {
            defaultSet: 'mdi'
        }
    }
};
