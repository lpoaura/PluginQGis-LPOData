# -*- coding: utf-8 -*-

"""
/***************************************************************************
        ScriptsLPO : common_functions.py
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
"""

__author__ = 'Elsa Guilley (LPO AuRA)'
__date__ = '2020-04-16'
__copyright__ = '(C) 2020 by Elsa Guilley (LPO AuRA)'

# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

def simplifyName(string):
    translation_table = str.maketrans(
        'àâäéèêëîïôöùûüŷÿç~- ',
        'aaaeeeeiioouuuyyc___',
        "2&'([{|}])`^\/@+-=*°$£%§#.?!;:<>"
    )
    return string.lower().translate(translation_table)
