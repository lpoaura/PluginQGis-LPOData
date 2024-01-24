from processing.gui.wrappers import WidgetWrapper
from qgis.PyQt.QtCore import QDate, Qt
from qgis.PyQt.QtWidgets import QDateEdit


class DateTimeWidget(WidgetWrapper):
    """
    QDateTimeEdit widget with calendar pop up
    """

    def createWidget(self):  # noqa N802
        self._combo = QDateEdit()
        self._combo.setCalendarPopup(True)
        today = QDate.currentDate()
        self._combo.setDate(today)
        return self._combo

    def value(self):
        date_chosen = self._combo.dateTime()
        return date_chosen.toString(Qt.ISODate)
