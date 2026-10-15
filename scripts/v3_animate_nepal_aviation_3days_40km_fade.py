from pathlib import Path
import json
from datetime import datetime, timezone, timedelta
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import rasterio
from rasterio.enums import Resampling
from matplotlib.colors import LightSource, LinearSegmentedColormap
from matplotlib.collections import LineCollection
from matplotlib.animation import FuncAnimation, FFMpegWriter
import shutil
import subprocess
from shapely.geometry import shape, Polygon, MultiPolygon, LineString, Point
from shapely.ops import unary_union, transform as shapely_transform
from pyproj import CRS, Transformer
try:
    from shapely import contains_xy
except ImportError:
    from shapely.vectorized import contains as contains_xy
# ============================================================
# NEPAL AVIATION — THREE-DAY ANIMATION
# V27-inspired editorial style + red-and-black spider-web chart
# ============================================================
PROJECT = Path(r"I:\ForgeD\Traffic_visualisation")
DATA = Path(r"I:\ForgeD\NepalAviation\data")
MONTH_DATA = DATA / "september_2026"
CSV_FILE = MONTH_DATA / "september_2026_trajectories_only.csv"
BOUNDARY_FILE = DATA / "boundary" / "nepal_boundary.geojson"
DEM_FILE = PROJECT / "data" / "terrain" / "nepal_dem_clipped.tif"
OUTPUT_DIR = PROJECT / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
#OUTPUT_FILE = OUTPUT_DIR / "nepal_aviation_september_2026_red_spider_preview.png"
OUTPUT_FILE = OUTPUT_DIR / "nepal_aviation_sep14_16_40km_fade.gif"
TEMP_VIDEO = OUTPUT_DIR / "nepal_aviation_sep14_16_40km_fade_temp.mp4"
PALETTE_FILE = OUTPUT_DIR / "nepal_aviation_sep14_16_40km_fade_palette.png"
FRAME_STEP_MINUTES = 5
FPS = 15
NEPAL_TZ = timezone(timedelta(hours=5, minutes=45))
BACKGROUND = "#07111F"
BORDER_COLOR = "#F2E8D5"
TEXT_COLOR = "#E8F0F7"
MUTED_COLOR = "#A5AAB5"
#START = pd.Timestamp("2026-09-01T00:00:00Z")
#END = pd.Timestamp("2026-10-01T00:00:00Z")
# Exact three Nepal-time days: 14–16 September inclusive (NPT = UTC+05:45).
START = pd.Timestamp("2026-09-13T18:15:00Z")
END = pd.Timestamp("2026-09-16T18:15:00Z")
COLORS = {
    "Nepal": "#F7CE46",
    "India": "#54D8F5",
    "Turkish Airlines": "#72F0C4",
    "Gulf": "#FF795E",
    "Other international": "#F052AC",
    "Unknown": "#A5B2C2",
}
PREFIX_GROUP = {
    "BHA": "Nepal",
    "NYT": "Nepal",
    "SHA": "Nepal",
    "TRA": "Nepal",
    "HIM": "Nepal",
    "RNA": "Nepal",
    "STA": "Nepal",
    "IGO": "India",
    "AIC": "India",
    "THY": "Turkish Airlines",
    "QTR": "Gulf",
    "FDB": "Gulf",
    "JZR": "Gulf",
    "ABY": "Gulf",
}
def airline_group(callsign):
    value = str(callsign or "").strip().upper()
    if not value or value == "NAN":
        return "Unknown"
    prefix = "".join(ch for ch in value if ch.isalpha())[:3]
    return PREFIX_GROUP.get(prefix, "Other international")
# ------------------------------------------------------------
# Load and prepare September trajectory data
# ------------------------------------------------------------
print("Loading September trajectory data...", flush=True)
if not CSV_FILE.exists():
    raise FileNotFoundError(f"Trajectory CSV not found: {CSV_FILE}")
