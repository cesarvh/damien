<template>
  <div class="pt-2">
    <v-row class="pb-2" no-gutters>
      <v-col cols="12" lg="9" class="d-flex align-baseline">
        <h1 v-if="$_.get(department, 'deptName')" id="page-title">
          {{ department.deptName }}&MediumSpace;
          <span v-if="department.catalogListings">
            ({{ $_.compact($_.keys(department.catalogListings)).join(', ') }})&MediumSpace;
          </span>
          <span v-if="selectedTermName"> - {{ selectedTermName }}</span>
        </h1>
      </v-col>
      <v-col cols="12" lg="3">
        <TermSelect :after-select="refresh" />
      </v-col>
    </v-row>
    <v-container v-if="!loading" class="mx-0 px-0 pb-6" fluid>
      <v-row justify="start">
        <v-col cols="12" md="5">
          <v-expansion-panels v-model="contactsPanel" disable-icon-rotate flat>
            <v-expansion-panel class="panel-override">
              <template #default>
                <div class="d-flex" :class="$currentUser.isAdmin ? 'flex-column' : 'align-center justify-space-between flex-wrap'">
                  <h2 class="pb-1 px-2">Department Contacts</h2>
                  <div class="d-flex height-unset" :class="{'flex-column': isCreatingNotification, 'align-center justify-space-between': !isCreatingNotification}">
                    <v-btn
                      v-if="$currentUser.isAdmin && !isCreatingNotification"
                      id="open-notification-form-btn"
                      class="ma-2 secondary text-capitalize"
                      :disabled="disableControls || $_.isEmpty(contacts)"
                      @click="() => isCreatingNotification = true"
                    >
                      Send notification
                    </v-btn>
                    <NotificationForm
                      v-if="$currentUser.isAdmin && isCreatingNotification"
                      :after-send="afterSendNotification"
                      :on-cancel="cancelSendNotification"
                      :recipients="[notificationRecipients]"
                    />
                    <v-expansion-panel-header
                      class="w-fit-content ml-auto mr-3"
                      hide-actions
                      text
                      @click="collapseAllContacts"
                    >
                      <template #default="{open}">
                        <span v-if="!open">
                          Expand
                          <v-icon class="rotate-180 ml-1">mdi-plus-box-multiple-outline</v-icon>
                        </span>
                        <span v-if="open">
                          Collapse All
                          <v-icon class="rotate-180 ml-1">mdi-minus-box-multiple-outline</v-icon>
                        </span>
                      </template>
                    </v-expansion-panel-header>
                  </div>
                </div>
                <v-expansion-panel-content class="panel-content-override">
                  <v-expansion-panels
                    v-model="contactDetailsPanel"
                    flat
                    focusable
                    hover
                    multiple
                    tile
                  >
                    <DepartmentContact
                      v-for="(contact, index) in contacts"
                      :key="contact.id"
                      :contact="contact"
                      :index="index"
                      :is-expanded="$_.includes(contactDetailsPanel, index)"
                    />
                  </v-expansion-panels>
                </v-expansion-panel-content>
              </template>
            </v-expansion-panel>
          </v-expansion-panels>
          <v-btn
            v-if="$currentUser.isAdmin && !isAddingContact"
            id="add-dept-contact-btn"
            class="text-capitalize pl-2 my-1 mx-2"
            color="tertiary"
            text
            @click="() => isAddingContact = true"
            @keypress.enter.prevent="() => isAddingContact = true"
          >
            <v-icon>mdi-plus-thick</v-icon>
            Add Contact
          </v-btn>
          <EditDepartmentContact
            v-if="$currentUser.isAdmin && isAddingContact"
            :id="`add-department-contact`"
            :after-save="afterSaveContact"
            :on-cancel="onCancelAddContact"
          />
        </v-col>
        <v-col cols="12" md="7">
          <DepartmentNote />
        </v-col>
      </v-row>
    </v-container>
    <v-container v-if="!loading" class="mx-0 px-0 pb-6" fluid>
      <v-card outlined class="elevation-1">
        <EvaluationTable />
      </v-card>
    </v-container>
  </div>
</template>

<script>
import Context from '@/mixins/Context.vue'
import DepartmentContact from '@/components/admin/DepartmentContact'
import DepartmentEditSession from '@/mixins/DepartmentEditSession'
import DepartmentNote from '@/components/admin/DepartmentNote'
import EditDepartmentContact from '@/components/admin/EditDepartmentContact'
import EvaluationTable from '@/components/evaluation/EvaluationTable'
import NotificationForm from '@/components/admin/NotificationForm'
import TermSelect from '@/components/util/TermSelect'

export default {
  name: 'Department',
  components: {
    DepartmentContact,
    DepartmentNote,
    EditDepartmentContact,
    EvaluationTable,
    NotificationForm,
    TermSelect
  },
  mixins: [Context, DepartmentEditSession],
  data: () => ({
    contactDetailsPanel: [],
    contactsPanel: undefined,
    isAddingContact: false,
    isCreatingNotification: false,
  }),
  computed: {
    notificationRecipients() {
      return {
        'deptName': this.department.deptName,
        'deptId': this.department.id,
        'recipients': this.$_.filter(this.contacts, 'canReceiveCommunications')
      }
    }
  },
  methods: {
    afterSaveContact() {
      this.isAddingContact = false
      this.alertScreenReader('Contact saved.')
      this.$putFocusNextTick('add-dept-contact-btn')
    },
    afterSendNotification() {
      this.isCreatingNotification = false
      this.snackbarOpen('Notification sent.')
      this.$putFocusNextTick('open-notification-form-btn')
    },
    cancelSendNotification() {
      this.isCreatingNotification = false
      this.alertScreenReader('Notification canceled.')
    },
    collapseAllContacts() {
      if (this.contactsPanel === 0) {
        this.contactDetailsPanel = []
      }
    },
    onCancelAddContact() {
      this.isAddingContact = false
      this.alertScreenReader('Canceled. Nothing saved.')
      this.$putFocusNextTick('add-dept-contact-btn')
    },
    refresh() {
      this.$loading()
      this.alertScreenReader(`Loading ${this.selectedTermName}`)
      const departmentId = this.$_.get(this.$route, 'params.departmentId')
      this.init(departmentId).then(department => {
        this.$ready(`${department.deptName} ${this.selectedTermName}`)
      })
    }
  }
}
</script>

<style scoped>
.w-fit-content {
  width: fit-content;
}
</style>

<style>
.panel-content-override>.v-expansion-panel-content__wrap {
  padding: 0 !important;
}
.panel-override {
  background-color: unset !important;

}
</style>