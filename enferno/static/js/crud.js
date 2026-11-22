/**
 * Shared behavior for admin data tables: server-side paging, sorting and search,
 * the edit dialog, and delete. List endpoints answer through table_response() in
 * enferno/utils/tables.py, so the query parameters here match it.
 *
 *   mixins: [layoutMixin, crudMixin({list: '/api/users', item: '/api/user/'})]
 *
 * A page supplies its headers and dialog fields. `item` is only needed for
 * editable tables; `newItem` returns the blank record the create dialog starts with.
 */
function crudMixin({list, item, newItem = () => ({})}) {
  return {
    data() {
      return {
        items: [],
        itemsLength: 0,
        loading: true,
        saving: false,
        search: '',
        options: {page: 1, itemsPerPage: 25, sortBy: []},
        listRequest: 0,
        edialog: false,
        eitem: newItem(),
      };
    },
    methods: {
      refresh(options) {
        if (options) this.options = options;
        const {page, itemsPerPage, sortBy} = this.options;
        const params = {page, per_page: itemsPerPage};
        if (this.search) params.q = this.search;
        if (sortBy?.length) {
          params.sort_by = sortBy[0].key;
          params.sort_desc = sortBy[0].order === 'desc';
        }
        // Only the latest request may update the table; a slower, older one is ignored
        const request = ++this.listRequest;
        this.loading = true;
        axios.get(list, {params})
          .then(res => {
            if (request !== this.listRequest) return;
            this.items = res.data.items;
            this.itemsLength = res.data.total;
          })
          .catch(err => {
            if (request === this.listRequest) this.notify(err.response?.data?.message || 'Failed to load the list');
          })
          .finally(() => {
            if (request === this.listRequest) this.loading = false;
          });
      },

      createItem() {
        this.eitem = newItem();
        this.edialog = true;
      },

      editItem(row) {
        // Edit a copy: the table row changes only after the server accepts the save
        this.eitem = structuredClone(Vue.toRaw(row));
        this.edialog = true;
      },

      async saveItem() {
        if (this.saving) return;
        this.saving = true;
        try {
          const res = await axios.post(item + (this.eitem.id || ''), {item: this.eitem});
          this.edialog = false;
          this.notify(res.data.message);
          this.refresh();
        } catch (err) {
          // The dialog stays open so a failed save keeps what the user typed
          this.notify(err.response?.data?.message || 'Save failed');
        } finally {
          this.saving = false;
        }
      },

      async deleteItem(row, label) {
        if (!await this.confirmAction(`Delete ${label}? This cannot be undone.`)) return;
        try {
          const res = await axios.delete(item + row.id);
          this.notify(res.data.message);
          this.refresh();
        } catch (err) {
          this.notify(err.response?.data?.message || 'Delete failed');
        }
      },
    },
  };
}
