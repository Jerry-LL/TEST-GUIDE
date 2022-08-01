# -*- coding: utf-8 -*-

'''
Created on 21.07.2020

@author: Alexander Lehmann
'''

__copyright__ = "Copyright © by TraceTronic GmbH, Dresden"
__license__ = "This file is distributed as an integral part of TraceTronic's software products " \
              "and may only be used in connection with and pursuant to the terms and conditions " \
              "of a valid TraceTronic software product license."

import json
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

try:
    # FakeApiModules importieren, damit alte Pfade gefunden werden
    import tts.core.application.FakeApiModules  # @UnusedImport
except ImportError:
    # FakeApiModules erst ab ECU-TEST 8.1 verfügbar
    print("could not import FakeApiModules")
    pass

from .UploadSettings import UploadSettings
from .ConfigDownloader import ConfigDownloader, ConfigDisabledError


class ConfigDownloadTest (unittest.TestCase):
    """
    Test für den ConfigDownloader
    """

    def testDownloadConfigOk(self):
        # ARRANGE
        port = 9085

        settings = [
            {"key": "Blubb", "value": "ABC123"},
            {"key": "Ola", "value": "Test"}]
        MockAtxSettingsRequestHandler.responseBody = {"settings": settings}
        MockAtxSettingsRequestHandler.responseCode = 200
        MockAtxSettingsRequestHandler.context = u'/context/'
        mock_server = HTTPServer(('localhost', port), MockAtxSettingsRequestHandler)
        mock_server_thread = Thread(target=mock_server.serve_forever)
        mock_server_thread.setDaemon(True)
        mock_server_thread.start()
        uploadSettings = UploadSettings(u'localhost', port, False, u'context', u'abc', None, 1)

        # ACT
        cd = ConfigDownloader(uploadSettings, 0)
        downloadedSettings = cd.DownloadConfig()

        # ASSERT
        self.assertEqual(settings, downloadedSettings)
        mock_server.shutdown()
        mock_server.server_close()

    def testDownloadConfigNotPresent(self):
        # ARRANGE
        port = 9085
        MockAtxSettingsRequestHandler.responseCode = 204
        mock_server = HTTPServer(('localhost', port), MockAtxSettingsRequestHandler)
        mock_server_thread = Thread(target=mock_server.serve_forever)
        mock_server_thread.setDaemon(True)
        mock_server_thread.start()
        
        uploadSettings = UploadSettings(u'localhost', port, False, u'context', u'abc', None, 1)

        # ACT
        cd = ConfigDownloader(uploadSettings, 0)
        executable = cd.DownloadConfig

        # ASSERT
        self.assertRaises(ConfigDisabledError, executable)

        mock_server.shutdown()
        mock_server.server_close()


class MockAtxSettingsRequestHandler(BaseHTTPRequestHandler):
    '''
    Mock-Handler, der Settings zurückliefert.
    '''
    responseBody = None
    responseCode = 200
    context = u''

    def do_GET(self):
        if not self.path.startswith(MockAtxSettingsRequestHandler.context):
            self.send_response(404)
            return

        self.send_response(MockAtxSettingsRequestHandler.responseCode)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(bytes(json.dumps(MockAtxSettingsRequestHandler.responseBody), 'utf-8'))


if __name__ == "__main__":
    unittest.main()
