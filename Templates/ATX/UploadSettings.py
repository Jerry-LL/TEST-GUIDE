# -*- coding: utf-8 -*-

'''
Created on 22.09.2021

@author: Christoph Groß <christoph.gross@tracetronic.de>
'''

__copyright__ = "Copyright © by TraceTronic GmbH, Dresden"
__license__ = "This file is distributed as an integral part of TraceTronic's software products " \
              "and may only be used in connection with and pursuant to the terms and conditions " \
              "of a valid TraceTronic software product license."

import os
import json


class UploadSettings(object):
    '''
    Enthält die für den Upload zu TEST-GUIDE benötigten Parameter.
    '''

    def __init__(self, url, port, useHttps, contextPath, authKey, proxies, projectId):
        '''
        Konstruktor.
        :param url: Addresse des Wicket-Web-Service.
        :type url: str
        :param port: Port dess Wicket-Web-Service.
        :type port: int
        :param useHttps: True, wenn eine Https-Verbindung verwendet werden soll, sonst False.
        :type useHttps: boolean
        :param contextPath: Context-URL (kann u.U. auch leer sein)
        :type contextPath: str
        :param authKey: Auth-Key für den Download der Zentral-Config.
        :type authKey: str
        :param proxies: Dict mit dem Mapping der Protokolle bei Verwendung eines Proxies oder
                        ein leeres Dict
        :type proxies: dict
        :param projectId: Project-Id
        :type projectId: int
        '''
        self.url = url or None
        self.port = port or 8085
        self.useHttps = useHttps or False
        self.contextPath = contextPath or u''
        self.authKey = authKey or u''
        self.proxies = proxies or {}
        self.projectId = projectId or 1

    @staticmethod
    def parseJson(workspacePath, uploadSettingsRelativePath):
        '''
        Löst den Pfad auf und liest die JSON Datei ein.
        @param workspacePath: Workspace-Verzeichnis
        @type workspacePath: str
        @param uploadSettingsRelativePath: relativer Pfad zur Konfigurationsdatei im Workspace
        @type uploadSettingsRelativePath: str
        @return: Verbindungseinstellungen
        @rtype: UploadSettings
        '''
        file = os.path.join(workspacePath, uploadSettingsRelativePath)
        if os.path.isfile(file):
            with open(file, 'r') as reader:
                data = json.load(reader)
                return UploadSettings(data.get(u'url', None),
                                      data.get(u'port', None),
                                      data.get(u'useHttps', None),
                                      data.get(u'contextPath', None),
                                      data.get(u'authKey', None),
                                      data.get(u'proxies', None),
                                      data.get(u'projectId', None))
        else:
            raise FileNotFoundError(u'Config file not found at path: {0}'.format(file))
