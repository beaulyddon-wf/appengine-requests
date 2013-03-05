import unittest

from mock import Mock, patch

from appengine_requests import AppEngineRequest
from appengine_requests import UnableToAuthenticate


class InitAppEngineRequestTestCase(unittest.TestCase):

    def test_no_options_passed_in(self):
        """Ensure that if no options are passed in that all defaults are setup
        correctly.
        """
        gae_req = AppEngineRequest()

        self.assertIsNone(gae_req.options)
        self.assertEqual(gae_req.email, "")
        self.assertEqual(gae_req.password, "")
        self.assertIsNone(gae_req.appid)
        self.assertIsNone(gae_req.url)
        self.assertIsNone(gae_req.secure)
        self.assertEqual(gae_req.source, "")
        self.assertEqual(gae_req.account_type, 'HOSTED_OR_GOOGLE')
        self.assertEqual(gae_req.auth_server_url, 'www.google.com')
        self.assertEqual(gae_req.auth_server_login, '/accounts/ClientLogin')


class BuildUrlAppEngineRequestTestCase(unittest.TestCase):

    def test_no_url_or_appid_passed_in_and_not_ssl(self):
        """Ensure that if no url or appid are passed in that the default url
        is set to localhost. And with no ssl it's set to http.
        """
        gae_req = AppEngineRequest()

        url = gae_req.build_url()

        self.assertEqual(url, "http://localhost/")

    def test_no_url_or_appid_passed_in_and_is_ssl(self):
        """Ensure that if no url or appid are passed in that the default url
        is set to localhost. And with ssl it's set to https.
        """
        gae_req = AppEngineRequest(use_ssl=True)

        url = gae_req.build_url()

        self.assertEqual(url, "https://localhost/")

    def test_no_url_with_non_hrd_not_full_domain_appid_passed_in(self):
        """Ensure that no url with an appid that has no s~ and no .appspot.com
        builds the correct GAE domain.
        """
        gae_req = AppEngineRequest(appid="test")

        url = gae_req.build_url()

        self.assertEqual(url, "http://test.appspot.com/")

    def test_no_url_with_non_hrd_not_domain_appid_passed_in(self):
        """Ensure that no url with an appid that has no s~ but with
        .appspot.com builds the correct GAE domain.
        """
        gae_req = AppEngineRequest(appid="test.appspot.com")

        url = gae_req.build_url()

        self.assertEqual(url, "http://test.appspot.com/")

    def test_no_url_with_hrd_not_full_domain_appid_passed_in(self):
        """Ensure that no url with an appid that has s~ and no .appspot.com
        builds the correct GAE domain.
        """
        gae_req = AppEngineRequest(appid="s~test")

        url = gae_req.build_url()

        self.assertEqual(url, "http://test.appspot.com/")

    def test_no_url_with_hrd_and_full_domain_appid_passed_in(self):
        """Ensure that no url with an appid that has s~ and .appspot.com
        builds the correct GAE domain.
        """
        gae_req = AppEngineRequest(appid="s~test.appspot.com")

        url = gae_req.build_url()

        self.assertEqual(url, "http://test.appspot.com/")

    def test_full_url_with_no_appid_or_ssl(self):
        """Ensure that a full url with no appid or ssl matches the url passed
        in.
        """
        gae_req = AppEngineRequest(url="http://test.appspot.com")

        url = gae_req.build_url()

        self.assertEqual(url, "http://test.appspot.com/")

    def test_full_url_with_no_appid_but_has_ssl(self):
        """Ensure that a full url with no appid but has ssl still  matches
        the url passed in.
        """
        gae_req = AppEngineRequest(url="http://test.appspot.com", use_ssl=True)

        url = gae_req.build_url()

        self.assertEqual(url, "http://test.appspot.com/")

    def test_full_url_with_appid_but_has_ssl(self):
        """Ensure that a full url with appid or ssl still  matches the url
        passed in.
        """
        gae_req = AppEngineRequest(url="http://test.appspot.com", appid="foo")

        url = gae_req.build_url()

        self.assertEqual(url, "http://test.appspot.com/")

    def test_url_missing_scheme_with_no_appid_sets_local(self):
        """Ensure that a url with no scheme and no appid appends the url to
        a localhost url.
        """
        gae_req = AppEngineRequest(url="foo")

        url = gae_req.build_url()

        self.assertEqual(url, "http://localhost/foo")

    def test_home_url_with_no_appid(self):
        """Ensure that a / url with no appid appends / to the local url."""
        gae_req = AppEngineRequest(url="/")

        url = gae_req.build_url()

        self.assertEqual(url, "http://localhost/")

    def test_url_with_appid(self):
        """Ensure that an url with an appid appends / to the appid url."""
        gae_req = AppEngineRequest(url="/foo", appid="test")

        url = gae_req.build_url()

        self.assertEqual(url, "http://test.appspot.com/foo")


