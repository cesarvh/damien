<template>
  <div class="ma-0 px-4 pb-4">
    <v-textarea
      id="service-announcement-textarea"
      v-model="text"
      aria-label="Enter service announcement for users to read"
      rows="3"
      max-rows="5"
      hide-details="auto"
      solo
    ></v-textarea>
    <v-checkbox
      id="service-announcement-published"
      v-model="isPublished"
      label="Publish"
    />
    <v-btn
      id="service-announcement-save"
      color="primary"
      :disabled="!$_.trim(text)"
      @click="save"
    >
      Save
    </v-btn>
  </div>
</template>

<script>
import Context from '@/mixins/Context'
import Util from '@/mixins/Util'
import { getServiceAnnouncement, updateServiceAnnouncement } from '@/api/config'
export default {
  name: 'EditServiceAnnouncement',
  mixins: [Context, Util],
  data: () => ({
    isPublished: undefined,
    isSaving: false,
    text: undefined,
  }),
  created() {
    getServiceAnnouncement().then(data => {
      this.text = data.text
      this.isPublished = data.isLive
    })
  },
  methods: {
    save() {
      updateServiceAnnouncement(this.text, this.isPublished).then(data => {
        this.text = data.text
        this.isPublished = data.isLive
      })
    }
  }
}
</script>