df = pd.read_csv(CSV_FILE)
required = {
    "flight_id", "timestamp_utc", "longitude", "latitude",
    "callsign", "segment_id", "point_index",
}
missing = required - set(df.columns)
if missing:
    raise ValueError(f"Missing CSV columns: {sorted(missing)}")
df["timestamp_utc"] = pd.to_datetime(
    df["timestamp_utc"], utc=True, errors="coerce"
)
for column in ["longitude", "latitude"]:
    df[column] = pd.to_numeric(df[column], errors="coerce")
df = df.dropna(
    subset=["flight_id", "timestamp_utc", "longitude", "latitude"]
).copy()
df = df.loc[
    (df["timestamp_utc"] >= START) & (df["timestamp_utc"] < END)
].copy()
if df.empty:
    raise ValueError("No September trajectory positions found.")
df["flight_id"] = df["flight_id"].astype(str)
df["callsign"] = df["callsign"].fillna("").astype(str).str.strip()
df["unix_time"] = df["timestamp_utc"].apply(lambda t: t.timestamp())
df["airline_group"] = df["callsign"].map(airline_group)
print(f"September positions: {len(df):,}", flush=True)
print(f"Flight IDs: {df['flight_id'].nunique():,}", flush=True)
# ------------------------------------------------------------
# Average recorded flight activity by Nepal-time hour
# across the selected three days.
# ------------------------------------------------------------
df["timestamp_npt"] = df["timestamp_utc"].dt.tz_convert("Asia/Kathmandu")
df["npt_date"] = df["timestamp_npt"].dt.date
df["npt_hour"] = df["timestamp_npt"].dt.hour
daily_hourly = df.groupby(["npt_date", "npt_hour"])["flight_id"].nunique()
selected_dates = sorted(df["npt_date"].unique())
complete_index = pd.MultiIndex.from_product(
    [selected_dates, range(24)], names=["npt_date", "npt_hour"]
)
chart_values = (
    daily_hourly.reindex(complete_index, fill_value=0)
    .groupby(level="npt_hour")
    .mean()
    .reindex(range(24), fill_value=0)
    .to_numpy(dtype=float)
)
# Build a three-day timeline. One frame every five minutes keeps the
# first full animation manageable while retaining the movement pattern.
frame_step_seconds = FRAME_STEP_MINUTES * 60
frame_epochs = np.arange(
    START.timestamp(), END.timestamp(), frame_step_seconds, dtype=float
)
if len(frame_epochs) == 0:
    raise ValueError("The selected animation period contains no frames.")

preview_epoch = float(frame_epochs[0])
local_time = datetime.fromtimestamp(
    preview_epoch, timezone.utc
).astimezone(NEPAL_TZ)
current_hour = local_time.hour + local_time.minute / 60
# ------------------------------------------------------------
# Load Nepal boundary
# ------------------------------------------------------------
if not BOUNDARY_FILE.exists():
    raise FileNotFoundError(f"Nepal boundary not found: {BOUNDARY_FILE}")
with BOUNDARY_FILE.open("r", encoding="utf-8") as f:
    boundary_data = json.load(f)
if boundary_data.get("type") == "FeatureCollection":
    nepal = unary_union([
        shape(feature["geometry"])
        for feature in boundary_data["features"]
        if feature.get("geometry")
    ])
elif boundary_data.get("type") == "Feature":
    nepal = shape(boundary_data["geometry"])
else:
    nepal = shape(boundary_data)
if nepal.is_empty:
    raise ValueError("Nepal boundary geometry is empty.")
if isinstance(nepal, Polygon):
    polygons = [nepal]
elif isinstance(nepal, MultiPolygon):
    polygons = list(nepal.geoms)
else:
    polygons = [
        geom for geom in getattr(nepal, "geoms", [])
        if isinstance(geom, Polygon)
    ]

