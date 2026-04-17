# CHANGELOG
## 1.0.0 — Initial Public Release

### Added
- Interactive 256×256 DEM window extraction centered on the clicked point.
- Real‑time computation of core terrain metrics:
  - Slope
  - Curvature (profile, plan, total)
  - Local Relief Model (LRM)
  - Hillshade
  - Openness (positive / negative)
  - Sky‑View Factor (SVF)
  - Multi‑Scale Relief Model (MSRM)
- Full set of single‑filter visualization modes:
  - Slope
  - Curvature
  - LRM
  - Hillshade
  - Openness+
  - Openness–
  - SVF
  - MSRM
- Composite mode combining Slope + Curvature + LRM.
- Archaeological presets:
  - Archaeo‑Enhance 1 (LRM + Openness+)
  - Archaeo‑Enhance 2 (SVF + Curvature)
  - Anthropic Edge Detector (Curvature + Slope)
  - Paleochannel Finder (LRM + Openness–)
  - Custom mode
- Scan Mode for continuous preview while moving the cursor.
- Recompute Preview button to refresh the same point after changing filters or parameters.
- Advanced parameter controls:
  - Hillshade azimuth & altitude
  - Openness/SVF radius
  - MSRM small/large scale
  - Optional smoothing for LRM
- Colormap system with 9 scientific palettes:
  - Mono
  - Earth
  - Sand
  - Clay‑Green
  - Shadowed
  - Oxide
  - Relief Shading (USGS‑style)
  - ArchaeoGold
  - Buried Structures
- Dynamic progress bar for all computations.
- PNG and GeoTIFF export, with georeferencing for GeoTIFF.
- Dockable UI panel with collapsible sections.
- Custom MapTool with crosshair cursor.
- Automatic shape matching for all metrics.
- NaN‑safe normalization with percentile clipping.
- Translation system (English/Italian) with automatic locale detection.
- QGIS 4‑compatible raster block extraction and safe array conversion.

### Improved
- Robust handling of invalid raster blocks and coordinate transforms.
- Stable preview rendering with smooth scaling and color‑mapping.
- Optimized LRM, curvature and MSRM computations for small DEM windows.
- More reliable dock initialization and cleanup on plugin unload.
- Enhanced UI responsiveness during heavy computations.

### Fixed
- Prevented preview freezing during metric computation.
- Ensured consistent array shapes across all filters.
- Corrected toolbar icon loading without Qt resource system.
- Resolved issues with MapTool activation and dock visibility.
- Eliminated duplicate entries in QGIS Panels menu.
- Improved error handling for missing or invalid DEM data.