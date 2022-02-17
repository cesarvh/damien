"""
Copyright ©2022. The Regents of the University of California (Regents). All Rights Reserved.

Permission to use, copy, modify, and distribute this software and its documentation
for educational, research, and not-for-profit purposes, without fee and without a
signed licensing agreement, is hereby granted, provided that the above copyright
notice, this paragraph and the following two paragraphs appear in all copies,
modifications, and distributions.

Contact The Office of Technology Licensing, UC Berkeley, 2150 Shattuck Avenue,
Suite 510, Berkeley, CA 94720-1620, (510) 643-7201, otl@berkeley.edu,
http://ipira.berkeley.edu/industry-info for commercial licensing opportunities.

IN NO EVENT SHALL REGENTS BE LIABLE TO ANY PARTY FOR DIRECT, INDIRECT, SPECIAL,
INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING LOST PROFITS, ARISING OUT OF
THE USE OF THIS SOFTWARE AND ITS DOCUMENTATION, EVEN IF REGENTS HAS BEEN ADVISED
OF THE POSSIBILITY OF SUCH DAMAGE.

REGENTS SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. THE
SOFTWARE AND ACCOMPANYING DOCUMENTATION, IF ANY, PROVIDED HEREUNDER IS PROVIDED
"AS IS". REGENTS HAS NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES,
ENHANCEMENTS, OR MODIFICATIONS.
"""

from itertools import groupby
import re

from damien.models.evaluation import Evaluation


class Section:

    def __init__(
        self,
        loch_rows,
        evaluations,
        instructors,
        catalog_listings=None,
        evaluation_type_cache=None,
    ):
        self.term_id = loch_rows[0].term_id
        self.course_number = loch_rows[0].course_number
        self.subject_area = loch_rows[0].subject_area
        self.catalog_id = loch_rows[0].catalog_id
        self.instruction_format = loch_rows[0].instruction_format
        self.section_num = loch_rows[0].section_num
        self.course_title = loch_rows[0].course_title

        self.instructors = instructors
        self.merged_evaluations = []

        default_form = None
        for c in catalog_listings:
            if c.subject_area in (self.subject_area, '') and (c.catalog_id is None or re.match(c.catalog_id, self.catalog_id)):
                default_form = c.default_form
                break

        # Multiple loch rows for a single section-instructor pairing are possible.
        loch_rows_by_instructor_uid = {k: list(v) for k, v in groupby(loch_rows, key=lambda r: r['instructor_uid'])}
        evaluation_uids = set()

        # Create one API feed element per visible saved evaluation, merging in data from SIS as needed.
        for evaluation in evaluations:
            evaluation_uids.add(evaluation.instructor_uid)
            if not evaluation.is_visible():
                continue
            # When merging evaluation data for a specific instructor, we prefer in order: 1) loch rows for that specific
            # instructor; 2) loch rows with no instructor; 3) any loch rows available.
            loch_rows_for_uid = loch_rows_by_instructor_uid.get(evaluation.instructor_uid) or loch_rows_by_instructor_uid.get(None) or loch_rows
            self.merged_evaluations.append(Evaluation.merge_transient(
                evaluation.instructor_uid,
                loch_rows_for_uid,
                evaluation,
                self.instructors.get(evaluation.instructor_uid),
                default_form=default_form,
                evaluation_type_cache=evaluation_type_cache,
            ))

        # Supplement with SIS-only rows.
        for instructor_uid, loch_rows_for_uid in loch_rows_by_instructor_uid.items():
            # Ignore instructor UIDs already handled under saved evaluations.
            if instructor_uid in evaluation_uids:
                continue
            # Ignore rows without an instructor unless we have no saved evaluations.
            if instructor_uid is None and len(evaluations):
                continue
            self.merged_evaluations.append(Evaluation.merge_transient(
                instructor_uid,
                loch_rows_for_uid,
                None,
                self.instructors.get(instructor_uid),
                default_form=default_form,
                evaluation_type_cache=evaluation_type_cache,
            ))

    @classmethod
    def is_visible_by_default(cls, loch_row):
        return (
            loch_row.enrollment_count
            and loch_row.instructor_role_code != 'ICNT'
            and loch_row.instruction_format not in {'CLC', 'GRP', 'IND', 'SUP', 'VOL'}
        )

    def to_api_json(self):
        return {
            'termId': self.term_id,
            'courseNumber': self.course_number,
            'subjectArea': self.subject_area,
            'catalogId': self.catalog_id,
            'instructionFormat': self.instruction_format,
            'sectionNumber': self.section_num,
            'courseTitle': self.course_title,
        }

    def get_evaluation_feed(self, evaluation_ids=None):
        return [e.to_api_json(section=self) for e in self.merged_evaluations if not evaluation_ids or e.get_id() in evaluation_ids]