# Create a true 40 km buffer in a local metric projection, then transform back.
# Aircraft may be shown just outside Nepal; they fade out by the buffer edge.
center = nepal.representative_point()
local_crs = CRS.from_proj4(
    f"+proj=aeqd +lat_0={center.y} +lon_0={center.x} +datum=WGS84 +units=m +no_defs"
)
to_local = Transformer.from_crs("EPSG:4326", local_crs, always_xy=True).transform
to_wgs84 = Transformer.from_crs(local_crs, "EPSG:4326", always_xy=True).transform
nepal_metric = shapely_transform(to_local, nepal)
nepal_buffer_metric = nepal_metric.buffer(40000)
nepal_buffer = shapely_transform(to_wgs84, nepal_buffer_metric)
print("Aircraft visibility buffer: 40 km beyond Nepal boundary", flush=True)

# Restrict the activity radar and flight totals to recorded positions inside Nepal.
inside_mask = contains_xy(
    nepal, df["longitude"].to_numpy(dtype=float), df["latitude"].to_numpy(dtype=float)
)
df_nepal = df.loc[inside_mask].copy()
if df_nepal.empty:
    raise ValueError("No recorded aircraft positions fall inside Nepal for this period.")
df_nepal["timestamp_npt"] = df_nepal["timestamp_utc"].dt.tz_convert("Asia/Kathmandu")
df_nepal["npt_date"] = df_nepal["timestamp_npt"].dt.date
df_nepal["npt_hour"] = df_nepal["timestamp_npt"].dt.hour
daily_hourly_nepal = df_nepal.groupby(["npt_date", "npt_hour"])["flight_id"].nunique()
selected_dates_nepal = sorted(df_nepal["npt_date"].unique())
complete_index_nepal = pd.MultiIndex.from_product(
    [selected_dates_nepal, range(24)], names=["npt_date", "npt_hour"]
)
chart_values = (
    daily_hourly_nepal.reindex(complete_index_nepal, fill_value=0)
    .groupby(level="npt_hour")
    .mean()
    .reindex(range(24), fill_value=0)
    .to_numpy(dtype=float)
)
print(f"Positions inside Nepal: {len(df_nepal):,}", flush=True)
print(f"Flights recorded inside Nepal: {df_nepal['flight_id'].nunique():,}", flush=True)

# ------------------------------------------------------------
# Prepare figure and terrain
# ------------------------------------------------------------
fig, ax = plt.subplots(figsize=(16, 9), dpi=100)
fig.patch.set_facecolor(BACKGROUND)
ax.set_facecolor(BACKGROUND)
# Reserve a dedicated top header so editorial text never overlaps the terrain.
ax.set_position([0.025, 0.035, 0.95, 0.755])
minx, miny, maxx, maxy = nepal_buffer.bounds
ax.set_xlim(minx - 0.08, maxx + 0.08)
ax.set_ylim(miny - 0.06, maxy + 0.06)
ax.set_aspect("equal", adjustable="box")
if not DEM_FILE.exists():
    raise FileNotFoundError(f"Terrain DEM not found: {DEM_FILE}")
print("Loading terrain...", flush=True)
with rasterio.open(DEM_FILE) as src:
    terrain_height = 1200
    terrain_width = max(1, round(src.width * terrain_height / src.height))
    terrain = src.read(
        1,
        out_shape=(terrain_height, terrain_width),
        masked=True,
        resampling=Resampling.bilinear,
    ).astype("float32")
    terrain_bounds = src.bounds
valid_mask = ~np.ma.getmaskarray(terrain)
values = terrain.compressed()
if values.size == 0:
    raise ValueError("Terrain DEM has no valid pixels.")
