# ArchaeoTerrainExplorer

## Interactive Micro‑Topographic Explorer for Archaeological Prospection

**ArchaeoTerrainExplorer** is a QGIS plugin designed for high‑resolution archaeological terrain analysis using DEM, LiDAR and photogrammetric surfaces.
It extracts a **256×256 DEM window** around the clicked point and computes **real‑time micro‑topographic metrics**, offering both **single‑filter modes** and **archaeological presets** with dynamic preview rendering.

The tool is optimized for rapid interpretation of subtle anthropic and geomorphological features such as tumuli, platforms, paleochannels, ditches, enclosures, buried structures and micro‑relief anomalies.

---

## Key Features

### Interactive Micro‑Topography
- Extracts a **256×256 DEM window** centered on the clicked point.
- Real‑time computation of:
    - Slope (Local gradient magnitude)
    - Curvature (profile, plan, total)
    - Local Relief Model (LRM)
    - Hillshade (Illumination model using azimuth and altitude)
    - Openness (positive / negative)
    - Sky‑View Factor (SVF)
    - Multi‑Scale Relief Model (MSRM)

### Terrain Filters
ArchaeoTerrainExplorer provides a complete suite of analytical and visualization filters for archaeological and geomorphological interpretation.
Each filter operates on the local DEM window and is normalized for consistent display.

### Visualization Modes
- **Composite mode** (Slope + Curvature + LRM)
    A balanced micro‑topographic blend combining slope (edges), curvature (convex/concave forms) and LRM (local anomalies). Ideal as a general‑purpose archaeological visualization for rapid interpretation of subtle relief features.
- **Single‑filter modes**:
    - Slope (Local gradient magnitude)
        Highlights rapid elevation changes and sharp breaks of slope. Useful for detecting scarps, banks, cuts, edges and anthropic discontinuities.
    - Curvature
        Emphasizes convex and concave forms through second‑derivative analysis. Convexities (mounds, ridges) and concavities (ditches, depressions) become immediately visible.
    - LRM (Local Relief Model)
        Extracts micro‑relief by subtracting large‑scale terrain trends. Excellent for subtle anthropic structures, platforms, tumuli, and faint geomorphological anomalies.
    - Hillshade
        Simulated illumination based on azimuth and altitude. Provides intuitive terrain shading and helps contextualize micro‑relief within broader morphology.
    - Openness+
        Measures the degree of sky visibility in upward directions. Enhances convex features such as mounds, ridges, tumuli and elevated anthropic structures.
    - Openness–
        Captures downward openness, emphasizing concave forms. Ideal for detecting ditches, paleochannels, fossati, depressions and negative relief features.
    - SVF (Sky‑View Factor)
        Directional horizon‑based metric expressing how much of the sky is visible. Excellent for subtle concavities, buried structures, enclosures and low‑contrast archaeological features.
    - MSRM (Multi‑Scale Relief Model)
        Multi‑scale residual analysis combining several smoothing radii. Reveals broad, faint archaeological and geomorphological patterns that are invisible in single‑scale filters.

### Archaeological Presets
Optimized combinations for archaeological anomaly detection.

- **Custom**
    User‑defined combination based on selected filter and colormap.
    Use for: experimentation and fine‑tuning.
- **Archaeo‑Enhance 1 (LRM + Openness+)**
    0.6 LRM + 0.4 Openness+  
    Highlights: convex anthropogenic features (mounds, tumuli, platforms).
    Use for: raised archaeological structures.
- **Archaeo‑Enhance 2 (SVF + Curvature)**
    0.5 SVF + 0.5 Curvature  
    Highlights: subtle convex/concave forms with smooth shading.
    Use for: faint archaeological anomalies and low‑contrast terrain.
-   **Anthropic Edge Detector (Curvature + Slope)**
    0.5 Curvature + 0.5 Slope  
    Highlights: sharp anthropogenic edges, ditches, embankments.
    Use for: fortifications, enclosures, ramparts, linear boundaries.
-   **Paleochannel Finder (LRM + Openness–)**
    0.6 LRM + 0.4 Openness–  
    Highlights: negative relief such as palaeochannels, ancient riverbeds, ditches.
    Use for: reconstructing ancient hydrology and buried channels.

### Advanced Interaction
- **Scan Mode**: continuous preview while moving the cursor
- **Recompute Preview**: refresh the same point after changing filters
- **Dynamic progress bar** for all computations
- A**utomatic shape matching** for all metrics
- **NaN‑safe normalization** and percentile clipping

### Colormap System (9 Palettes)
- Mono
    Pure grayscale representation. Ideal for neutral, non‑interpreted visualization and for comparing raw filter outputs without color bias.
- Earth
    Brown–ochre to beige tones. Excellent for LRM, SVF and MSRM, providing a naturalistic terrain feel while preserving micro‑relief readability.
- Sand
    Light sand‑colored gradient. Optimized for highlighting positive features such as tumuli, platforms, dunes and anthropic rises.
- Clay‑Green
    Olive‑green to light‑green palette. Designed for concavities, fossati, paleochannels and negative relief features, improving contrast in depressions.
- Shadowed
    Gray to deep blue tones. Emphasizes shaded or deeply concave areas, useful for detecting cuts, hollows and negative micro‑relief.
- Oxide
    Mineral‑oxide gradient from gray to reddish‑brown. Ideal for curvature, SVF and MSRM, enhancing subtle structural variations and buried features.
- Relief Shading (USGS‑style)
    Soft neutral shading inspired by classic USGS maps. Provides intuitive terrain readability with gentle contrast, excellent for general interpretation.
- ArchaeoGold
    Gold–ochre palette. Highlights mounds, platforms, tumuli and positive anthropic structures with strong visual prominence.
- Buried Structures
    Cool‑to‑warm gradient (blue → cyan → yellow → orange). Designed to reveal alignments, buried structures, linear anomalies and subtle archaeological patterns.

### Export
- Export GeoTIFF with georeferencing
- Export PNG preview

### UI and Integration
- Dockable panel with collapsible sections
- Custom MapTool with crosshair cursor
- Full translation system (English/Italian)
- QGIS 4‑compatible raster extraction and block handling

---

## How It Works

1. Click on the DEM (or move the cursor in Scan Mode). 
2. The plugin extracts a 256×256 raster block around the point.
3. Terrain metrics are computed on‑the‑fly:
    - slope and curvature via finite differences
    - LRM via multi‑scale smoothing
    - hillshade via gradient‑based illumination
    - openness and SVF via directional horizon scanning
    - MSRM via multi‑scale residuals
4. The preview is normalized, color‑mapped and displayed in the dock.
5. Users can switch filters, presets, parameters or colormaps and recompute instantly.

---

## Requirements
- QGIS **4.x**
- Python 3
- PyQt6 / Qt6
- A valid raster layer (DEM, LiDAR, photogrammetry)

---

## License

This plugin is released under the **GNU GPL v3** license.

---

## Author

**Dr. Geol. Faustino Cetraro**  
Geologist, scientific communicator, and developer of geomorphological tools for QGIS.

---

## Changelog

See [`CHANGELOG.md`](CHANGELOG.md) for full version history.  
Version **1.0.0** corresponds to the **first public release (initial version 1.0)**.

## Interface

<img width="1160" height="811" alt="img1" src="https://github.com/user-attachments/assets/07aa8e16-3fe9-4f52-abb4-eedd5c47a37a" />
