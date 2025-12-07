/**
 * NotificationDropdown Component
 * Renders a notification bell with dropdown menu
 */

const NotificationDropdown = {
  name: 'NotificationDropdown',

  props: {
    notifications: {
      type: Array,
      default: () => []
    }
  },

  emits: ['click', 'mark-read', 'mark-all-read', 'remove'],

  template: `
    <v-menu offset="14" :close-on-content-click="false" max-width="380" transition="fade-transition">
      <template v-slot:activator="{ props }">
        <v-btn v-bind="props" icon variant="text" size="small">
          <v-badge
            :model-value="unreadCount > 0"
            :content="unreadCount"
            color="error"
            offset-x="-2"
            offset-y="-2"
          >
            <i class="ti ti-bell" style="font-size: 22px;"></i>
          </v-badge>
        </v-btn>
      </template>

      <v-card width="380">
        <v-card-title class="d-flex align-center py-3 px-4">
          <span class="text-body-1 font-weight-medium">Notifications</span>
          <v-chip v-if="unreadCount > 0" size="x-small" color="primary" class="ml-2">
            {{ unreadCount }} New
          </v-chip>
          <v-spacer></v-spacer>
          <v-btn
            v-if="notifications.length"
            icon
            variant="text"
            size="x-small"
            @click="markAllRead"
            title="Mark all as read"
          >
            <i class="ti ti-mail-opened" style="font-size: 18px;"></i>
          </v-btn>
        </v-card-title>

        <v-divider></v-divider>

        <v-list class="notification-list py-0">
          <template v-for="(notification, index) in notifications" :key="notification.id">
            <v-list-item
              class="notification-item py-3"
              :class="{ 'bg-grey-lighten-4': !notification.isSeen }"
              @click="handleClick(notification)"
            >
              <template v-slot:prepend>
                <v-avatar
                  :image="notification.img"
                  :color="notification.color || 'primary'"
                  size="40"
                >
                  <i v-if="notification.icon && !notification.img" :class="notification.icon" style="font-size: 20px;"></i>
                  <span v-else-if="!notification.img">{{ avatarText(notification.title) }}</span>
                </v-avatar>
              </template>

              <v-list-item-title class="text-body-2 font-weight-medium mb-1">
                {{ notification.title }}
              </v-list-item-title>
              <v-list-item-subtitle class="text-caption">
                {{ notification.subtitle }}
              </v-list-item-subtitle>
              <v-list-item-subtitle v-if="notification.time" class="text-caption mt-1" style="opacity: 0.6;">
                {{ notification.time }}
              </v-list-item-subtitle>

              <template v-slot:append>
                <div class="d-flex flex-column align-center">
                  <v-badge
                    v-if="!notification.isSeen"
                    dot
                    color="primary"
                    inline
                  ></v-badge>
                  <v-btn
                    icon
                    variant="text"
                    size="x-small"
                    class="visible-on-hover mt-1"
                    @click.stop="removeNotification(notification.id)"
                    title="Remove"
                  >
                    <i class="ti ti-x" style="font-size: 16px;"></i>
                  </v-btn>
                </div>
              </template>
            </v-list-item>
            <v-divider v-if="index < notifications.length - 1"></v-divider>
          </template>

          <v-list-item v-if="!notifications.length" class="text-center py-8">
            <div class="d-flex flex-column align-center">
              <i class="ti ti-bell-off mb-2" style="font-size: 48px; opacity: 0.3;"></i>
              <v-list-item-title class="text-body-2 text-medium-emphasis">
                No notifications
              </v-list-item-title>
            </div>
          </v-list-item>
        </v-list>

        <template v-if="notifications.length">
          <v-divider></v-divider>
          <v-card-actions class="pa-3">
            <v-btn block variant="text" color="primary">
              View All Notifications
            </v-btn>
          </v-card-actions>
        </template>
      </v-card>
    </v-menu>
  `,

  computed: {
    unreadCount() {
      return this.notifications.filter(n => !n.isSeen).length;
    }
  },

  methods: {
    avatarText(text) {
      if (!text) return '';
      return text.split(' ').map(w => w[0]).join('').substring(0, 2).toUpperCase();
    },

    markAllRead() {
      this.$emit('mark-all-read');
    },

    handleClick(notification) {
      this.$emit('click', notification);
      if (!notification.isSeen) {
        this.$emit('mark-read', notification.id);
      }
    },

    removeNotification(id) {
      this.$emit('remove', id);
    }
  }
};