low, high = np.percentile(values, [2, 99.5])
terrain_display = np.ma.clip(terrain, low, high)
terrain_cmap = LinearSegmentedColormap.from_list(
    "nepal_dark",
    ["#101923", "#202C38", "#354451", "#53616B",
     "#7C858B", "#B1B5B6", "#D7D8D5"],
)
terrain_rgba = LightSource(azdeg=315, altdeg=38).shade(
    terrain_display.filled(low),
    cmap=terrain_cmap,
    vert_exag=3.0,
    dx=1,
    dy=1,
    blend_mode="soft",
)
terrain_rgba[..., 3] = valid_mask.astype(float)
ax.imshow(
    terrain_rgba,
    extent=(
        terrain_bounds.left, terrain_bounds.right,
        terrain_bounds.bottom, terrain_bounds.top,
    ),
    origin="upper",
    interpolation="bilinear",
    zorder=0,
)
for polygon in polygons:
    x, y = polygon.exterior.xy
    ax.plot(x, y, color=BORDER_COLOR, linewidth=1.15, alpha=0.95, zorder=3)
    for ring in polygon.interiors:
        ix, iy = ring.xy
        ax.plot(ix, iy, color=BORDER_COLOR, linewidth=0.55, alpha=0.6, zorder=3)
# ------------------------------------------------------------
# Airports
# ------------------------------------------------------------
AIRPORTS = {
    "Kathmandu": (85.3591, 27.6966),
    "Pokhara": (83.9821, 28.2000),
    "Biratnagar": (87.2636, 26.4815),
    "Jhapa": (88.0796, 26.5708),
    "Bhairahawa": (83.4163, 27.5057),
    "Nepalgunj": (81.6670, 28.1039),
    "Bharatpur": (84.4297, 27.6781),
    "Janakpur": (85.9224, 26.7088),
    "Dhangadhi": (80.5819, 28.7533),
    "Lukla": (86.7297, 27.6869),
    "Phaplu": (86.5840, 27.5170),
    "Ramechhap": (86.0614, 27.3939),
}
for name, (lon, lat) in AIRPORTS.items():
    kathmandu = name == "Kathmandu"
    # Subtle red halo, then a bright red core with a clean ivory rim.
    ax.scatter(
        [lon], [lat],
        s=115 if kathmandu else 72,
        color="#FF202D",
        alpha=0.16,
        linewidths=0,
        zorder=7,
    )
    ax.scatter(
        [lon], [lat],
        s=42 if kathmandu else 27,
        color="#FF202D",
        edgecolors="#F2E8D5",
        linewidths=1.0 if kathmandu else 0.7,
        zorder=8,
    )
    dx, dy = 0.07, 0.055
    if name in {"Janakpur", "Bhairahawa"}:
        dy = -0.11
    elif name == "Jhapa":
        dx = -0.38
    elif name == "Kathmandu":
        dx, dy = 0.09, 0.10
    ax.text(
        lon + dx, lat + dy, name.upper(),
        color="#FF6B73" if kathmandu else "#D7DDE2",
        fontsize=6.4 if name not in {"Kathmandu", "Pokhara"} else 7,
        fontweight="bold" if kathmandu else "normal",
        zorder=9,
    )
# ------------------------------------------------------------
# Draw recent position for each flight and its recent trail.
# Separate trajectory segments are kept disconnected.
# ------------------------------------------------------------
TRAIL_MINUTES = 10
MAX_TRAIL_GAP_SECONDS = 60

# Pre-sort trajectory segments once. The terrain, airports and typography
# remain static; only aircraft, trails, clock/count and radar marker update.
trajectory_segments = []
print("Preparing Nepal-clipped trajectory segments...", flush=True)
for (flight_id, segment_id), group in df.groupby(
    ["flight_id", "segment_id"], sort=False
):
    group = group.sort_values("unix_time")
    times = group["unix_time"].to_numpy(dtype=float)
    coords = group[["longitude", "latitude"]].to_numpy(dtype=float)
    if len(times) == 0:
        continue
    group_name = airline_group(group.iloc[0]["callsign"])
    point_inside = contains_xy(nepal_buffer, coords[:, 0], coords[:, 1])

    # Clip each short recorded edge to Nepal once, rather than recalculating it per frame.
    clipped_edges = []
    for j in range(len(coords) - 1):
        if times[j + 1] - times[j] > MAX_TRAIL_GAP_SECONDS:
            clipped_edges.append([])
            continue
        edge = LineString([coords[j], coords[j + 1]])
        clipped = edge.intersection(nepal_buffer)
        parts = []
        stack = [clipped]
        while stack:
            geom = stack.pop()
            if geom.is_empty:
                continue
            if geom.geom_type == "LineString":
                arr = np.asarray(geom.coords, dtype=float)
                if len(arr) >= 2:
                    parts.append(arr)
            elif hasattr(geom, "geoms"):
                stack.extend(list(geom.geoms))
        clipped_edges.append(parts)

    trajectory_segments.append(
        (str(flight_id), times, coords, point_inside, clipped_edges, group_name)
    )

