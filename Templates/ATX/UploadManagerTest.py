# -*- coding: utf-8 -*-

'''
Created on 20.11.2014

:author: Philipp Schneider <philipp.schneider@tracetronic.de>
'''

__copyright__ = "Copyright © by TraceTronic GmbH, Dresden"
__license__ = "This file is distributed as an integral part of TraceTronic's software products " \
              "and may only be used in connection with and pursuant to the terms and conditions " \
              "of a valid TraceTronic software product license."

import gettext
gettext.NullTranslations().install()
import json
import os

import tempfile
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from mockito import mock, when

try:
    # FakeApiModules importieren, damit alte Pfade gefunden werden
    import tts.core.application.FakeApiModules  # @UnusedImport
except ImportError:
    # FakeApiModules erst ab ECU-TEST 8.1 verfügbar
    pass

from .UploadSettings import UploadSettings
from .UploadManager import UploadManager


class UploadManagerTest(unittest.TestCase):
    '''
    Tests für den UploadManager.
    '''

    def testUrlWithContextPath(self):
        reportApiMock = mock()
        uploadSettings = UploadSettings(u'127.0.0.1', 8085, True, u'test-guide', u'', None, 1)
        um = UploadManager(reportApiMock, u"1.5.1", u'file-upload', u"BigFile.zip", u"DummyPath",
                           uploadSettings)
        self.assertEqual(um._GetTargetUrl(),
                         (u"https://127.0.0.1:8085/test-guide/api/upload-file?apiVersion=1.5.1"
                          u"&authKey=&projectId=1&async=true"))

    def testStatusUrlWithContextPath(self):
        reportApiMock = mock()
        uploadSettings = UploadSettings(u'127.0.0.1', 8085, True, u'test-guide', u'', None, 1)
        um = UploadManager(reportApiMock, u"1.5.1", u'file-upload', u"BigFile.zip", u"DummyPath",
                           uploadSettings)
        self.assertEqual(um._GetStatusUrl(u"/api/upload-file/status/42"),
                         u"https://127.0.0.1:8085/test-guide/api/upload-file/status/42?authKey=")

    def testStatusUrlWithoutContextPath(self):
        reportApiMock = mock()
        uploadSettings = UploadSettings(u'127.0.0.1', 8085, True, u'', u'', None, 1)
        um = UploadManager(reportApiMock, u"1.5.1", u'file-upload', u"BigFile.zip", u"DummyPath",
                           uploadSettings)
        self.assertEqual(um._GetStatusUrl(u"/api/upload-file/status/42"),
                         u"https://127.0.0.1:8085/api/upload-file/status/42?authKey=")

    def testHttpsUrl(self):
        reportApiMock = mock()

        uploadSettings = UploadSettings(u'127.0.0.1', 8085, True, u'', u'', None, 1)
        um = UploadManager(reportApiMock, u"1.5.1", u'file-upload', u"BigFile.zip", u"DummyPath",
                           uploadSettings)
        self.assertEqual(um._GetTargetUrl(),
                         (u"https://127.0.0.1:8085/api/upload-file?apiVersion=1.5.1&authKey="
                          u"&projectId=1&async=true"))

    def testDefaultHttpUrl(self):
        reportApiMock = mock()
        uploadSettings = UploadSettings(u'127.0.0.1', 8085, False, u'', u'', None, 1)
        um = UploadManager(reportApiMock, u"1.5.1", u'file-upload', u"BigFile.zip", u"DummyPath",
                           uploadSettings)
        self.assertEqual(um._GetTargetUrl(),
                         (u"http://127.0.0.1:8085/api/upload-file?apiVersion=1.5.1&authKey="
                          u"&projectId=1&async=true"))

    def testHttpAuthKeyUrl(self):
        # ARRANGE
        authKey = (u"egBnG8EOnkGttaW0yEkon%2B%2BzSh7RUCW5Id6ze8gnjrTayPKEkOhxq1pmx4Pgj8chH35ZnCniSw"
                   u"wYscK%2Boej8aqOU0zE4skvFnCtdkitP4o4zrrP2Xy%2BIm7C6XBuju7XQ8KHstUyLagzSY3QKKhbB"
                   u"lz1gPll%2FFINg%2BX%2BXjeoas2ftpI8%2FW%2FhfuQPqaFavstq1uxKeDg0U2h8cJsLvDxKj4FeQ"
                   u"CqBaPdOwDduQJgwZzW7vZc43tTp%2BmJdRqAuRveYqPo1zWpX%2FinL2JHnft2g4nV0OLpPJ0zpBUw"
                   u"k%2BKiVunww%3D")
        reportApiMock = mock()
        uploadSettings = UploadSettings(u'127.0.0.1', 8085, False, u'', authKey, None, 1)

        # ACT
        um = UploadManager(reportApiMock, u"1.5.1", u'file-upload', u"BigFile.zip", u"DummyPath",
                           uploadSettings)
        # ASSERT
        self.assertEqual(um._GetTargetUrl(),
                         (u"http://127.0.0.1:8085/api/upload-file"
                          u"?apiVersion=1.5.1&authKey={0}&projectId=1&async=true").format(authKey))

    def testBigFileUpload(self):
        '''
        Prüfung das kein MemoryError beim Upload von großen Dateien erfolgt.
        '''
        # ARRANGE
        reportApiMock = mock()
        when(reportApiMock).GetReportDir().thenReturn(tempfile.gettempdir())
        uploadSettings = UploadSettings(u'localhostInvalidUrl', 8085, True, u'test-guide', u'', None, 1)

        fileTemp = tempfile.NamedTemporaryFile(prefix=u"bigUploadFile", delete=False)
        try:
            # Beispieldatei mit > 1000MB erzeugen
            with open(fileTemp.name, u"wb") as out:
                out.seek((1024 * 1024 * 1024) - 1)
                out.write(b'\0')

            um = UploadManager(reportApiMock, u"1.5.1", u'file-upload',
                               u"BigFile.zip", fileTemp.name, uploadSettings)

            # ACT
            try:
                # ASSERT
                # Es darf kein Memory Error auftreten beim Upload.
                self.assertTrue(not um.StartUpload(),
                                u"Upload von falscher URL darf nicht möglich sein.")
            except MemoryError:
                self.fail(u"MemoryError ist aufgetreten.")

        finally:
            fileTemp.close()
            os.remove(fileTemp.name)

    def testGetConfigUploadTriesOnEmptySetting(self):
        # ARRANGE
        reportApiMock = mock()
        when(reportApiMock).GetSetting(u'maxUploadTries').thenReturn("")
        uploadSettings = UploadSettings(u'localhost', 8085, True, u'test-guide', u'', None, 1)

        # ACT
        result = UploadManager(reportApiMock, u"1.5.1", u'file-upload', u"BigFile.zip",
                               u"DummyPath", uploadSettings)
        # ASSERT
        self.assertEqual(result.GetMaxUploadTries(), 1)

    def testGetConfigUploadTriesOnInvalidSetting(self):
        # ARRANGE
        reportApiMock = mock()
        when(reportApiMock).GetSetting(u'maxUploadTries').thenReturn("jo10")
        uploadSettings = UploadSettings(u'localhost', 8085, True, u'test-guide', u'', None, 1)

        # ACT
        result = UploadManager(reportApiMock, u"1.5.1", u'file-upload', u"BigFile.zip",
                               u"DummyPath", uploadSettings)
        # ASSERT
        self.assertEqual(result.GetMaxUploadTries(), 1)

    def testGetConfigUploadTriesOnInvalidFloatSetting(self):
        # ARRANGE
        reportApiMock = mock()
        when(reportApiMock).GetSetting(u'maxUploadTries').thenReturn("10.05")
        uploadSettings = UploadSettings(u'localhost', 8085, True, u'test-guide', u'', None, 1)

        # ACT
        result = UploadManager(reportApiMock, u"1.5.1", u'file-upload', u"BigFile.zip",
                               u"DummyPath", uploadSettings)
        # ASSERT
        self.assertEqual(result.GetMaxUploadTries(), 1)

    def testGetConfigUploadTriesOnUnlimited(self):
        # ARRANGE
        reportApiMock = mock()
        when(reportApiMock).GetSetting(u'maxUploadTries').thenReturn("-1")
        uploadSettings = UploadSettings(u'localhost', 8085, True, u'test-guide', u'', None, 1)

        # ACT
        result = UploadManager(reportApiMock, u"1.5.1", u'file-upload', u"BigFile.zip",
                               u"DummyPath", uploadSettings)
        # ASSERT
        self.assertEqual(result.GetMaxUploadTries(), 9223372036854775807)

    def testBaseUrlWithContextPath(self):
        reportApiMock = mock()

        uploadSettings = UploadSettings(u'127.0.0.1', 8085, True, u'test-guide', u'', None, 1)

        um = UploadManager(reportApiMock, u"1.5.1", u'file-upload', u"BigFile.zip", u"DummyPath",
                           uploadSettings)
        self.assertEqual(um._GetBaseUrl(),
                         u"https://127.0.0.1:8085/test-guide")

    def testBaseUrlWithoutContextPath(self):
        # ARRANGE
        reportApiMock = mock()
        uploadSettings = UploadSettings(u'127.0.0.1', 8085, True, u'', u'', None, 1)
        um = UploadManager(reportApiMock, u"1.5.1", u'file-upload', u"BigFile.zip", u"DummyPath",
                           uploadSettings)
        # ACT + ASSERT
        self.assertEqual(um._GetBaseUrl(),
                         u"https://127.0.0.1:8085")

    def testUploadErrorLogOnUploadFailedOnMaintenanceStatus(self):
        # ARRANGE
        port = 9087
        mock_server = HTTPServer(('localhost', port), MockMaintenanceStatusRequestHandler)
        mock_server_thread = Thread(target=mock_server.serve_forever)
        mock_server_thread.setDaemon(True)
        mock_server_thread.start()

        reportApiMock = mock()
        when(reportApiMock).GetReportDir().thenReturn(tempfile.gettempdir())
        when(reportApiMock).GetSetting(u'maxUploadTries').thenReturn("1")
        errorJson = os.path.join(reportApiMock.GetReportDir(), u"error.raw.json")

        if os.path.exists(errorJson):
            os.remove(errorJson)

        with tempfile.NamedTemporaryFile(prefix=u"uploadFile", delete=False) as fileTemp:
            fileTemp.write(b'Test')
            fileTemp.flush()
        try:
            # ACT
            uploadSettings = UploadSettings(u'localhost', port, False, u'', u'', None, 1)
            um = UploadManager(reportApiMock, u"1.5.1", u'file-upload', u"File.zip",
                               fileTemp.name, uploadSettings)

            # ASSERT
            self.assertFalse(um.StartUpload())
            self.assertTrue(os.path.exists(errorJson))

            with open(errorJson) as jsonFile:
                errorResponse = json.loads(jsonFile.read())
                self.assertEqual(errorResponse[u"messages"][0][u"statusCode"], 503)
        finally:
            os.remove(fileTemp.name)

    def testUploadToResourceAdapterBuffer(self):
        '''
        Prüfung für Upload über ResourceAdapter.
        '''
        # ARRANGE
        port = 44422
        mock_server = HTTPServer(('localhost', port), MockResourceAdapterRequestHandler)
        mock_server_thread = Thread(target=mock_server.serve_forever)
        mock_server_thread.setDaemon(True)
        mock_server_thread.start()

        reportApiMock = mock()
        when(reportApiMock).GetReportDir().thenReturn(tempfile.gettempdir())
        when(reportApiMock).GetSetting(u'projectId').thenReturn(u'123')
        when(reportApiMock).GetSetting(u'uploadAuthenticationKey').thenReturn(u'AuthKey==')
        when(reportApiMock).GetSetting(u'uploadThroughResourceAdapter').thenReturn(port)

        with tempfile.NamedTemporaryFile(prefix=u'uploadFile', delete=False) as fileTemp:
            fileTemp.write(b'Test')
            fileTemp.flush()

        uploadSettings = UploadSettings(u'127.0.0.1', port, True, u'test-guide', u'', u'AuthKey==', 123)

        um = UploadManager(reportApiMock, u'1.5.1', u'file-upload',
                           u'File.zip', fileTemp.name, uploadSettings)

        # ACT
        result = um.StartUpload()
        os.remove(fileTemp.name)

        # ASSERT
        self.assertTrue(result)


class MockMaintenanceStatusRequestHandler(BaseHTTPRequestHandler):
    '''
    Mock-Server für TEST-GUIDE im Wartungsmodus.
    '''

    def do_GET(self):
        self.send_response(503)
        self.end_headers()


class MockResourceAdapterRequestHandler(BaseHTTPRequestHandler):
    """
    Mock-Server für den Upload-Knecht im RA
    """

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        self.rfile.read(content_length)
        self.send_response(202)
        self.end_headers()


if __name__ == "__main__":
    unittest.main()
