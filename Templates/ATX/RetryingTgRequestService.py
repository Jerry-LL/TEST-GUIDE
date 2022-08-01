# -*- coding: utf-8 -*-

__copyright__ = "Copyright © by TraceTronic GmbH, Dresden"
__license__ = "This file is distributed as an integral part of TraceTronic's software products " \
              "and may only be used in connection with and pursuant to the terms and conditions " \
              "of a valid TraceTronic software product license."

from datetime import datetime
import time

import requests
from log import DPrint, LEVEL_NORMAL

# HTTP date format: Thu, 01 Dec 1994 16:00:00 GMT
# https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Date
HTTP_DATE_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'
A_LOT_OF_TRIES = 100000
HTTP_SERVICE_UNAVAILABLE = 503
HTTP_TOO_MANY_REQUESTS = 429


class RetryingTgRequestService:
    """
    Führt Requests zu einem TEST-GUIDE-Server durch. Sorgt dafür, dass im Wartungsfall von
    TEST-GUIDE der Request entsprechend der Einstellung wiederholt versucht wird.
    """

    def __init__(self, maxTries, defaultSleepSec=360, minSleepSec=10, maxSleepSec=14400):
        """
        :param maxTries: Maximale Anzahl der Versuche. Wenn kleiner als 1, wird unbegrenzt oft
        versucht.
        :param defaultSleepSec: Wartezeit in Sekunden zwischen zwei Versuchen für den Fall, dass
        kein Retry-After-HTTP-Header vom Server kommt.
        :param minSleepSec: Untere Schranke an die Wartezeit zwischen zwei Versuchen in Sekunden.
        :param maxSleepSec: Obere Schranke an die Wartezeit zwischen zwei Versuchen in Sekunden.
        """
        self.__maxTries = A_LOT_OF_TRIES if maxTries < 1 else maxTries
        self.__defaultSleepSec = defaultSleepSec
        self.__minSleepSec = minSleepSec
        self.__maxSleepSec = maxSleepSec

    def _ParseRetryAfter(self, headerRetryAfterValue):
        """
        Parst den übergebenen Retry-After Header-Wert, der in Sekunden oder
        als Datum (RFC 1123-Format) übertragen werden kann.
        :param: headerRetryAfterValue: Header aus dem die Sekunden ermittelt werden sollen.
        :type: headerRetryAfterValue: str
        :return: Sekunden, die bis zum nächsten Upload gewartet werden sollen, unter
        Berücksichtigung der im ctor angegebenen Grenzen
        :rtype: int
        """
        if isinstance(headerRetryAfterValue, str):
            if headerRetryAfterValue.isdigit():
                sleepSec = int(headerRetryAfterValue)
            else:
                try:
                    dateRetryAfter = datetime.strptime(headerRetryAfterValue,
                                                       HTTP_DATE_FORMAT)
                    dateNow = datetime.now()
                    sleepSec = int(dateRetryAfter.timestamp() - dateNow.timestamp())
                except ValueError:
                    DPrint(LEVEL_NORMAL, 'Invalid Retry-After header: {0}'
                           .format(headerRetryAfterValue))
                    sleepSec = self.__defaultSleepSec
        elif isinstance(headerRetryAfterValue, int):
            sleepSec = headerRetryAfterValue
        else:
            sleepSec = self.__defaultSleepSec

        return max(min(sleepSec, self.__maxSleepSec), self.__minSleepSec)

    def PerformRequest(self, requestCallback, retryCallback=lambda tries, sleepSec: None):
        """
        Führt den Request durch. Wenn 429 oder 503 zurückkommt, wird die vom Server vorgeschlagene
        Zeit gewartet und danach der Request wiederholt.

        :param requestCallback: Parameterlose Funktion, der den eigentlichen Request beinhaltet.
        Muss eine requests.Response zurückgeben
        :param retryCallback: Funktion, die beim Retry aufgerufen wird. Übergeben werden die Anzahl
        der bisherigen Versuche und die Wartezeit in Sekunden.

        :return: Response. Der Aufrufer ist für das Schließen zuständig.

        :raises HTTPError: Wenn die maximale Anzahl Versuche überschritten wurde. Beinhaltet die
        Response des letzten Versuchs.
        """

        tries = 1
        while True:
            response = requestCallback()

            if response.status_code not in [HTTP_TOO_MANY_REQUESTS, HTTP_SERVICE_UNAVAILABLE]:
                return response

            retryAfter = response.headers.get("Retry-After")

            DPrint(LEVEL_NORMAL, "Try {0}/{1} failed because the server returned HTTP {2}"
                   .format(tries, self.__maxTries, response.status_code))

            sleepSec = self._ParseRetryAfter(retryAfter)

            retryCallback(tries, sleepSec)

            if tries >= self.__maxTries:
                response.raise_for_status()

            response.close()
            DPrint(LEVEL_NORMAL, "Retrying after {0} seconds".format(sleepSec))
            time.sleep(sleepSec)
            tries += 1

    def PerformHealthCheckedRequest(self, baseUrl, requestCallback,
                                    retryCallback=lambda tries, sleepSec: None):
        """
        Analog zu performRequest, prüft aber vorab über die TEST-GUIDE-Health-API, ob
        TEST-GUIDE überhaupt verfügbar ist.


        :param baseUrl: Basis-URL des TEST-GUIDE-Servers
        :param requestCallback: Parameterlose Funktion, der den eigentlichen Request beinhaltet.
        Muss eine requests.Response zurückgeben
        :param retryCallback: Funktion, die beim Retry aufgerufen wird. Übergeben werden die Anzahl
        der bisherigen Versuche und die Wartezeit in Sekunden.

        :return: Response. Der Aufrufer ist für das Schließen zuständig.

        :raises HTTPError: Wenn die maximale Anzahl Versuche überschritten wurde. Beinhaltet die
        Response des letzten Versuchs.
        """

        def DoCheckHealth():
            healthUrl = r'{0}/api/health/ready'.format(baseUrl)
            DPrint(LEVEL_NORMAL, 'Checking server health via {0}'.format(healthUrl))
            return requests.get(healthUrl, verify=False)

        # Warten, bis TG ready ist
        healthResponse = self.PerformRequest(DoCheckHealth, retryCallback)
        healthResponse.close()

        # Eigentlichen Request absetzen
        return self.PerformRequest(requestCallback, retryCallback)