active_flights = 0
aircraft_scatter = ax.scatter(
    [], [], s=24, edgecolors="#FFFFFF", linewidths=0.3, zorder=7
)
trail_collections = {}
for group_name, color in COLORS.items():
    collection = LineCollection(
        [], colors=color, linewidths=1.25, alpha=0.72, zorder=5
    )
    ax.add_collection(collection)
    trail_collections[group_name] = collection

# ------------------------------------------------------------
# Editorial typography
# ------------------------------------------------------------
fig.text(
    0.035, 0.965, "N E P A L",
    color="#F1F0EB",
    fontsize=29,
    fontfamily="DejaVu Serif",
    fontweight="bold",
    va="top",
)
fig.text(
    0.037, 0.925,
    "A I R C R A F T   I N   N E P A L"
    "   •   1 4 – 1 6   S E P T E M B E R   2 0 2 6",
    color=MUTED_COLOR,
    fontsize=7.5,
    fontfamily="DejaVu Sans",
    va="top",
)
date_text = fig.text(
    0.037, 0.885, local_time.strftime("%d %b %Y  •  %H:%M"),
    color="#F1F0EB",
    fontsize=21,
    fontfamily="DejaVu Sans",
    va="top",
)
count_text = fig.text(
    0.039, 0.835,
    f"{active_flights:03d}  AIRCRAFT WITH RECENT DATA\n"
    f"{df_nepal['flight_id'].nunique():,}  FLIGHTS RECORDED IN NEPAL",
    color=MUTED_COLOR,
    fontsize=9.5,
    fontfamily="DejaVu Sans",
    va="top",
    linespacing=1.65,
)
fig.text(
    0.035, 0.012,
    "HISTORICAL ADS-B DATA  •  AIRCRAFT FADE OUT 40 KM BEYOND NEPAL  •  NPT",
    color="#7F8A99",
    fontsize=7.5,
    va="bottom",
)
# ------------------------------------------------------------
# Halloween-inspired spider-web activity chart — upper right
# 24 spokes = hours of Nepal time; shape = September daily average
# ------------------------------------------------------------
radar_ax = fig.add_axes([0.79, 0.805, 0.16, 0.16], projection="polar")
radar_ax.set_facecolor("none")
radar_ax.set_theta_zero_location("N")
radar_ax.set_theta_direction(-1)
angles = np.arange(24) * (2 * np.pi / 24)
closed_angles = np.append(angles, angles[0])
closed_values = np.append(chart_values, chart_values[0])
max_value = max(float(chart_values.max()), 1.0)
radar_ax.set_ylim(0, max_value * 1.12)
# Spider-web spokes
radar_ax.set_xticks(angles)
radar_ax.set_xticklabels([""] * 24)
radar_ax.xaxis.grid(True, color="#64242D", linewidth=0.5, alpha=0.85)
# Concentric web rings
radar_ax.set_yticks([
    max_value * 0.25,
    max_value * 0.50,
    max_value * 0.75,
    max_value,
])
radar_ax.set_yticklabels([])
radar_ax.yaxis.grid(True, color="#64242D", linewidth=0.6, alpha=0.85)
radar_ax.spines["polar"].set_visible(False)
# Spider-Man-inspired activity shape: glowing signal red
radar_ax.fill(
    closed_angles, closed_values,
    color="#FF202D", alpha=0.22, zorder=2,
)
radar_ax.plot(
    closed_angles, closed_values,
    color="#FF303A", linewidth=1.35, alpha=1.0, zorder=3,
)
# Current preview hour marker
marker_angle = current_hour * (2 * np.pi / 24)
hour_index = int(local_time.hour)
marker_radius = chart_values[hour_index]
marker_radius_display = max(marker_radius, max_value * 0.06)
radar_marker_line, = radar_ax.plot(
    [marker_angle, marker_angle],
    [0, marker_radius_display],
    color="#F2E8D5", linewidth=1.1, alpha=1.0, zorder=4,
)
radar_marker_dot = radar_ax.scatter(
    [marker_angle], [marker_radius_display],
    s=19, color="#F2E8D5", edgecolors="#FF202D",
    linewidths=0.8, zorder=5,
)
# Sparse hour labels around the web
for hour in [0, 6, 12, 18]:
    radar_ax.text(
        angles[hour], max_value * 1.13, f"{hour:02d}",
        color="#FF6B73",
        fontsize=6.5,
        fontfamily="DejaVu Serif",
        fontweight="bold",
        ha="center",
        va="center",
        clip_on=False,
    )
