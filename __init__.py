# -*- coding: utf-8 -*-

"""
/***************************************************************************
        ScriptsLPO : __init__.py
        -------------------
        Date                 : 2020-04-16
        Copyright            : (C) 2020 by Elsa Guilley (LPO AuRA)
        Email                : lpo-aura@lpo.fr
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""

__author__ = "Elsa Guilley (LPO AuRA)"
__date__ = "2020-04-16"
__copyright__ = "(C) 2020 by Elsa Guilley (LPO AuRA)"

from .scripts_lpo import ScriptsLPOPlugin


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load ScriptsLPOPlugin class from file scripts_lpo.py

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    return ScriptsLPOPlugin(iface)
