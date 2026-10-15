# **Nepal Aviation in Motion**

# 

# **A terrain-aware animation of historical aircraft movements across Nepal and the Himalayan region, covering 14–16 September 2026 (Nepal Standard Time, NPT).**

# 

# **The renderer creates an animated GIF with a dedicated header above the map, terrain shading, Nepal's boundary, airport markers, aircraft positions, and flight trails. Flight paths may extend up to 40 km beyond Nepal's boundary and fade out progressively.**

# 

# **Animation Preview**

# 

# 

# 

# **Preview Images**

# 

# **Historical Aviation Visualization**

# 

# 

# 

# **Editorial Preview**

# 

# 

# 

# **Features**

# 

# **Historical aircraft trajectory visualization**

# 

# **Terrain-aware map of Nepal and the Himalayan region**

# 

# **Shaded-relief terrain background**

# 

# **Nepal national boundary and airport markers**

# 

# **Aircraft positions and flight trails**

# 

# **Flight paths extending beyond the national boundary with progressive fading**

# 

# **Animated visualization of three days of flight activity**

# 

# **Python-based geospatial processing and rendering**

# 

# **Project Structure**

# 

# **nepal-aviation-in-motion/**

# **├── README.md**

# **├── requirements.txt**

# **├── .gitignore**

# **├── images/**

# **│   ├── nepal\_aviation\_sep14\_16\_40km\_fade.gif**

# **│   ├── nepal\_aviation\_september\_2026\_red\_spider\_preview.png**

# **│   └── nepal\_aviation\_v27\_editorial\_preview.png**

# **└── scripts/**

# &#x20;   **├── download\_nepal\_dem\_tiles.py**

# &#x20;   **└── v3\_animate\_nepal\_aviation\_3days\_40km\_fade.py**

# 

# **Technologies**

# 

# **Python**

# 

# **NumPy**

# 

# **Pandas**

# 

# **Matplotlib**

# 

# **Rasterio**

# 

# **Shapely**

# 

# **PyProj**

# 

# **Pillow**

# 

# **FFmpeg**

# 

# **See requirements.txt for the Python package list.**

# 

# **Installation**

# 

# **1. Install Python**

# 

# **Install Python 3.13 from the official website:**

# 

# **https://www.python.org/downloads/**

# 

# **During installation on Windows, enable the option to add Python to PATH if available.**

# 

# **2. Install FFmpeg**

# 

# **FFmpeg is used for video and animation processing.**

# 

# **Official download and installation instructions:**

# 

# **https://ffmpeg.org/download.html**

# 

# **After installation, ensure that FFmpeg is available on your system PATH.**

# 

# **3. Clone the repository**

# 

# **Install Git if necessary:**

# 

# **https://git-scm.com/downloads**

# 

# **Then open PowerShell or a terminal and run:**

# 

# **git clone https://github.com/prakash023/Nepal-aviation-in-motion.git**

# **cd Nepal-aviation-in-motion**

# 

# **4. Create a virtual environment**

# 

# **On Windows:**

# 

# **py -3.13 -m venv .venv**

# **.\\.venv\\Scripts\\Activate.ps1**

# 

# **If PowerShell blocks activation, you can install packages using the environment's Python executable directly instead.**

# 

# **5. Install Python dependencies**

# 

# **python -m pip install --upgrade pip**

# **pip install -r requirements.txt**

# 

# **Data Requirements**

# 

# **The large source datasets are not included in this repository. Users must obtain the required data separately.**

# 

# **The animation requires:**

# 

# **Aircraft trajectories: the historical flight-position CSV dataset for the selected period**

# 

# **Nepal boundary: a GeoJSON or equivalent boundary dataset**

# 

# **Digital Elevation Model (DEM): terrain elevation data covering Nepal and the surrounding Himalayan region**

# 

# **Use data sources that permit your intended use, and follow their attribution and redistribution requirements.**

# 

# **Downloading the DEM**

# 

# **A Python downloader is included:**

# 

# **scripts/download\_nepal\_dem\_tiles.py**

# 

# **Review the script to understand its data source, output directory, and any required configuration before running it.**

# 

# **Run it from the repository root:**

# 

# **python scripts/download\_nepal\_dem\_tiles.py**

# 

# **The downloader's output paths may need to be configured for your computer. The DEM must be available at the location expected by the renderer before generating an animation.**

# 

# **Generate the Animation**

# 

# **After obtaining the required datasets and configuring their paths, run:**

# 

# **python scripts/v3\_animate\_nepal\_aviation\_3days\_40km\_fade.py**

# 

# **The renderer processes the input data and generates an animation. Output location and rendering settings are defined in the Python script.**

# 

# **Note: The current scripts may contain machine-specific file paths. Review and adjust those paths for your own environment before running the workflow.**

# 

# **Acknowledgements and Inspiration**

# 

# **This project was inspired by the creative work of geospatial visualization artists and developers, including Milos GIS, as well as other projects shared by the GIS, mapping, and data visualization communities.**

# 

# **These examples motivated me to explore ways of visualizing aviation movements by combining historical flight data, Python, geospatial analysis, and terrain across Nepal and the Himalayas.**

# 

# **Nepal Aviation in Motion is an independent project focused on Nepal's aviation activity. Inspiration does not imply direct collaboration or endorsement.**

# 

# **Any third-party code, datasets, or assets reused in the project should be credited separately, in accordance with their licences.**

# 

# **Limitations**

# 

# **The animation represents historical data for the specified period; it is not a live air-traffic tracking service.**

# 

# **Flight coverage depends on the completeness and quality of the underlying dataset.**

# 

# **Terrain and boundary accuracy depend on the source datasets.**

# 

# **Reproducing the animation requires obtaining the necessary input data and configuring local paths.**

# 

# **Licence**

# 

# **A project licence has not yet been specified. Until one is added, do not assume that the project's code, images, or third-party data may be freely reused. Check the relevant data and software licences before redistribution.**

# 

# **Created as an independent GIS, Python, and geospatial visualization project exploring Nepal's aviation activity.**

