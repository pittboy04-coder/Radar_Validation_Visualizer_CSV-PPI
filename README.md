# Radar Validation Visualizer (CSV-to-PPI)

Standalone radar data viewer that loads CSV files (Furuno captures or simulator exports) and displays them on a PPI radar display with a side-by-side geographic scene view.

## Supported Formats

- **Furuno capture CSV**: `Status,Scale,Range,Gain,Angle,EchoValues` (integers 0-252, angle ticks 8192=360°)
- **Simulator export CSV**: `timestamp,unused,range_m,gain_code,angle_ticks,bin_0,...` (floats 0.0-1.0)

Format is auto-detected from the header.

## Usage

```bash
pip install -r requirements.txt
python main.py
```

Click **LOAD FILE** to select a CSV file, or **LOAD FOLDER** to select a folder of CSVs. The viewer displays the data on both a PPI radar display and a geographic scene view side-by-side.

## Controls

- **Mouse wheel**: Zoom in/out (change range scale)
- **ESC**: Exit
- Window is resizable

## Features

- **Auto-detect CSV formats**: Automatically recognizes both Furuno capture format (integer echoes 0-252) and simulator export format (float echoes 0.0-1.0) from header inspection
- **Cross-platform export directory**: Defaults file dialog to `~/maritime_radar_sim` on Linux or OneDrive Desktop on Windows for easy access to saved data
- **Flexible file loading**: Supports loading a single CSV file or an entire folder of CSVs, with file dialog defaulting to the export directory
- **Side-by-side display**: PPI radar display and geographic scene view render simultaneously for validation
