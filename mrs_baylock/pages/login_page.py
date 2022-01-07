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

from flask import current_app as app
from mrs_baylock.pages.page import Page
from mrs_baylock.test_utils import utils
from selenium.webdriver.common.by import By


class LoginPage(Page):

    SIGN_IN_BUTTON = (By.ID, 'todo')
    USERNAME_INPUT = (By.ID, 'todo')
    PASSWORD_INPUT = (By.ID, 'todo')
    DEV_AUTH_LOGIN_BUTTON = (By.ID, 'todo')

    def load_page(self):
        app.logger.info('Loading the Damien login page')
        self.driver.get(app.config['BASE_URL'])
        self.wait_for_title('Some Title')

    def click_sign_in(self):
        self.wait_for_page_and_click(LoginPage.SIGN_IN_BUTTON)

    def dev_auth(self, uid=None):
        if not uid:
            uid = utils.get_admin_uid()
        app.logger.info(f'Logging in to Damien as UID {uid}')
        self.wait_for_element_and_type(LoginPage.USERNAME_INPUT, uid)
        self.wait_for_element_and_type(LoginPage.PASSWORD_INPUT, app.config['DEV_AUTH_PASSWORD'])
        self.wait_for_element_and_click(LoginPage.DEV_AUTH_LOGIN_BUTTON)