radar_ax.set_title(
    "FLIGHT ACTIVITY",
    color="#F2E8D5",
    fontsize=7,
    fontfamily="DejaVu Serif",
    fontweight="bold",
    pad=9,
)
radar_ax.text(
    0.5, -0.19, "NEPAL-ONLY AVERAGE • NPT",
    transform=radar_ax.transAxes,
    color="#A5AAB5",
    fontsize=5.5,
    fontfamily="DejaVu Sans",
    ha="center",
    va="top",
)
# ------------------------------------------------------------
# Finish and save preview
# ------------------------------------------------------------
ax.set_xticks([])
ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_visible(False)
# Layout is explicitly positioned above to reserve a clean header.
def update_frame(frame_epoch):
    frame_epoch = float(frame_epoch)
    frame_local_time = datetime.fromtimestamp(
        frame_epoch, timezone.utc
    ).astimezone(NEPAL_TZ)

    positions = []
    position_colors = []
    active_ids = set()
    trails_by_group = {name: [] for name in COLORS}
    trail_colors_by_group = {name: [] for name in COLORS}
    trail_start = frame_epoch - TRAIL_MINUTES * 60

    for flight_id, times, coords, point_inside, clipped_edges, group_name in trajectory_segments:
        idx = np.searchsorted(times, frame_epoch, side="right") - 1
        if idx < 0 or times[idx] < frame_epoch - 5 * 60:
            continue

        # Show aircraft inside Nepal and up to 40 km beyond it; fade by distance.
        if point_inside[idx]:
            positions.append(coords[idx])
            position_colors.append(COLORS[group_name])
            active_ids.add(flight_id)

        start_idx = max(
            0, np.searchsorted(times, trail_start, side="left") - 1
        )
        for j in range(start_idx, idx):
            if times[j + 1] - times[j] <= MAX_TRAIL_GAP_SECONDS:
                # Clip trails to the 40 km buffer and fade portions outside Nepal.
                for part in clipped_edges[j]:
                    if len(part) < 2:
                        continue
                    for k in range(len(part) - 1):
                        edge_part = np.asarray([part[k], part[k + 1]], dtype=float)
                        midpoint = Point(float(edge_part[:, 0].mean()), float(edge_part[:, 1].mean()))
                        if nepal.covers(midpoint):
                            alpha = 0.72
                        else:
                            mx, my = to_local(midpoint.x, midpoint.y)
                            distance_km = nepal_metric.distance(Point(mx, my)) / 1000.0
                            alpha = 0.72 * max(0.0, min(1.0, 1.0 - distance_km / 40.0))
                        trails_by_group[group_name].append(edge_part)
                        base_rgb = plt.matplotlib.colors.to_rgb(COLORS[group_name])
                        trail_colors_by_group[group_name].append((*base_rgb, alpha))

    if positions:
        aircraft_scatter.set_offsets(np.asarray(positions, dtype=float))
        rgba_positions = []
        for (lon, lat), color in zip(positions, position_colors):
            if nepal.covers(Point(float(lon), float(lat))):
                alpha = 1.0
            else:
                mx, my = to_local(float(lon), float(lat))
                distance_km = nepal_metric.distance(Point(mx, my)) / 1000.0
                alpha = max(0.0, min(1.0, 1.0 - distance_km / 40.0))
            rgba_positions.append((*plt.matplotlib.colors.to_rgb(color), alpha))
        aircraft_scatter.set_facecolors(rgba_positions)
    else:
        aircraft_scatter.set_offsets(np.empty((0, 2)))
        aircraft_scatter.set_facecolors([])

    for group_name, collection in trail_collections.items():
        collection.set_segments(trails_by_group[group_name])
        collection.set_colors(trail_colors_by_group[group_name])

    date_text.set_text(frame_local_time.strftime("%d %b %Y  •  %H:%M"))
    count_text.set_text(
        f"{len(active_ids):03d}  AIRCRAFT WITH RECENT DATA\n"
        f"{df_nepal['flight_id'].nunique():,}  FLIGHTS RECORDED IN NEPAL"
    )

    current_hour = frame_local_time.hour + frame_local_time.minute / 60
    marker_angle = current_hour * (2 * np.pi / 24)
    marker_radius = chart_values[frame_local_time.hour]
    marker_radius_display = max(marker_radius, max_value * 0.06)
    radar_marker_line.set_data(
        [marker_angle, marker_angle], [0, marker_radius_display]
    )
    radar_marker_dot.set_offsets([[marker_angle, marker_radius_display]])

    if int(frame_epoch - START.timestamp()) % 3600 < frame_step_seconds:
        print(
            f"Rendering: {frame_local_time:%Y-%m-%d %H:%M} NPT "
            f"({len(active_ids)} active aircraft)",
            flush=True,
        )
    return [aircraft_scatter, date_text, count_text, radar_marker_line, radar_marker_dot,
            *trail_collections.values()]

