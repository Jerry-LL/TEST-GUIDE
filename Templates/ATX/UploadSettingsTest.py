# -*- coding: utf-8 -*-

'''
Created on 22.09.2021

@author: Christoph Groß <christoph.gross@tracetronic.de>
'''

__copyright__ = "Copyright © by TraceTronic GmbH, Dresden"
__license__ = "This file is distributed as an integral part of TraceTronic's software products " \
              "and may only be used in connection with and pursuant to the terms and conditions " \
              "of a valid TraceTronic software product license."

import tempfile
import unittest

import os
import json
from .UploadSettings import UploadSettings


class UploadSettingsTest(unittest.TestCase):

    def testFileNotFound(self):
        self.assertRaises(FileNotFoundError,
                          lambda: UploadSettings.parseJson(tempfile.gettempdir(),
                                                           u'myconfigfile.json'))

    def testParseJsonFile(self):
        # ARRANGE
        filename = u'subdir/myconfigfile.json'

        data = {
            'url': '127.0.0.1',
            'serverLabel': 'Test',
            'useHttps': True, 'port': 123,
            'contextPath': '/ctx',
            'authKey': 'abc123',
            'proxies': {'https': 'mit ssl', 'http': 'ohne ssl'},
            'projectId': 1337
        }

        with tempfile.TemporaryDirectory() as tempdir:
            os.mkdir(os.path.join(tempdir, u'subdir'))
            filePath = os.path.join(tempdir, u'subdir', u'myconfigfile.json')
            with open(filePath, 'w') as writer:
                json.dump(data, writer)

            # ACT
            result = UploadSettings.parseJson(tempdir, filename)

            # ASSERT
            self.assertEqual(data.get('useHttps'), result.useHttps)
            self.assertEqual(data.get('url'), result.url)
            self.assertEqual(data.get('port'), result.port)
            self.assertEqual(data.get('contextPath'), result.contextPath)
            self.assertEqual(data.get('authKey'), result.authKey)
            self.assertEqual(data.get('proxies'), result.proxies)
            self.assertEqual(data.get('projectId'), result.projectId)

    def testJsonFileNoDict(self):
        # ARRANGE
        filename = u'subdir/myconfigfile.json'

        data = [1, 2, 3]

        with tempfile.TemporaryDirectory() as tempdir:
            os.mkdir(os.path.join(tempdir, u'subdir'))
            filePath = os.path.join(tempdir, u'subdir', u'myconfigfile.json')
            with open(filePath, 'w') as writer:
                json.dump(data, writer)

            # ASSERT
            self.assertRaises(AttributeError, lambda: UploadSettings.parseJson(tempdir, filename))

    def testFileIsNotJson(self):
        # ARRANGE
        filename = u'myconfigfile.json'

        with tempfile.TemporaryDirectory() as tempdir:
            filePath = os.path.join(tempdir, filename)
            with open(filePath, 'w') as writer:
                writer.write(u'test')

            # ASSERT
            self.assertRaises(json.decoder.JSONDecodeError,
                              lambda: UploadSettings.parseJson(tempdir, filename))
