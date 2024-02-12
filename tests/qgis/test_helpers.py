#! python3  # noqa E265

"""
    Usage from the repo root folder:

    .. code-block:: bash

        # for whole tests
        python -m unittest tests.qgis.test_plg_preferences
        # for specific test
        python -m unittest tests.qgis.test_plg_preferences.TestPlgPreferences.test_plg_preferences_structure
"""

# standard library
from qgis.testing import unittest

# project
from plugin_qgis_lpo.commons.helpers import simplify_name

# ############################################################################
# ########## Classes #############
# ################################


class TestHelpers(unittest.TestCase):
    def test_simplify_name(self):
        """Test settings types and default values."""
        string = "Table des espèces d'oiseaux 20/03/2023"

        # global
        self.assertEqual(simplify_name(string), "table_des_especes_doiseaux_20032023")


# ############################################################################
# ####### Stand-alone run ########
# ################################
if __name__ == "__main__":
    unittest.main()