class GetAuthTokenAppEngineRequestTestCase(unittest.TestCase):

    @patch("appengine_requests.requests.post")
    def test_empty_request_returns_empty(self, request_post):
        """Ensure that if the request returns empty that the proper exception
        is raised.
        """
        gae_req = AppEngineRequest(url="/foo", appid="test")

        request_post.return_value = Mock(text="")

        self.assertRaises(UnableToAuthenticate, gae_req.get_auth_token)

        data = {
            "Email": "",
            "Passwd": "",
            "service": "ah",
            "source": "",
            "accountType": "HOSTED_OR_GOOGLE"
        }

        request_post.assert_called_once_with(
            "https://www.google.com/accounts/ClientLogin", data=data)

    @patch("appengine_requests.requests.post")
    def test_response_with_only_filter_chars_raises(self, request_post):
        """Ensure that if the request returns only the filterd values that it
        raises. Not sure what would trigger this case.
        """
        gae_req = AppEngineRequest(url="/foo", appid="test", source="test",
                                   email="foo@bar.com", password="foobar")

        request_post.return_value = Mock(text="=\n")

        self.assertRaises(UnableToAuthenticate, gae_req.get_auth_token)

        data = {
            "Email": "foo@bar.com",
            "Passwd": "foobar",
            "service": "ah",
            "source": "test",
            "accountType": "HOSTED_OR_GOOGLE"
        }

        request_post.assert_called_once_with(
            "https://www.google.com/accounts/ClientLogin", data=data)

    @patch("appengine_requests.requests.post")
    def test_response_doesnot_have_auth_raises(self, request_post):
        """Ensure that if the request returns without an Auth token supplied
        that it raises.
        """
        gae_req = AppEngineRequest(url="/foo", appid="test", source="test",
                                   email="foo@bar.com", password="foobar")

        request_post.return_value = Mock(text="asdf=blah\n")

        self.assertRaises(UnableToAuthenticate, gae_req.get_auth_token)

        data = {
            "Email": "foo@bar.com",
            "Passwd": "foobar",
            "service": "ah",
            "source": "test",
            "accountType": "HOSTED_OR_GOOGLE"
        }

        request_post.assert_called_once_with(
            "https://www.google.com/accounts/ClientLogin", data=data)

    @patch("appengine_requests.requests.post")
    def test_response_has_auth_token(self, request_post):
        """Ensure that if the response has an auth token that it is returned
        correctly.
        """
        gae_req = AppEngineRequest(url="/foo", appid="test", source="test",
                                   email="foo@bar.com", password="foobar")

        request_post.return_value = Mock(text="Auth=my_token\n")

        token = gae_req.get_auth_token()

        self.assertEqual(token, "my_token")
        self.assertIsNone(gae_req.sid)

        data = {
            "Email": "foo@bar.com",
            "Passwd": "foobar",
            "service": "ah",
            "source": "test",
            "accountType": "HOSTED_OR_GOOGLE"
        }

        request_post.assert_called_once_with(
            "https://www.google.com/accounts/ClientLogin", data=data)

    @patch("appengine_requests.requests.post")
    def test_response_has_auth_token_and_sid(self, request_post):
        """Ensure that if the response has an auth token and a sessionid that
        the token is returned correctly and the sid set on the class.
        """
        gae_req = AppEngineRequest(url="/foo", appid="test", source="test",
                                   email="foo@bar.com", password="foobar")

        request_post.return_value = Mock(text="Auth=my_token\nSID=my_sid")

        token = gae_req.get_auth_token()

        self.assertEqual(token, "my_token")
        self.assertEqual(gae_req.sid, "my_sid")

        data = {
            "Email": "foo@bar.com",
            "Passwd": "foobar",
            "service": "ah",
            "source": "test",
            "accountType": "HOSTED_OR_GOOGLE"
        }

        request_post.assert_called_once_with(
            "https://www.google.com/accounts/ClientLogin", data=data)


class VerifiyTokenAppEngineRequestTestCase(unittest.TestCase):

    def test_verification_failed(self):
        """Ensure that if verification fails that an UnableToVerifyToken
        exception is raised.
        """
        pass
