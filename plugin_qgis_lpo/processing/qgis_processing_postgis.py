"""
***************************************************************************
    postgis.py
    ---------------------
    Date                 : November 2012
    Copyright            : (C) 2012 by Martin Dobias
    Email                : volayaf at gmail dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

__author__ = "Martin Dobias"
__date__ = "November 2012"
__copyright__ = "(C) 2012, Martin Dobias"


import psycopg2
import psycopg2.extensions  # For isolation levels
from qgis.core import (
    QgsDataSourceUri,
    QgsProcessingException,
    QgsSettings,
)
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import QInputDialog

# Use unicode!
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)


def uri_from_name(conn_name):
    settings = QgsSettings()
    settings.beginGroup("/PostgreSQL/connections/%s" % conn_name)

    if not settings.contains("database"):  # non-existent entry?
        raise QgsProcessingException(
            QCoreApplication.translate(
                "PostGIS", 'There is no defined database connection "{0}".'
            ).format(conn_name)
        )

    uri = QgsDataSourceUri()

    settingsList = [
        "service",
        "host",
        "port",
        "database",
        "username",
        "password",
        "authcfg",
    ]
    service, host, port, database, username, password, authcfg = [
        settings.value(x, "", type=str) for x in settingsList
    ]

    useEstimatedMetadata = settings.value("estimatedMetadata", False, type=bool)
    try:
        sslmode = settings.value("sslmode", QgsDataSourceUri.SslPrefer, type=int)
    except TypeError:
        sslmode = QgsDataSourceUri.SslPrefer

    settings.endGroup()

    if hasattr(authcfg, "isNull") and authcfg.isNull():
        authcfg = ""

    if service:
        uri.setConnection(service, database, username, password, sslmode, authcfg)
    else:
        uri.setConnection(host, port, database, username, password, sslmode, authcfg)

    uri.setUseEstimatedMetadata(useEstimatedMetadata)

    return uri



def get_connection_name():
    s = QgsSettings()
    s.beginGroup("PostgreSQL/connections")
    connection_name, res = QInputDialog.getItem(
        None, "Choisir une connexion", "Connexion", s.childGroups(), editable=False
    )
    if res:
        return connection_name
    else:
        return None
