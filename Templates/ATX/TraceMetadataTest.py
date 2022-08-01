# -*- coding: utf-8 -*-

__copyright__ = "Copyright © by TraceTronic GmbH, Dresden"
__license__ = "This file is distributed as an integral part of TraceTronic's software products " \
              "and may only be used in connection with and pursuant to the terms and conditions " \
              "of a valid TraceTronic software product license."

import unittest

try:
    # FakeApiModules importieren, damit alte Pfade gefunden werden
    import tts.core.application.FakeApiModules  # @UnusedImport
except ImportError:
    # FakeApiModules erst ab ECU-TEST 8.1 verfügbar
    pass

from .TraceMetadata import SplitNameAndFormatDetails


class TraceMetadataTest(unittest.TestCase):

    def testGetNameAndFormatDetails(self):
        self.assertEqual((None, None), SplitNameAndFormatDetails(None))
        self.assertEqual((None, None), SplitNameAndFormatDetails(""))
        self.assertEqual(("ABC", ""), SplitNameAndFormatDetails("ABC"))
        self.assertEqual(("ABC (", ""), SplitNameAndFormatDetails("ABC ("))
        self.assertEqual(("ABC )", ""), SplitNameAndFormatDetails("ABC )"))
        self.assertEqual(("ABC", "XYZ"), SplitNameAndFormatDetails("ABC (XYZ)"))
        self.assertEqual(("ABC", "XYZ (xyz)"), SplitNameAndFormatDetails("ABC (XYZ (xyz))"))
        self.assertEqual(("ABC(XYZ", "xyz)"), SplitNameAndFormatDetails("ABC(XYZ (xyz))"))
        self.assertEqual(("", ""), SplitNameAndFormatDetails(" ()"))
