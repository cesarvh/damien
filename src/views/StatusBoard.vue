<template>
  <div class="pt-2">
    <v-row class="pb-2" no-gutters>
      <v-col cols="12" md="9" class="d-flex align-baseline">
        <h1 id="page-title">Evaluation Status Dashboard - {{ selectedTermName }}</h1>
      </v-col>
      <v-col cols="12" md="3">
        <TermSelect :after-select="refresh" />
      </v-col>
    </v-row>
    <v-card outlined class="elevation-1">
      <v-data-table
        id="department-table"
        disable-pagination
        :disable-sort="loading"
        :headers="headers"
        :header-props="{'every-item': true, 'some-items': true}"
        hide-default-footer
        :items="departments"
        show-select
      >
        <template #header.data-table-select>
          <div class="d-flex flex-row notify-all">
            <v-simple-checkbox
              id="checkbox-select-dept-all"
              aria-label="Select all department rows"
              :disabled="loading"
              :indeterminate="someDepartmentsSelected"
              :ripple="false"
              :value="allDepartmentsSelected"
              @input="toggleSelectAll"
            ></v-simple-checkbox>
            <div class="d-flex align-center">Send notification</div>
            <v-btn
              v-if="!isCreatingNotification"
              id="open-notification-form-btn"
              class="ma-2 secondary text-capitalize"
              color="secondary"
              :disabled="$_.isEmpty(selectedDepartmentIds) || loading"
              small
              @click="() => isCreatingNotification = true"
              @keypress.enter.prevent="() => isCreatingNotification = true"
            >
              Apply
            </v-btn>
          </div>
        </template>
        <template #body="{items}">
          <tbody>
            <template v-for="(department, index) in items">
              <tr :id="`department-${index}`" :key="department.name">
                <td>
                  <v-simple-checkbox
                    :id="`checkbox-select-dept-${$_.kebabCase(department.deptName)}`"
                    :disabled="loading"
                    :ripple="false"
                    :value="isSelected(department)"
                    @input="toggleSelect(department)"
                  ></v-simple-checkbox>
                </td>
                <td class="department-name">
                  <div class="d-flex align-top">
                    <router-link :id="`link-to-dept-${$_.kebabCase(department.deptName)}`" :to="`/department/${department.id}`">
                      {{ department.deptName }}
                      ({{ $_.compact($_.keys(department.catalogListings)).join(', ') }})
                    </router-link>
                  </div>
                </td>
                <td :id="`last-updated-dept-${department.id}`" class="department-lastUpdated">
                  {{ department.updatedAt | moment('MMM D, YYYY h:mma') }}
                </td>
                <td class="department-errors">
                  <v-chip
                    v-if="department.totalInError"
                    :id="`errors-count-dept-${department.id}`"
                    class="error error--text error-count"
                    outlined
                    small
                  >
                    {{ department.totalInError }} <span class="sr-only">errors</span>
                  </v-chip>
                  <v-icon
                    v-if="!department.totalInError"
                    aria-hidden="false"
                    aria-label="no errors"
                    class="success--text"
                    role="img"
                  >
                    mdi-check-circle
                  </v-icon>
                </td>
                <td class="department-confirmed">
                  <v-icon
                    v-if="department.totalConfirmed > 0 && department.totalConfirmed === department.totalEvaluations"
                    aria-hidden="false"
                    aria-label="all confirmed"
                    class="success--text"
                    role="img"
                  >
                    mdi-check-circle
                  </v-icon>
                  <span v-if="department.totalConfirmed === 0 || department.totalConfirmed < department.totalEvaluations">
                    <span aria-hidden="true">{{ department.totalConfirmed }} / {{ department.totalEvaluations }}</span>
                    <span class="sr-only">{{ department.totalConfirmed }} of {{ department.totalEvaluations }} confirmed</span>
                  </span>
                </td>
                <td class="department-note">
                  <pre class="body-2 text-condensed truncate-with-ellipsis">{{ $_.get(department, 'note.note') }}</pre>
                </td>
              </tr>
            </template>
          </tbody>
        </template>
      </v-data-table>
    </v-card>
    <v-dialog v-model="isCreatingNotification" width="600">
      <NotificationForm
        v-if="isCreatingNotification"
        :after-send="afterSendNotification"
        :on-cancel="cancelSendNotification"
        :recipients="notificationRecipients"
      />
    </v-dialog>
  </div>
</template>

