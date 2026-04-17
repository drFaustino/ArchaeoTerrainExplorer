# -*- coding: utf-8 -*-

import os
from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QDockWidget, QFileDialog, QMessageBox
from qgis.PyQt.QtGui import QImage, QPixmap
from qgis.PyQt.QtWidgets import QProgressBar

from qgis.PyQt.QtCore import QCoreApplication

UI_PATH = os.path.join(
    os.path.dirname(__file__),
    "dockwidget_base.ui"
)

FORM_CLASS, _ = uic.loadUiType(UI_PATH)


class ArchaeoTerrainExplorerDockWidget(QDockWidget, FORM_CLASS):

    def __init__(self, iface):
        super().__init__(iface.mainWindow())
        self.iface = iface
        self.maptool = None   # verrà impostato dal plugin
        self.setupUi(self)

        self._init_preview()  # preview

        self.setWindowTitle(self.tr("ArchaeoTerrain Explorer"))

        # Qt6 correct dock areas
        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea |
            Qt.DockWidgetArea.RightDockWidgetArea
        )

        # Pick
        self.btnActivateTool.clicked.connect(self.on_activate_one_shot)
        
        # Refresh
        self.btnRefresh.clicked.connect(self._refresh)

        # Cancel
        self.btnClear.clicked.connect(self._clear_preview)

        # Export (GeoTIFF / PNG)
        self.btnExport.clicked.connect(self._export_dispatch)

    def tr(self, message):
        return QCoreApplication.translate("ArchaeoTerrainExplorer", message)

    def _init_preview(self):
        img = QImage(320, 320, QImage.Format.Format_RGB32)
        img.fill(Qt.GlobalColor.white)
        self.labelMain.setPixmap(QPixmap.fromImage(img))

    def set_maptool(self, maptool):
        self.maptool = maptool
        try:
            self.btnRecompute.clicked.disconnect()
        except TypeError:
            pass
        self.btnRecompute.clicked.connect(self._recompute)

    def _recompute(self):
        print("DEBUG: btnRecompute premuto")
        if self.maptool is not None and hasattr(self.maptool, "recompute_last_point"):
            print("DEBUG: chiamo recompute_last_point()")
            self.maptool.recompute_last_point()
        else:
            print("DEBUG: maptool mancante o senza recompute_last_point")


    def recompute_last_point(self):
        if self._last_dem is None or self._last_res is None:
            return

        dem = self._last_dem
        res = self._last_res

        self._progress(10)
        self._last_s = slope(dem, res)

        self._progress(30)
        self._last_c = curvature(dem, res)

        self._progress(50)
        self._last_l = lrm(dem)

        preset = self.dock.comboPreset.currentText()
        filter_mode = self.dock.comboFilter.currentText()

        need_hs = filter_mode == "Hillshade"
        need_op_pos = filter_mode == "Openness+" or preset.startswith("Archaeo‑Enhance 1")
        need_op_neg = filter_mode == "Openness-" or preset.startswith("Paleochannel Finder")
        need_svf = filter_mode == "SVF" or preset.startswith("Archaeo‑Enhance 2")
        need_msrm = filter_mode == "MSRM"

        self._progress(60)
        self._ensure_advanced_metrics(
            need_hs=need_hs,
            need_op_pos=need_op_pos,
            need_op_neg=need_op_neg,
            need_svf=need_svf,
            need_msrm=need_msrm
        )

        self._progress(80)
        self._update_preview()

        self._progress(100)
        self._progress_reset()


    def dockArea(self):
        return Qt.DockWidgetArea.RightDockWidgetArea

    def _refresh(self):
        if self.maptool is not None and hasattr(self.maptool, "refresh_preview"):
            self.maptool.refresh_preview()
        else:
            QMessageBox.warning(self, "ATE", self.tr("Nessun punto precedente disponibile per l'aggiornamento."))


    def _export_dispatch(self):
        fmt = self.comboExportFormat.currentText()
        tool = self.iface.mapCanvas().mapTool()

        if not tool:
            QMessageBox.warning(self, "ATE", self.tr("Nessun MapTool attivo."))
            return

        if fmt == "GeoTIFF":
            if not hasattr(tool, "export_geotiff"):
                QMessageBox.warning(self, "ATE", self.tr("Funzione di export GeoTIFF non disponibile."))
                return
            tool.export_geotiff()

        else:
            if not hasattr(tool, "export_png"):
                QMessageBox.warning(self, "ATE", self.tr("Funzione di export PNG non disponibile."))
                return
            tool.export_png()
  
    def on_activate_one_shot(self):
        if self.maptool is None:
            return
        canvas = self.iface.mapCanvas()
        canvas.setMapTool(self.maptool)
        self.maptool.enable_one_shot()


    def _clear_preview(self):
        # Crea un'immagine bianca 320x320
        img = QImage(320, 320, QImage.Format.Format_RGB32)
        img.fill(Qt.GlobalColor.white)

        # Imposta la preview
        self.labelMain.setPixmap(QPixmap.fromImage(img))

        # Azzera progress bar
        bar = self.findChild(QProgressBar, "progressBar")
        if bar:
            bar.setValue(0)

        # Cancella dati memorizzati nel maptool
        if hasattr(self, "maptool") and self.maptool:
            self.maptool._last_s = None
            self.maptool._last_c = None
            self.maptool._last_l = None
            self.maptool._extent_last = None
