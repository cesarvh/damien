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

from damien.models.tool_setting import ToolSetting
import simplejson as json
from tests.util import override_config


non_admin_uid = '100'
admin_uid = '200'
unauthorized_uid = '666'


class TestConfigController:
    """Config API."""

    def test_anonymous(self, client):
        """Returns a well-formed response to anonymous user."""
        response = client.get('/api/config')
        assert response.status_code == 200
        data = response.json
        assert data['damienEnv'] == 'test'
        assert data['devAuthEnabled'] is False
        assert data['ebEnvironment'] == 'damien-test'
        assert data['emailTestMode'] is True
        assert data['timezone'] == 'America/Los_Angeles'

    def test_authorized_user(self, app, client, fake_auth):
        """Returns a well-formed response to authorized user."""
        with override_config(app, 'DEVELOPER_AUTH_ENABLED', True):
            fake_auth.login(non_admin_uid)
            response = client.get('/api/config')
            assert response.status_code == 200
            data = response.json
            assert data['damienEnv'] == 'test'
            assert data['devAuthEnabled'] is True
            assert data['ebEnvironment'] == 'damien-test'
            assert data['emailTestMode'] is True
            assert data['timezone'] == 'America/Los_Angeles'

    def test_available_terms(self, app, client, fake_auth):
        fake_auth.login(non_admin_uid)
        response = client.get('/api/config')
        assert response.status_code == 200
        data = response.json
        assert len(data['availableTerms']) == 2
        assert data['availableTerms'][0] == {'id': '2218', 'name': 'Fall 2021'}
        assert data['availableTerms'][1] == {'id': '2222', 'name': 'Spring 2022'}

    def test_current_term(self, app, client, fake_auth):
        fake_auth.login(non_admin_uid)
        response = client.get('/api/config')
        assert response.status_code == 200
        data = response.json
        assert data['currentTermId'] == '2222'
        assert data['termDates']['default']['begin'] == '2022-01-18'
        assert data['termDates']['default']['end'] == '2022-05-06'
        assert data['termDates']['valid']['begin'] == '2022-01-18'
        assert data['termDates']['valid']['end'] == '2022-05-06'


class TestServiceAnnouncement:
    """Tool Settings API."""

    @staticmethod
    def _api_service_announcement(client, expected_status_code=200):
        response = client.get('/api/service_announcement')
        assert response.status_code == expected_status_code
        return response.json

    def test_not_authenticated(self, client):
        """Rejects anonymous user."""
        self._api_service_announcement(client, expected_status_code=401)

    def test_announcement_is_not_live_as_advisor(self, client, fake_auth):
        """Does not return unpublished announcements to users."""
        _update_service_announcement(text='Go to the city of Megiddo', is_live=False)
        fake_auth.login(non_admin_uid)
        assert self._api_service_announcement(client) is None

    def test_announcement_is_not_live_as_admin(self, client, fake_auth):
        """Returns unpublished announcement to admin."""
        text = 'See Bugenhagen before it\'s too late'
        _update_service_announcement(text=text, is_live=False)
        fake_auth.login(admin_uid)
        api_json = self._api_service_announcement(client)
        assert api_json == {
            'text': text,
            'isLive': False,
        }

    def test_announcement_is_live(self, client, fake_auth):
        """All users get the service announcement."""
        text = 'The son of the devil will rise from the world of politics.'
        _update_service_announcement(text=text, is_live=True)
        fake_auth.login(non_admin_uid)
        api_json = self._api_service_announcement(client)
        assert api_json == {
            'text': text,
            'isLive': True,
        }


class TestUpdateAnnouncement:
    """Tool Settings API."""

    @staticmethod
    def _api_update_announcement(client, text, is_live, expected_status_code=200):
        response = client.post(
            '/api/service_announcement/update',
            content_type='application/json',
            data=json.dumps({'text': text, 'isLive': is_live}),
        )
        assert response.status_code == expected_status_code
        return response.json

    def test_not_authenticated(self, client):
        """Rejects anonymous user."""
        self._api_update_announcement(
            client,
            text='Go to the city of Megiddo',
            is_live=True,
            expected_status_code=401,
        )

    def test_not_authorized(self, client, fake_auth):
        """Rejects non-admin user."""
        fake_auth.login(non_admin_uid)
        self._api_update_announcement(
            client,
            text='See Bugenhagen before it\'s too late',
            is_live=True,
            expected_status_code=401,
        )

    def test_update_service_announcement(self, client, fake_auth):
        """Admin can update service announcement."""
        fake_auth.login(admin_uid)
        text = 'The son of the devil will rise from the world of politics.'
        self._api_update_announcement(client, text=text, is_live=True)
        # Verify the update
        response = client.get('/api/service_announcement')
        assert response.status_code == 200
        assert response.json == {
            'text': text,
            'isLive': True,
        }


def _update_service_announcement(text, is_live):
    ToolSetting.upsert('SERVICE_ANNOUNCEMENT_TEXT', text)
    ToolSetting.upsert('SERVICE_ANNOUNCEMENT_IS_LIVE', is_live)
    return {
        'text': text,
        'isLive': is_live,
    }
