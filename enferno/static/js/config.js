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
                itemsPerPageOptions: [10, 25, 50, 100]
            }
        },
        theme: {
            defaultTheme: window.__settings__?.dark ? 'dark' : 'light',
            themes: {
                light: {
                    dark: false,
                    colors: {
                        // Coinbase-inspired colors
                        primary: '#0052FF',      // Coinbase Blue
                        secondary: '#1652F0',    // Secondary Blue
                        accent: '#05D2DD',       // Teal Accent
                        error: '#FF7452',        // Error Red
                        info: '#56B4FC',         // Light Blue
                        success: '#05BE7A',      // Green
                        warning: '#F6B74D',      // Orange/Yellow
                        background: '#FFFFFF',   // White
                        surface: '#F9FBFD',      // Light Gray
                    }
                },
                dark: {
                    dark: true,
                    colors: {
                        // Coinbase dark theme
                        primary: '#1652F0',      // Coinbase Blue (slightly darker)
                        secondary: '#0A46E4',    // Secondary Blue
                        accent: '#00B4D8',       // Teal Accent
                        error: '#E94B35',        // Error Red
                        info: '#3A9BF4',         // Light Blue
                        success: '#00A661',      // Green
                        warning: '#DEA54B',      // Orange/Yellow
                        background: '#0A0B0D',   // Very Dark Gray (near black)
                        surface: '#1E2026',      // Dark Gray for cards
                    }
                }
            }
        },
        icons: {
            defaultSet: 'mdi'
        }
    }
};
