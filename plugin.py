from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.core import QgsRasterLayer, QgsMessageLog, Qgis
import os
from .ui.dockwidget import ArchaeoTerrainExplorerDockWidget
from .tools.maptool import ArchaeoTerrainExplorerMapTool
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QCoreApplication, QSettings, QTranslator
from qgis.PyQt.QtCore import Qt

class ArchaeoTerrainExplorerPlugin:

    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.dock = None
        self.maptool = None

        # Percorso del plugin
        self.plugin_dir = os.path.dirname(__file__)

        # -------------------------
        # Translation loader
        # -------------------------
        locale = QSettings().value("locale/userLocale", "en")[0:2]  # 'it', 'en', ...
        qm_path = os.path.join(
            self.plugin_dir,
            "i18n",
            f"ArchaeoTerrainExplorer_{locale}.qm"
        )

        self.translator = None
        if os.path.exists(qm_path):
            self.translator = QTranslator()
            if self.translator.load(qm_path):
                QCoreApplication.installTranslator(self.translator)

    # -------------------------
    # Translation helper
    # -------------------------
    def tr(self, message: str) -> str:
        return QCoreApplication.translate("ArchaeoTerrainExplorer", message)
    
    def initGui(self):
        # Crea azione con icona
        icon_path = os.path.join(self.plugin_dir, "icons", "icon.png")
        self.action = QAction(
            QIcon(icon_path),
            self.tr("ArchaeoTerrain Explorer"),
            self.iface.mainWindow()
        )

        self.action.triggered.connect(self.open_dock)

        # Aggiungi icona alla toolbar
        self.iface.addToolBarIcon(self.action)

        # Crea dock SOLO se non esiste già
        if self.dock is None:
            self.dock = ArchaeoTerrainExplorerDockWidget(self.iface)
            self.iface.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock)

        # Crea MapTool
        if self.maptool is None:
            self.maptool = ArchaeoTerrainExplorerMapTool(self.iface.mapCanvas(), self.dock)

        # Collega il MapTool al dock
        self.dock.set_maptool(self.maptool)

        
    def unload(self):
        # Rimuovi icona toolbar
        if self.action:
            try:
                self.iface.removeToolBarIcon(self.action)
            except:
                pass

        # Rimuovi dock
        if self.dock:
            try:
                self.iface.removeDockWidget(self.dock)
            except:
                pass

        self.action = None
        self.dock = None
        self.maptool = None


    def open_dock(self):
        if self.dock is None:
            return
        self.dock.show()
        self.dock.raise_()
        self.dock.setVisible(True)


    def toggle(self, checked):
        if checked:
            if not self._check_layer():
                QMessageBox.warning(None, "ATE", self.tr("Select a DEM raster layer."))
                self.action.setChecked(False)
                return

            self.dock.show()
          
        else:
            self.dock.hide()
           

    def _check_layer(self):
        return isinstance(self.iface.activeLayer(), QgsRasterLayer)
