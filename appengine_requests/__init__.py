__version__ = "0.0.1"


class AppEngineRequest(object):

    def __init__(self, **kwargs):
        """Initalize the AppEngineRequest request, set the arguments passed in
        and the defaults for those that aren't.

        :param options: :class: `Args`
        """
        self.options = kwargs.get('options')
        self.email = kwargs.get('email')
        self.appid = kwargs.get('appid')
        self.url = kwargs.get('url')
        self.secure = kwargs.get('use_ssl')

        self.password = None

    def build_url(self):
        """Build a url based off the appid, url and ssl properties."""
        scheme = "https" if self.secure else "http"

        url = ""
        if not self.url:
            url = "/"
        else:
            if self.url.startswith('http'):
                return self.url

            url = self.url if self.url.startswith("/") else "/" + self.url

        if not self.appid:
            domain = "localhost"
        else:
            domain = self.appid.strip("s~")

            if not self.appid.endswith(".appspot.com"):
                domain += ".appspot.com"

        return "%s://%s%s" % (scheme, domain, url)