print(f"Animation frames: {len(frame_epochs):,}", flush=True)
print(f"Sampling interval: every {FRAME_STEP_MINUTES} minutes", flush=True)
print(f"Playback: {FPS} FPS", flush=True)

if shutil.which("ffmpeg") is None:
    raise RuntimeError("FFmpeg was not found on PATH. Install FFmpeg or add it to PATH.")

animation = FuncAnimation(
    fig, update_frame, frames=frame_epochs, interval=1000 / FPS,
    blit=False, repeat=False, cache_frame_data=False
)
print(f"Rendering temporary video: {TEMP_VIDEO}", flush=True)
writer = FFMpegWriter(
    fps=FPS, codec="libx264", bitrate=3500,
    extra_args=["-pix_fmt", "yuv420p", "-movflags", "+faststart"]
)
animation.save(TEMP_VIDEO, writer=writer, dpi=100)

plt.close(fig)

print("Encoding optimized GIF with FFmpeg...", flush=True)
subprocess.run([
    "ffmpeg", "-y", "-i", str(TEMP_VIDEO),
    "-vf", "fps=15,scale=1280:-1:flags=lanczos,palettegen=stats_mode=diff",
    str(PALETTE_FILE)
], check=True)
subprocess.run([
    "ffmpeg", "-y", "-i", str(TEMP_VIDEO), "-i", str(PALETTE_FILE),
    "-lavfi",
    "fps=15,scale=1280:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=3",
    "-loop", "0", str(OUTPUT_FILE)
], check=True)

# Remove intermediates only after GIF encoding succeeds.
TEMP_VIDEO.unlink(missing_ok=True)
PALETTE_FILE.unlink(missing_ok=True)

print(f"GIF saved: {OUTPUT_FILE}")
print(f"Frame count: {len(frame_epochs):,}")
print(f"Duration: {len(frame_epochs) / FPS:.1f} seconds")
print(f"Dates: {START} to {END} (END exclusive)")
print("Radar chart: average recorded activity inside Nepal for the selected three Nepal-time days")
