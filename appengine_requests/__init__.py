__version__ = "0.0.1"

import hashlib
import os

from urlparse import urlsplit

import requests


SECURE_SCHEMA = "https://"
AUTH_TOKEN_FLAG = "Auth"
AUTH_SID = "SID"
AUTHED_SID = "ACSID"
S_AUTHED_SID = "SACSID"
APPCFG_LOGIN_PATH = "APPCFG_LOGIN_PATH"
PATH = "/"
DEV_LOGIN = "dev_appserver_login"


class UnableToAuthenticate(Exception):
    pass


class AppEngineRequest(object):

    def __init__(self, **kwargs):
        """Initalize the AppEngineRequest request, set the arguments passed in
        and the defaults for those that aren't.

        :param options: :class: `Args`
        """
        self.options = kwargs.get('options')
        self.email = kwargs.get('email', "")
        self.password = kwargs.get("password", "")
        self.appid = kwargs.get('appid')
        self.url = kwargs.get('url')
        self.secure = kwargs.get('use_ssl')
        self.source = kwargs.get("source", "")
        self.auth_server_url = kwargs.get("auth_server_url", "www.google.com")
        self.auth_server_login = kwargs.get(
            "auth_server_login", "/accounts/ClientLogin")
        self.account_type = kwargs.get("account_type", "HOSTED_OR_GOOGLE")
        self.auth_service = kwargs.get("auth_service", "ah")
        self.continue_location = kwargs.get(
            "continue_location", "http://localhost")
        self.login_path = kwargs.get("login_path", "/_ah")
        self.login_domain = kwargs.get("login_domain", "localhost")
        self.sid = None
        self.scheme = None
        self.netloc = None
        self.domain = None
        self.full_url = ""

    def build_url(self):
        """Build a url based off the appid, url and ssl properties."""

        self.scheme = "https" if self.secure else "http"
        self.netloc = ""
        path = ""

        if self.url:
            parsed_url = urlsplit(self.url)
            self.netloc = parsed_url.netloc
            path = parsed_url.path
            self.domain = parsed_url.hostname
            if parsed_url.scheme:
                self.scheme = parsed_url.scheme

        if not self.netloc:
            if not self.appid:
                self.domain = "localhost"
            else:
                self.domain = self.appid.strip("s~")

                if not self.appid.endswith(".appspot.com"):
                    self.domain += ".appspot.com"

        path = "%s/%s" % (self.domain, path)
        self.netloc = path.replace("//", "/")

        self.full_url = "%s://%s" % (self.scheme, self.netloc)

        return self.full_url

    def run(self, url=None, is_admin=False):
        """Run the url either passed in or from the attributes."""
        self.url = url
        url = self.build_url()

        cookies = {"PATH": PATH}

        # need to check if hitting local or appspot.
        if self.domain == "localhost":
            cookies[DEV_LOGIN] = self.dev_create_cookie_data(is_admin)
        else:
            self.auth_token = self.get_auth_token()
            authenticated_sid = self.verify_token(self.auth_token)

            cookies[AUTHED_SID] = authenticated_sid
            cookies[S_AUTHED_SID] = authenticated_sid

        return cookies

    def get(self, url=None, is_admin=False):
        cookies = self.run(url, is_admin)
        req = requests.get(url, cookies=cookies)

        return req.text

    def post(self, url=None, is_admin=False, payload=None):
        cookies = self.run(url, is_admin)
        req = requests.post(url, cookies=cookies, data=payload)

        return req.text

    def get_auth_token(self):
        """Take the user name and password and get an authentication token to
        be used in the services.

        If the session id is found in the response it will set it as well.

        :return: :class: `str` Auth Token
        """
        data = {
            "Email": self.email,
            "Passwd": self.password,
            "service": self.auth_service,
            "source": self.source,
            "accountType": self.account_type
        }

        url = "%s%s%s" % (SECURE_SCHEMA, self.auth_server_url,
                          self.auth_server_login)
        r = requests.post(url, data=data)
        text = r.text

        if not text:
            raise UnableToAuthenticate()

        response_dict = dict(x.split("=") for x in text.split("\n") if x)

        if not response_dict or not AUTH_TOKEN_FLAG in response_dict:
            raise UnableToAuthenticate()

        self.sid = response_dict.get(AUTH_SID)

        return response_dict[AUTH_TOKEN_FLAG]

    def verify_token(self, auth_token):
        """Take a token and verify it against an appspots login path. Return
        the ACSID found on the cooike for that request.

        :return: :class: `str` ASCID
        """
        args = {"continue": self.continue_location, "auth": auth_token}
        login_path = os.environ.get(APPCFG_LOGIN_PATH, self.login_path)

        url = "%s://%s%s/login" % (self.scheme, self.domain, login_path)

        cookies = {
            AUTH_SID: self.sid,
            PATH: "/"
        }

        # TODO: verfiy that this request comes back correctly
        req = requests.get(url, params=args, cookies=cookies,
                           allow_redirects=False)

        token = req.cookies.get(AUTHED_SID)
        if not token:
            return req.cookies.get(S_AUTHED_SID)

    def dev_create_cookie_data(self, admin):
        """Create the cookie data for hitting the development server.

        :return: :class: `str`
        """
        admin_string = 'True' if admin else 'False'
        user_id = ''

        if not self.email:
            return None

        user_id_digest = hashlib.md5(self.email.lower()).digest()
        user_id = '1' + ''.join(['%02d' % ord(x) for x in user_id_digest])[:20]

        return "%s:%s:%s" % (self.email, admin_string, user_id)
