import numpy as np
from osgeo import gdal, osr

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QImage, QPixmap
from qgis.gui import QgsMapTool
from qgis.utils import iface

from qgis.PyQt.QtWidgets import QLabel, QProgressBar, QFileDialog, QMessageBox
from qgis.core import (
    QgsRasterLayer,
    QgsRectangle,
    QgsCoordinateTransform,
    QgsProject,
)

from ..core.raster_engine import raster_block_to_array
from ..core.metrics import slope, curvature
from ..core.filters import multi_scale_lrm as lrm
from ..core.terrain_filters import hillshade, openness, sky_view_factor, msrm
from qgis.PyQt.QtCore import QCoreApplication

class ArchaeoTerrainExplorerMapTool(QgsMapTool):

    def __init__(self, canvas, dock):
        super().__init__(canvas)
        self.canvas = canvas
        self.dock = dock
       
        # stato metriche
        self._last_dem = None
        self._last_res = None
        self._last_s = None
        self._last_c = None
        self._last_l = None
        self._last_hs = None
        self._last_op_pos = None
        self._last_op_neg = None
        self._last_svf = None
        self._last_msrm = None
        self._extent_last = None
        self._one_shot = False


    def tr(self, message):
        return QCoreApplication.translate("ArchaeoTerrainExplorer", message)

    def enable_one_shot(self):
        self._one_shot = True

    def activate(self):
        super().activate()
        self.canvas.setCursor(Qt.CursorShape.CrossCursor)

    def deactivate(self):
        super().deactivate()
        self.canvas.setCursor(Qt.CursorShape.ArrowCursor)

    # ---------------------------------------------------------
    # EVENTI MAPTOOL
    # ---------------------------------------------------------
    
    def canvasReleaseEvent(self, event):
        if hasattr(self.dock, "btnScanMode") and self.dock.btnScanMode.isChecked():
            return

        pos = event.position().toPoint()
        self._process_point(pos)

        # --- ONE SHOT MODE ---
        if self._one_shot:
            self.canvas.unsetMapTool(self)
            self._one_shot = False
            self.canvas.setCursor(Qt.CursorShape.ArrowCursor)

    def canvasMoveEvent(self, event):
        if hasattr(self.dock, "btnScanMode") and self.dock.btnScanMode.isChecked():
            pos = event.position().toPoint()
            self._process_point(pos)

    def _process_point(self, pos):
        layer = iface.activeLayer()
        if not isinstance(layer, QgsRasterLayer):
            return

        point = self.toMapCoordinates(pos)

        crs_canvas = self.canvas.mapSettings().destinationCrs()
        crs_raster = layer.crs()

        try:
            transform = QgsCoordinateTransform(crs_canvas, crs_raster, QgsProject.instance())
            point_raster = transform.transform(point)
        except Exception:
            self._progress_reset()
            return

        self._progress(5)
        extent = self._extent(point_raster, layer)
        self._extent_last = extent

        res = layer.rasterUnitsPerPixelX()
        width = int(extent.width() / res)
        height = int(extent.height() / res)

        self._progress(15)
        block = layer.dataProvider().block(1, extent, width, height)
        if not block:
            self._progress_reset()
            return

        self._progress(30)
        arr = raster_block_to_array(block)
        arr[arr <= -1e20] = np.nan
        if np.all(np.isnan(arr)):
            self._progress_reset()
            return

        self._last_dem = arr
        self._last_res = res

        # metriche base
        self._progress(45)
        self._last_s = slope(arr, res)

        self._progress(60)
        self._last_c = curvature(arr, res)

        self._progress(75)
        # LRM con smoothing opzionale
        try:
            do_smooth = self.dock.checkEnableSmoothing.isChecked()
        except AttributeError:
            do_smooth = False

        if do_smooth:
            # smoothing semplice: media mobile via lrm con small più grande
            self._last_l = lrm(arr, small=5, large=21)
        else:
            self._last_l = lrm(arr)

        preset = self.dock.comboPreset.currentText()
        filter_mode = self.dock.comboFilter.currentText()

        need_hs = filter_mode == "Hillshade"
        need_op_pos = filter_mode == "Openness+" or preset.startswith("Archaeo‑Enhance 1")
        need_op_neg = filter_mode == "Openness-" or preset.startswith("Paleochannel Finder")
        need_svf = filter_mode == "SVF" or preset.startswith("Archaeo‑Enhance 2")
        need_msrm = filter_mode == "MSRM"

        self._ensure_advanced_metrics(
            need_hs=need_hs,
            need_op_pos=need_op_pos,
            need_op_neg=need_op_neg,
            need_svf=need_svf,
            need_msrm=need_msrm
)
        self._update_preview()
       
    # ---------------------------------------------------------
    # METRICHE AVANZATE (lazy, solo se servono)
    # ---------------------------------------------------------

    def _ensure_advanced_metrics(
        self,
        need_hs=False,
        need_op_pos=False,
        need_op_neg=False,
        need_svf=False,
        need_msrm=False
    ):
        dem = self._last_dem
        res = self._last_res
        if dem is None or res is None:
            return

        ref = dem

        # parametri da UI
        az = getattr(self.dock, "spinAzimuth", None)
        alt = getattr(self.dock, "spinAltitude", None)
        radius = getattr(self.dock, "spinSVFRadius", None)
        msrm_small = getattr(self.dock, "spinMSRMSmall", None)
        msrm_large = getattr(self.dock, "spinMSRMLarge", None)

        az = az.value() if az else 315
        alt = alt.value() if alt else 45
        radius = radius.value() if radius else 7
        msrm_small = msrm_small.value() if msrm_small else 3
        msrm_large = msrm_large.value() if msrm_large else 15

        # HILLSHADE
        if need_hs and self._last_hs is None:
            raw = hillshade(dem, azimuth_deg=az, altitude_deg=alt, res=res)
            self._last_hs = self._match_shape(ref, raw)

        # OPENNESS POS
        if need_op_pos and self._last_op_pos is None:
            raw = openness(dem, radius=radius, positive=True)
            self._last_op_pos = self._match_shape(ref, raw)

        # OPENNESS NEG
        if need_op_neg and self._last_op_neg is None:
            raw = openness(dem, radius=radius, positive=False)
            self._last_op_neg = self._match_shape(ref, raw)

        # SVF
        if need_svf and self._last_svf is None:
            raw = sky_view_factor(dem, radius=radius)
            self._last_svf = self._match_shape(ref, raw)

        # MSRM multi‑scala
        if need_msrm and self._last_msrm is None:
            raw = msrm(dem, small=msrm_small, large=msrm_large, n_scales=3)
            self._last_msrm = self._match_shape(ref, raw)

    # ---------------------------------------------------------
    # REFRESH
    # ---------------------------------------------------------

    def refresh_preview(self):
        if self._last_s is not None:
            self._update_preview()

    # ---------------------------------------------------------
    # GEOMETRIA / NORMALIZZAZIONE
    # ---------------------------------------------------------

    def _extent(self, point, layer):
        res = layer.rasterUnitsPerPixelX()
        half = 128 * res
        return QgsRectangle(
            point.x() - half,
            point.y() - half,
            point.x() + half,
            point.y() + half
        )

    def _normalize(self, arr):
        a = np.nan_to_num(arr.copy())
        vmin, vmax = np.percentile(a, 2), np.percentile(a, 98)
        if vmax == vmin:
            vmax = vmin + 1
        a = np.clip(a, vmin, vmax)
        return ((a - vmin) / (vmax - vmin) * 255).astype(np.uint8)

    def _match_shape(self, ref, arr):
        ref = np.asarray(ref)
        arr = np.asarray(arr)

        if arr.ndim > 2:
            arr = arr.squeeze()

        r_h, r_w = ref.shape
        arr = arr[:r_h, :r_w]

        pad_h = max(0, r_h - arr.shape[0])
        pad_w = max(0, r_w - arr.shape[1])

        if pad_h or pad_w:
            arr = np.pad(arr, ((0, pad_h), (0, pad_w)), mode="edge")

        return arr[:r_h, :r_w]

    def _to_pixmap(self, arr):
        arr = np.ascontiguousarray(arr)

        if arr.ndim == 2:
            h, w = arr.shape
            bytes_per_line = w
            fmt = QImage.Format.Format_Grayscale8
        else:
            h, w, _ = arr.shape
            bytes_per_line = w * 3
            fmt = QImage.Format.Format_RGB888

        img = QImage(arr.data, w, h, bytes_per_line, fmt)
        return QPixmap.fromImage(img.copy())

    # ---------------------------------------------------------
    # VISUALIZZAZIONE
    # ---------------------------------------------------------

    def _update_preview(self):
        label = self.dock.findChild(QLabel, "labelMain")
        if not label:
            return

        if self._last_s is None:
            return

        s = np.asarray(self._last_s).squeeze()
        c = self._match_shape(s, np.asarray(self._last_c).squeeze())
        l = self._match_shape(s, np.asarray(self._last_l).squeeze())

        s_n = self._normalize(s)
        c_n = self._normalize(c)
        l_n = self._normalize(l)

                # lettura preset / filtro
        preset = getattr(self.dock, "comboPreset", None)
        preset = preset.currentText() if preset else "Custom"

        filter_mode = getattr(self.dock, "comboFilter", None)
        filter_mode = filter_mode.currentText() if filter_mode else "Composite"

        # filtri opzionali da UI
        chk_hs = getattr(self.dock, "checkComputeHillshade", None)
        chk_op = getattr(self.dock, "checkComputeOpenness", None)
        chk_svf = getattr(self.dock, "checkComputeSVF", None)
        chk_msrm = getattr(self.dock, "checkComputeMSRM", None)

        need_hs = (filter_mode == "Hillshade") or (chk_hs.isChecked() if chk_hs else False)
        need_op_pos = (
            filter_mode == "Openness+" or
            preset.startswith("Archaeo‑Enhance 1") or
            (chk_op.isChecked() if chk_op else False)
        )
        need_op_neg = (
            filter_mode == "Openness-" or
            preset.startswith("Paleochannel Finder") or
            (chk_op.isChecked() if chk_op else False)
        )
        need_svf = (
            filter_mode == "SVF" or
            preset.startswith("Archaeo‑Enhance 2") or
            (chk_svf.isChecked() if chk_svf else False)
        )
        need_msrm = (filter_mode == "MSRM") or (chk_msrm.isChecked() if chk_msrm else False)

        self._ensure_advanced_metrics(
            need_hs=need_hs,
            need_op_pos=need_op_pos,
            need_op_neg=need_op_neg,
            need_svf=need_svf,
            need_msrm=need_msrm
        )

        hs_n = self._normalize(self._match_shape(s, self._last_hs)) if self._last_hs is not None else None
        op_pos_n = self._normalize(self._match_shape(s, self._last_op_pos)) if self._last_op_pos is not None else None
        op_neg_n = self._normalize(self._match_shape(s, self._last_op_neg)) if self._last_op_neg is not None else None
        svf_n = self._normalize(self._match_shape(s, self._last_svf)) if self._last_svf is not None else None
        msrm_n = self._normalize(self._match_shape(s, self._last_msrm)) if self._last_msrm is not None else None

        # FILTRO SINGOLO
        if filter_mode == "Slope":
            composite = s_n
        elif filter_mode == "Curvature":
            composite = c_n
        elif filter_mode == "LRM":
            composite = l_n
        elif filter_mode == "Hillshade" and hs_n is not None:
            composite = hs_n
        elif filter_mode == "Openness+" and op_pos_n is not None:
            composite = op_pos_n
        elif filter_mode == "Openness-" and op_neg_n is not None:
            composite = op_neg_n
        elif filter_mode == "SVF" and svf_n is not None:
            composite = svf_n
        elif filter_mode == "MSRM" and msrm_n is not None:
            composite = msrm_n

        else:
            # PRESET
            if preset.startswith("Archaeo‑Enhance 1") and op_pos_n is not None:
                composite = 0.6 * l_n + 0.4 * op_pos_n
            elif preset.startswith("Archaeo‑Enhance 2") and svf_n is not None:
                composite = 0.5 * svf_n + 0.5 * c_n
            elif preset.startswith("Anthropic Edge Detector"):
                composite = 0.5 * c_n + 0.5 * s_n
            elif preset.startswith("Paleochannel Finder") and op_neg_n is not None:
                composite = 0.6 * l_n + 0.4 * op_neg_n
            else:
                composite = (
                    0.45 * s_n +
                    0.25 * c_n +
                    0.30 * l_n
                )

        composite = self._normalize(composite)

        cmap_index = self.dock.comboColormap.currentIndex()
        colored = self.apply_colormap(composite, cmap_index)
        pix = self._to_pixmap(colored)

        label.setPixmap(
            pix.scaled(
                label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )
        
        # --- CHIUSURA PROGRESS BAR ---
        self._progress(90)
        self._progress(100)
        self._progress_reset()

    def apply_colormap(self, arr, cmap_index):
        arr = np.clip(arr, 0, 255).astype(np.uint8)

        # --- 0 MONO ---
        if cmap_index == 0:
            return arr

        # --- 1 EARTH ---
        # Toni marrone‑ocra → beige → quasi bianco.
        # Ottima per LRM, SVF, MSRM.
        if cmap_index == 1:
            x = arr.astype(np.float32) / 255.0
            r = np.clip(255 * (0.55 * x + 0.35 * x**2), 0, 255)
            g = np.clip(255 * (0.45 * x + 0.25 * x**2), 0, 255)
            b = np.clip(255 * (0.30 * x + 0.15 * x**2), 0, 255)
            return np.dstack([r, g, b]).astype(np.uint8)

        # --- 2 SAND ---
        # Toni sabbia chiari → scuri.
        # Perfetta per tumuli, dune, strutture positive.
        if cmap_index == 2:
            x = arr.astype(np.float32) / 255.0
            r = np.clip(255 * (0.8 * x + 0.2), 0, 255)
            g = np.clip(255 * (0.75 * x + 0.15), 0, 255)
            b = np.clip(255 * (0.55 * x + 0.10), 0, 255)
            return np.dstack([r, g, b]).astype(np.uint8)

        # --- 3 CLAY_GREEN (nuova versione verdastra) ---
        # Toni argilla‑verdastro → ottimo per fossati, paleocanali, concavità.
        if cmap_index == 3:  # sostituisce clay
            x = arr.astype(np.float32) / 255.0
            # verde oliva → verde chiaro
            r = np.clip(255 * (0.35 * x + 0.05), 0, 255)
            g = np.clip(255 * (0.55 * x + 0.20), 0, 255)
            b = np.clip(255 * (0.30 * x + 0.10), 0, 255)
            return np.dstack([r, g, b]).astype(np.uint8)

        # --- 4 SHADOWED ---
        # Grigio → blu scuro.
        # Per evidenziare concavità profonde.
        if cmap_index == 4:
            x = arr.astype(np.float32) / 255.0
            r = np.clip(255 * (0.25 * x), 0, 255)
            g = np.clip(255 * (0.35 * x), 0, 255)
            b = np.clip(255 * (0.60 * x + 0.20), 0, 255)
            return np.dstack([r, g, b]).astype(np.uint8)

        # --- 5 OXIDE (sostituisce sepia) ---
        # Toni ossido‑minerale (grigio → rosso‑marrone)
        # Perfetta per curvature, SVF, MSRM.
        if cmap_index == 5:
            x = arr.astype(np.float32) / 255.0
            # grigio → rosso‑ossido → marrone chiaro
            r = np.clip(255 * (0.80 * x + 0.20), 0, 255)
            g = np.clip(255 * (0.45 * x + 0.10), 0, 255)
            b = np.clip(255 * (0.30 * x + 0.05), 0, 255)
            return np.dstack([r, g, b]).astype(np.uint8)

        # --- 6 RELIEF SHADING (USGS STYLE) ---
        # Simulazione di shading topografico “morbido”, con toni neutri e leggibili.
        if cmap_index == 6:
            x = arr.astype(np.float32) / 255.0
            # Toni neutri: grigio → beige chiaro
            r = np.clip(255 * (0.55 * x + 0.20), 0, 255)
            g = np.clip(255 * (0.52 * x + 0.18), 0, 255)
            b = np.clip(255 * (0.48 * x + 0.15), 0, 255)
            return np.dstack([r, g, b]).astype(np.uint8)

        # --- 7 ARCHAEOGOLD (PER TUMULI E PIATTAFORME) ---
        # Palette oro‑ocra per mettere in risalto tumuli, piattaforme, rialzi antropici.
        if cmap_index == 7:
            x = arr.astype(np.float32) / 255.0
            # Oro → ocra → sabbia
            r = np.clip(255 * (0.90 * x + 0.10), 0, 255)
            g = np.clip(255 * (0.75 * x + 0.15), 0, 255)
            b = np.clip(255 * (0.40 * x + 0.05), 0, 255)
            return np.dstack([r, g, b]).astype(np.uint8)

        # --- 8 BURIED STRUCTURES (PER STRUTTURE SEPOLTE / ALLINEAMENTI) ---
        # Palette fredda‑calda per evidenziare allineamenti, strutture sepolte, anomalie lineari.
        if cmap_index == 8:
            x = arr.astype(np.float32) / 255.0
            # Blu → ciano → giallo → arancio (molto morbido)
            r = np.clip(255 * (0.85 * x), 0, 255)
            g = np.clip(255 * (0.95 * x + 0.05), 0, 255)
            b = np.clip(255 * (0.60 * (1 - x) + 0.20), 0, 255)
            return np.dstack([r, g, b]).astype(np.uint8)

        return arr

    # ---------------------------------------------------------
    # EXPORT
    # ---------------------------------------------------------

    def export_geotiff(self):
        if self._last_s is None:
            QMessageBox.warning(None, "ATE", self.tr("Nessuna anteprima disponibile da esportare."))
            self._progress_reset()
            return

        self._progress(10)

        s = np.asarray(self._last_s).squeeze()
        c = self._match_shape(s, np.asarray(self._last_c).squeeze())
        l = self._match_shape(s, np.asarray(self._last_l).squeeze())

        s_n = self._normalize(s)
        c_n = self._normalize(c)
        l_n = self._normalize(l)

        composite = 0.45 * s_n + 0.25 * c_n + 0.30 * l_n
        composite = self._normalize(composite)

        self._progress(30)
        path, _ = QFileDialog.getSaveFileName(
            None,
            self.tr("Esporta GeoTIFF"),
            "",
            "GeoTIFF (*.tif)"
        )
        if not path:
            self._progress_reset()
            return

        self._progress(40)

        layer = self.canvas.currentLayer()
        if not isinstance(layer, QgsRasterLayer) or self._extent_last is None:
            QMessageBox.critical(None, "ATE", self.tr("Nessun raster / extent valido per l'export."))
            self._progress_reset()
            return

        crs = layer.crs()
        extent = self._extent_last

        h, w = composite.shape
        res = layer.rasterUnitsPerPixelX()

        xmin = extent.xMinimum()
        ymax = extent.yMaximum()
        geotransform = (xmin, res, 0, ymax, 0, -res)

        driver = gdal.GetDriverByName("GTiff")
        ds = driver.Create(path, w, h, 1, gdal.GDT_Byte, options=["COMPRESS=LZW"])
        if ds is None:
            QMessageBox.critical(None, "ATE", self.tr("Impossibile creare il file GeoTIFF."))
            self._progress_reset()
            return

        ds.SetGeoTransform(geotransform)

        srs = osr.SpatialReference()
        srs.ImportFromWkt(crs.toWkt())
        ds.SetProjection(srs.ExportToWkt())

        band = ds.GetRasterBand(1)
        band.WriteArray(composite.astype(np.uint8))
        band.SetNoDataValue(0)

        ds.FlushCache()
        ds = None

        self._progress(100)
        QMessageBox.information(None, "ATE", self.tr("GeoTIFF esportato correttamente."))
        self._progress_reset()

    def export_png(self):
        label = self.dock.labelMain
        pix = label.pixmap()
        if pix is None:
            QMessageBox.warning(None, "ATE", self.tr("Nessuna anteprima da esportare."))
            return

        path, _ = QFileDialog.getSaveFileName(
            None,
            self.tr("Esporta PNG"),
            "",
            "PNG (*.png)"
        )
        if not path:
            return

        pix.save(path, "PNG")
        QMessageBox.information(None, "ATE", self.tr("PNG esportato correttamente."))

    def _export_dispatch(self):
        tool = self.iface.mapCanvas().mapTool()
        if not tool:
            QMessageBox.warning(self, "ATE", self.tr("Nessun MapTool attivo."))
            return

        fmt = self.comboExportFormat.currentText()
        if fmt == "GeoTIFF":
            tool.export_geotiff()
        else:
            tool.export_png()

    # ---------------------------------------------------------
    # PROGRESS
    # ---------------------------------------------------------

    def _progress(self, value):
        bar = self.dock.findChild(QProgressBar, "progressBar")
        if bar:
            bar.setValue(value)

    def _progress_reset(self):
        bar = self.dock.findChild(QProgressBar, "progressBar")
        if bar:
            bar.setValue(0)

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

