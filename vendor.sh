#!/usr/bin/env bash
# Refresh vendored frontend assets. Enferno has no build step, so these files
# are committed. Bump a version, run this, then load an admin page in a browser.
set -euo pipefail

VUE_VERSION="3.5.44"
VUETIFY_VERSION="4.3.1"
AXIOS_VERSION="1.21.0"

cd "$(dirname "$0")/enferno/static"
CDN="https://cdn.jsdelivr.net/npm"

fetch() {
  echo "  $2"
  curl -fsSL "$1" -o "$2"
}

fetch "$CDN/vue@$VUE_VERSION/dist/vue.global.prod.js" js/vue.min.js
fetch "$CDN/vuetify@$VUETIFY_VERSION/dist/vuetify.min.js" js/vuetify.min.js
fetch "$CDN/vuetify@$VUETIFY_VERSION/dist/vuetify.min.css" css/vuetify.min.css
fetch "$CDN/axios@$AXIOS_VERSION/dist/axios.min.js" js/axios.min.js
