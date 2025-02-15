<template>
  <v-autocomplete
    :id="id"
    v-model="selected"
    :allow-overflow="false"
    :append-icon="null"
    :aria-disabled="disabled"
    :auto-select-first="true"
    :background-color="disabled ? 'disabled' : 'white'"
    class="overflow-x-hidden person-lookup"
    color="white"
    dense
    :disabled="disabled"
    :hide-no-data="true"
    :items="suggestions"
    light
    :loading="isSearching"
    :menu-props="menuProps"
    no-data-text="No results found."
    no-filter
    outlined
    :placeholder="placeholder"
    return-object
    :search-input.sync="search"
    single-line
    hide-details="auto"
  >
    <template #selection>
      <span class="text-nowrap">{{ toLabel(selected) }}</span>
    </template>
    <template #item="data">
      <v-list-item-content class="tertiary--text">
        <span v-html="suggest(data.item)" />
      </v-list-item-content>
    </template>
  </v-autocomplete>
</template>

<script>
import {searchInstructors} from '@/api/instructor'
import {searchUsers} from '@/api/user'

export default {
  name: 'PersonLookup',
  props: {
    disabled: {
      required: false,
      type: Boolean
    },
    excludeUids: {
      default: () => [],
      required: false,
      type: Array
    },
    id: {
      default: 'input-person-lookup-autocomplete',
      required: false,
      type: String
    },
    instructorLookup: {
      required: false,
      type: Boolean
    },
    onSelectResult: {
      default: () => {},
      required: false,
      type: Function
    },
    placeholder: {
      default: 'Name or UID',
      required: false,
      type: String
    }
  },
  data: () => ({
    isSearching: false,
    menuProps: {
      contentClass: 'v-sheet--outlined autocomplete-menu'
    },
    search: undefined,
    searchTokenMatcher: undefined,
    selected: undefined,
    suggestions: undefined
  }),
  watch: {
    search(snippet) {
      this.debouncedSearch(snippet)
    },
    selected(suggestion) {
      this.onSelectResult(suggestion)
    }
  },
  methods: {
    executeSearch(snippet) {
      if (snippet) {
        this.isSearching = true
        const apiSearch = this.instructorLookup ? searchInstructors : searchUsers
        apiSearch(snippet, this.excludeUids).then(results => {
          const searchTokens = this.$_.split(this.$_.trim(snippet), /\W/g)
          this.searchTokenMatcher = RegExp(this.$_.join(searchTokens, '|'), 'gi')
          this.suggestions = results
          this.isSearching = false
        })
      } else {
        this.searchTokenMatcher = null
        this.suggestions = []
      }
    },
    suggest(user) {
      return this.toLabel(user).replace(this.searchTokenMatcher, match => `<strong>${match}</strong>`)
    },
    toLabel(user) {
      return `${user.firstName} ${user.lastName} (${user.uid})`
    }
  },
  created() {
    this.debouncedSearch = this.$_.debounce(this.executeSearch, 300)
  }
}
</script>

<style>
.autocomplete-menu {
  z-index: 203 !important;
}
.person-lookup.v-input--is-focused {
  appearance: auto !important;
  caret-color: #000 !important;
  color: -webkit-focus-ring-color !important;
  outline: auto !important;
  outline-color: -webkit-focus-ring-color !important;
  outline-offset: 0px !important;
  outline-style: auto !important;
  outline-width: 1px !important;
}
</style>