# Nepal Aviation in Motion

A terrain-aware animation of historical aircraft movements across Nepal and the Himalayan region, covering 14–16 September 2026 (Nepal Standard Time, NPT).

The renderer creates a GIF with a dedicated header above the map, terrain shading, Nepal's boundary, airport markers, aircraft positions, and flight trails. Flight paths may extend up to 40 km beyond Nepal's boundary and fade out progressively.

![Nepal Aviation in Motion preview](images/preview.png)

## What you need

- **Windows 10/11 (the current renderer uses Windows paths)
- **Python 3.13 — [official Python downloads](https://www.python.org/downloads/)
- **Git** (optional, if you want to clone the repository) — [official Git downloads](https://git-scm.com/downloads)
- FFmpeg — [official FFmpeg download page](https://ffmpeg.org/download.html). Install a Windows build and add its `bin` directory to your `PATH` so `ffmpeg -version` works in PowerShell.
- The three input data files listed in [Input data](#input-data)

## Installation

### 1. Get the project

Either download the repository as a ZIP from GitHub and extract it, or use Git:

```powershell
git clone https://github.com/YOUR-USERNAME/nepal-aviation-in-motion.git
cd nepal-aviation-in-motion
```

Run these commands from the project root:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, you can skip activation and use the environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Check FFmpeg

Open a new PowerShell window and run:

```powershell
ffmpeg -version
```

If PowerShell says that `ffmpeg` is not recognized, install FFmpeg and add its `bin` folder to `PATH`, then reopen PowerShell.

## Input data

The animation cannot be generated from the code alone. You must obtain the required source data separately and ensure you have permission to use it.

The current script expects these files on the original Windows setup:

```text
I:\ForgeD\NepalAviation\data\september_2026\september_2026_trajectories_only.csv
I:\ForgeD\NepalAviation\data\boundary\nepal_boundary.geojson
I:\ForgeD\Traffic_visualisation\data\terrain\nepal_dem_clipped.tif
```

- Trajectory CSV: historical aircraft positions for September 2026. Use the same schema expected by the renderer.
- Nepal boundary GeoJSON: polygon boundary used for clipping and the 40 km fade-out area.
- Nepal DEM GeoTIFF: terrain raster used for the shaded-relief background.

These datasets are not included in this repository. Check the original providers' licences and redistribution terms before sharing or publishing them.

### Important: configure your paths

The current renderer has the original author's Windows paths hard-coded near the top of `scripts/v3_animate_nepal_aviation_3days_40km_fade.py`, in the `PROJECT` and `DATA` variables. Before running it on another computer, edit those variables and make sure the three input files exist at the resulting paths. The output GIF is written to the `output` directory under `PROJECT`.

This path setup is a limitation of the current version; the project is not yet fully portable just by cloning the repository and installing requirements.

## Run the animation

From the project root, with the virtual environment activated and the data paths configured, run:

```powershell
python .\scripts\v3_animate_nepal_aviation_3days_40km_fade.py
```

The script writes:

```text
nepal_aviation_sep14_16_40km_fade.gif
```

inside the configured `PROJECT\output` directory. Rendering may take some time and requires enough free disk space for temporary video and GIF files.

## Project structure

```text
nepal-aviation-in-motion/
├── README.md
├── requirements.txt
├── .gitignore
├── scripts/
├   ── download_nepal_dem_tiles.py
│   └── v3_animate_nepal_aviation_3days_40km_fade.py
├── images/
│   └── preview.png
└── animation/
    └── nepal_aviation_sep14_16_40km_fade.gif  # add your rendered GIF here
```

## Notes

- This is a visualization of historical data, not a live air-traffic tracking service.
- The preview image is illustrative; replace it with a frame from the final animation if you prefer.
- Large trajectory CSVs and DEM rasters are intentionally excluded from the repository.
- The repository's Python package list is in [`requirements.txt`](requirements.txt).



## Acknowledgements & Inspiration

This project was inspired by the creative work of geospatial visualization artists and developers, as well as other projects shared by the GIS, mapping, and data visualization communities.

These examples motivated me to explore new ways of visualizing aviation movements by combining historical flight data, Python, geospatial analysis, and 3D terrain across Nepal and the Himalayas.

Nepal Aviation in Motion is an independent project developed to explore and visualize Nepal's aviation activity.

All original creators deserve credit for their respective work. Any code, data, or assets reused from other projects will be credited separately where applicable.