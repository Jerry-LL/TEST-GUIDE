# -*- coding: utf-8 -*-

__copyright__ = "Copyright © by TraceTronic GmbH, Dresden"
__license__ = "This file is distributed as an integral part of TraceTronic's software products " \
              "and may only be used in connection with and pursuant to the terms and conditions " \
              "of a valid TraceTronic software product license."

import unittest
from datetime import datetime, timedelta
from unittest import mock
from unittest.mock import patch

from parameterized import parameterized
from requests import HTTPError

try:
    # FakeApiModules importieren, damit alte Pfade gefunden werden
    import tts.core.application.FakeApiModules  # @UnusedImport
except ImportError:
    # FakeApiModules erst ab ECU-TEST 8.1 verfügbar
    pass

from .RetryingTgRequestService import RetryingTgRequestService, HTTP_DATE_FORMAT


class ResponseStub:
    def __init__(self, statusCode, retryAfterHeaderValue=None):
        self.closed = 0
        self.status_code = statusCode
        self.headers = {}
        if retryAfterHeaderValue is not None:
            self.headers['Retry-After'] = retryAfterHeaderValue

    def close(self):
        self.closed += 1

    def raise_for_status(self):
        raise HTTPError(response=self)


class Responder:
    def __init__(self, responses):
        self.respones = responses
        self.i = -1

    def GetNextReponse(self):
        self.i += 1
        return self.respones[self.i]


class RetryingTgRequestServiceTest(unittest.TestCase):

    @patch("time.sleep")
    def testMaxTriesExceededException(self, patched_sleep):
        # ARRANGE
        subject = RetryingTgRequestService(1)
        response = ResponseStub(503)
        responder = Responder([response])

        # ACT
        with self.assertRaises(HTTPError) as cm:
            subject.PerformRequest(responder.GetNextReponse)

        # ASSERT
        self.assertEqual(cm.exception.response, response)
        patched_sleep.assert_not_called()

    @patch("time.sleep")
    def testUnlimitedTries(self, patched_sleep):
        # ARRANGE
        subject = RetryingTgRequestService(0)
        response1 = ResponseStub(503)
        response2 = ResponseStub(200)
        responder = Responder([response1, response1, response1, response1, response1, response1,
                               response1, response1, response1, response1, response1, response2])

        # ACT
        actual = subject.PerformRequest(responder.GetNextReponse)

        # ASSERT
        self.assertEqual(response1.closed, 11)
        self.assertEqual(actual, response2)

    @parameterized.expand([[None], [3.3], ["Blalba"]])
    def testParseRetryAfterDefaulting(self, retryAfterHeaderValue):
        # ARRANGE
        defaultSleepSec = 23
        subject = RetryingTgRequestService(1, defaultSleepSec)

        # ACT
        actual = subject._ParseRetryAfter(retryAfterHeaderValue)

        # ASSERT
        self.assertEqual(actual, defaultSleepSec)

    def testParseRetryAfterDate(self):
        # ARRANGE
        futureSeconds = 600
        retryAfterHeaderValue = (datetime.now() + timedelta(seconds=futureSeconds)).strftime(
            HTTP_DATE_FORMAT)
        subject = RetryingTgRequestService(1)

        # ACT
        actual = subject._ParseRetryAfter(retryAfterHeaderValue)

        # ASSERT
        self.assertAlmostEqual(actual, futureSeconds, delta=5)

    @parameterized.expand([[600], ['600'], [u'600'], [r'600']])
    def testParseRetryAfterSeconds(self, retryAfterHeaderValue):
        # ARRANGE
        subject = RetryingTgRequestService(1)

        # ACT
        actual = subject._ParseRetryAfter(retryAfterHeaderValue)

        # ASSERT
        self.assertEqual(actual, 600)

    def testParseRetryAfterUpperLimit(self):
        # ARRANGE
        maxSleepSec = 23
        subject = RetryingTgRequestService(1, maxSleepSec=maxSleepSec)

        # ACT
        actual = subject._ParseRetryAfter(maxSleepSec + 1)

        # ASSERT
        self.assertEqual(actual, maxSleepSec)

    def testParseRetryAfterLowerLimit(self):
        # ARRANGE
        minSleepSec = 23
        subject = RetryingTgRequestService(1, minSleepSec=minSleepSec)

        # ACT
        actual = subject._ParseRetryAfter(minSleepSec - 1)

        # ASSERT
        self.assertEqual(actual, minSleepSec)

    @patch("time.sleep")
    def testPerformRequest(self, patched_sleep):
        # ARRANGE
        sleepSec = 600
        response1 = ResponseStub(503, sleepSec)
        response2 = ResponseStub(200)
        responder = Responder([response1, response2])
        subject = RetryingTgRequestService(2)
        retryCallback = mock.Mock()

        # ACT
        actual = subject.PerformRequest(responder.GetNextReponse, retryCallback)

        # ASSERT
        self.assertEqual(actual, response2)
        self.assertEqual(response1.closed, 1)
        actualSleepSec = patched_sleep.call_args_list[0][0][0]
        self.assertEqual(actualSleepSec, sleepSec)
        retryCallback.assert_called_with(1, sleepSec)

    @patch("requests.get")
    def testPerformHealthCheckedRequest(self, patched_get):
        # ARRANGE
        baseUrl = "http://base.url:123"
        response = ResponseStub(200)
        responder = Responder([response])
        subject = RetryingTgRequestService(1)

        # ACT
        actual = subject.PerformHealthCheckedRequest(baseUrl, responder.GetNextReponse)

        # ASSERT
        self.assertEqual(actual, response)
        patched_get.assert_called_with(baseUrl + "/api/health/ready", verify=False)
