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
from plugin_qgis_lpo.commons.helpers import invalid_layer_message, simplify_name

# ############################################################################
# ########## Classes #############
# ################################


class TestHelpers(unittest.TestCase):
    def test_simplify_name(self):
        """Test settings types and default values."""
        string = "Table des espèces d'oiseaux 20/03/2023"

        # global
        self.assertEqual(simplify_name(string), "table_des_especes_doiseaux_20032023")

    def test_invalid_layer_message_includes_qgis_reason(self):
        """Test invalid layer diagnostics are included in the exception text."""

        class FakeError:
            def __init__(self, summary, message):
                self._summary = summary
                self._message = message

            def isEmpty(self):
                return False

            def summary(self):
                return self._summary

            def message(self, *_args):
                return self._message

        class FakeProvider:
            def error(self):
                return FakeError(
                    "Erreur provider",
                    "relation postgis_resultat inexistante",
                )

        class FakeLayer:
            def error(self):
                return FakeError("Erreur couche", "URI invalide")

            def dataProvider(self):
                return FakeProvider()

        message = invalid_layer_message(FakeLayer())

        self.assertIn("Cause remontée par QGIS/PostGIS", message)
        self.assertIn("couche: Erreur couche", message)
        self.assertIn("URI invalide", message)
        self.assertIn("fournisseur de données: Erreur provider", message)
        self.assertIn("relation postgis_resultat inexistante", message)


# ############################################################################
# ####### Stand-alone run ########
# ################################
if __name__ == "__main__":
    unittest.main()
