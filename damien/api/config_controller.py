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

from damien.api.errors import BadRequestError
from damien.api.util import admin_required
from damien.lib.berkeley import available_term_ids, term_name_for_sis_id
from damien.lib.http import tolerant_jsonify
from damien.lib.queries import get_default_meeting_dates, get_valid_meeting_dates
from damien.lib.util import safe_strftime, to_bool_or_none
from damien.models.tool_setting import ToolSetting
from flask import current_app as app, request
from flask_login import current_user, login_required


@app.route('/api/config')
def app_config():
    def _term_feed(term_id):
        return {'id': term_id, 'name': term_name_for_sis_id(term_id)}
    default_start, default_end = get_default_meeting_dates(app.config['CURRENT_TERM_ID'])
    valid_start, valid_end = get_valid_meeting_dates(app.config['CURRENT_TERM_ID'])
    return tolerant_jsonify({
        'availableTerms': [_term_feed(term_id) for term_id in available_term_ids()],
        'currentTermId': app.config['CURRENT_TERM_ID'],
        'currentTermName': term_name_for_sis_id(app.config['CURRENT_TERM_ID']),
        'damienEnv': app.config['DAMIEN_ENV'],
        'devAuthEnabled': app.config['DEVELOPER_AUTH_ENABLED'],
        'easterEggMonastery': app.config['EASTER_EGG_MONASTERY'],
        'easterEggNannysRoom': app.config['EASTER_EGG_NANNYSROOM'],
        'ebEnvironment': app.config['EB_ENVIRONMENT'] if 'EB_ENVIRONMENT' in app.config else None,
        'emailSupport': app.config['EMAIL_COURSE_EVALUATION_ADMIN'],
        'emailTestMode': app.config['EMAIL_TEST_MODE'],
        'termDates': {
            'default': {
                'begin': safe_strftime(default_start, '%Y-%m-%d'),
                'end': safe_strftime(default_end, '%Y-%m-%d'),
            },
            'valid': {
                'begin': safe_strftime(valid_start, '%Y-%m-%d'),
                'end': safe_strftime(valid_end, '%Y-%m-%d'),
            },
        },
        'timezone': app.config['TIMEZONE'],
    })


@app.route('/api/service_announcement')
@login_required
def get_service_announcement():
    announcement = _get_service_announcement()
    return tolerant_jsonify(announcement if current_user.is_admin or announcement['isLive'] else None)


@app.route('/api/service_announcement/update', methods=['POST'])
@admin_required
def update_service_announcement():
    params = request.get_json()
    text = params.get('text')
    is_live = to_bool_or_none(params.get('isLive'))
    if not text or is_live is None:
        raise BadRequestError('API requires \'text\' and \'isLive\'')
    _update_service_announcement(text, is_live)
    return tolerant_jsonify(_get_service_announcement())


def _get_service_announcement():
    is_live = ToolSetting.get_tool_setting('SERVICE_ANNOUNCEMENT_IS_LIVE')
    is_live = False if is_live is None else to_bool_or_none(is_live)
    return {
        'text': ToolSetting.get_tool_setting('SERVICE_ANNOUNCEMENT_TEXT'),
        'isLive': is_live,
    }


def _update_service_announcement(text, is_live):
    ToolSetting.upsert('SERVICE_ANNOUNCEMENT_TEXT', text)
    ToolSetting.upsert('SERVICE_ANNOUNCEMENT_IS_LIVE', is_live)
