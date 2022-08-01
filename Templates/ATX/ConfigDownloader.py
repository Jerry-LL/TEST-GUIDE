# -*- coding: utf-8 -*-

'''
Created on 20.07.2020

@author Alexander Lehmann
'''

__copyright__ = "Copyright © by TraceTronic GmbH, Dresden"
__license__ = "This file is distributed as an integral part of TraceTronic's software products " \
              "and may only be used in connection with and pursuant to the terms and conditions " \
              "of a valid TraceTronic software product license."

import requests

from log import EPrint, SPrint, WPrint, DPrint, LEVEL_NORMAL

from .RetryingTgRequestService import RetryingTgRequestService


class ConfigDisabledError(Exception):
    '''
    Error der geworfen wird, wenn die zentrale Config deaktiviert ist.
    '''
    pass


class ConfigDownloader:
    '''
    Lädt die Konfiguration für die ATX-Generierung von einem TEST-GUIDE Server herunter.
    '''

    def __init__(self, uploadSettings, maxTries):
        '''
        Konstruktor.
        :param uploadSettings: die Einstellungen für den Upload zu TEST-GUIDE.
        :type uploadSettings: UploadSettings
        :param maxTries: Obere Schranke an die Anzahl der Download-Versuche. Kleiner 1 bedeutet
        unbegrenzt
        :type maxTries: int
        '''
        self.__uploadSettings = uploadSettings
        self.__maxTries = maxTries

    def DownloadConfig(self):
        '''
        :return: Ermittelt die aktuellen Settings von TEST-GUIDE.
        :rtype: dict
        '''

        def DoDownloadConfig():
            url = self.__GetTargetUrl()
            DPrint(LEVEL_NORMAL, 'Downloading config from {0}'.format(url))
            return requests.get(url=url,
                                verify=False,
                                proxies=self.__uploadSettings.proxies)

        requestService = RetryingTgRequestService(self.__maxTries)

        response = requestService.PerformRequest(DoDownloadConfig)
        if response.status_code == 204:
            raise ConfigDisabledError("Error: useSettingsFromServer is set to 'True' but "
                                      "settings are disabled in TEST-GUIDE")
        if response.status_code != 200:
            EPrint("Could not retrieve config from server")
            response.raise_for_status()
            raise IOError("Unexpected status code " + str(response.status_code) + " - " + response.reason)

        jsonDict = response.json()
        return jsonDict['settings']

    def __GetTargetUrl(self):
        """
        :returns: Gibt in Abhängigkeit ob HTTPS verwendet werden soll oder nicht die entsprechende
                  URL zu den ATX-Generator-Settings zurück.
        :rtype: str
        """
        # Default URL Protocol wenn nix angegeben.
        urlProtocolPrefix = u'http://'

        # Wenn https gewünscht.
        if self.__uploadSettings.useHttps:
            urlProtocolPrefix = u'https://'

        contextPath = self.__uploadSettings.contextPath
        if self.__uploadSettings.contextPath:
            contextPath += u'/'

        return (u'{pro}{url}:{port}/{context}api/report/atx/settings'
                u'?authKey={authKey}'
                u'&projectId={projectId}').format(pro=urlProtocolPrefix,
                                                  url=self.__uploadSettings.url,
                                                  port=self.__uploadSettings.port,
                                                  context=contextPath,
                                                  authKey=self.__uploadSettings.authKey,
                                                  projectId=self.__uploadSettings.projectId)