<script>
import {getDepartmentsEnrolled} from '@/api/departments'
import Context from '@/mixins/Context'
import NotificationForm from '@/components/admin/NotificationForm'
import TermSelect from '@/components/util/TermSelect'

export default {
  name: 'StatusBoard',
  components: {NotificationForm, TermSelect},
  mixins: [Context],
  data: () => ({
    blockers: {},
    departments: [],
    headers: [],
    isCreatingNotification: false,
    isExporting: false,
    selectedDepartmentIds: []
  }),
  computed: {
    allDepartmentsSelected() {
      return !!(this.$_.size(this.selectedDepartmentIds) && this.$_.size(this.selectedDepartmentIds) === this.$_.size(this.departments))
    },
    notificationRecipients() {
      let recipients = []
      this.$_.each(this.departments, d => {
        if (this.isSelected(d)) {
          const departmentRecipients = this.$_.filter(d.contacts, 'canReceiveCommunications')
          if (departmentRecipients.length) {
            recipients.push({
              'deptId': d.id,
              'deptName': d.deptName,
              'recipients': this.$_.filter(d.contacts, 'canReceiveCommunications')
            })
          }
        }
      })
      return recipients
    },
    someDepartmentsSelected() {
      return !!(this.$_.size(this.selectedDepartmentIds) && this.$_.size(this.selectedDepartmentIds) < this.$_.size(this.departments))
    }
  },
  created() {
    this.headers = [
      {class: 'text-nowrap pt-12 pb-3', text: 'Department', value: 'deptName', width: '50%'},
      {class: 'text-nowrap pt-12 pb-3', text: 'Last Updated', value: 'updatedAt', width: '20%'},
      {class: 'text-nowrap pt-12 pb-3', text: 'Errors', value: 'totalInError', width: '10%'},
      {class: 'text-nowrap pt-12 pb-3', text: 'Confirmed', value: 'totalConfirmed', width: '10%'},
      {
        class: 'text-nowrap pt-12 pb-3',
        sort: (a, b) => {
          const deptANote = this.$_.get(a, `${this.selectedTermId}.note`)
          const deptBNote = this.$_.get(b, `${this.selectedTermId}.note`)
          // Nulls last
          return deptANote && deptBNote ? deptANote.localeCompare(deptBNote) : !deptANote - !deptBNote
        },
        text: 'Notes',
        value: 'notes',
        width: '30%'
      },
    ]
  },
  methods: {
    afterSendNotification() {
      this.selectedDepartmentIds = []
      this.isCreatingNotification = false
      this.alertScreenReader('Notification sent.')
      this.$putFocusNextTick('open-notification-form-btn')
    },
    cancelSendNotification() {
      this.isCreatingNotification = false
      this.alertScreenReader('Notification canceled.')
      this.$putFocusNextTick('open-notification-form-btn')
    },
    isSelected(department) {
      return this.$_.includes(this.selectedDepartmentIds, department.id)
    },
    loadBlockers() {
      this.blockers = {}
      this.$_.each(this.departments, d => {
        if (d.totalBlockers) {
          this.blockers[d.deptName] = d.totalBlockers
        }
      })
    },
    refresh() {
      this.$loading()
      this.alertScreenReader(`Loading ${this.selectedTermName}`)
      this.departments = []
      getDepartmentsEnrolled(false, false, true, this.selectedTermId).then(data => {
        this.departments = data
        this.loadBlockers()
        this.$ready(`Evaluation Status Dashboard for ${this.selectedTermName}`)
      })
    },
    toggleSelect(department) {
      const index = this.$_.indexOf(this.selectedDepartmentIds, department.id)
      if (index === -1) {
        this.selectedDepartmentIds.push(department.id)
      } else {
        this.selectedDepartmentIds.splice(index, 1)
      }
    },
    toggleSelectAll() {
      if (this.allDepartmentsSelected) {
        this.selectedDepartmentIds = []
      } else {
        this.selectedDepartmentIds = this.$_.map(this.departments, 'id')
      }
    }
  }
}
</script>

<style scoped>
.department-confirmed {
  min-width: 100px;
}
.department-errors {
  min-width: 80px;
}
.department-lastUpdated {
  min-width: 130px;
}
.department-name {
  min-width: 250px;
}
.department-note {
  max-width: 400px;
}
.error-count {
  border-width: 2px;
  font-weight: bold;
  padding: 0 7px;
}
.notify-all {
  position: absolute;
  top: 0;
}
</style>
