import requests
import logging

from datetime import datetime, timedelta


class LookerAuthenticationError(Exception):
    pass


class LookerAuth(object):
    def __init__(self, *, client_id, client_secret, looker_base_url):
        self._client_id = client_id
        self._client_secret = client_secret
        self._login_url = "{}/api/3.0/login".format(looker_base_url)

        self._auth_token = None
        self._expiry_time = datetime.now()

    def _authenticate(self):
        logging.debug("No up-to-date token. Authenticating now.")
        params = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }

        response = requests.post(self._login_url, params=params)
        credentials = response.json()

        try:
            self._auth_token = credentials["access_token"]
            self._expiry_time = datetime.now() + timedelta(seconds=credentials["expires_in"] - 60)
            logging.debug("New credentials succesfully fetched.")
        except:
            logging.error(
                """
Couldn't find credentials in Looker response:
    {}
If you're seeing 'Not found' this could be because of an incorrect client_id/client_secret.
            """.format(credentials)
            )
            raise

    def get_token(self):
        if datetime.now() >= self._expiry_time:
            self._authenticate()

        return self._auth_token
