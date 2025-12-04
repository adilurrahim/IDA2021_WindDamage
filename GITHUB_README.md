# 🌪️ Hurricane Ida Wind Loss Analysis Pipeline

**Publication-ready code for Nature Climate Change**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

This repository contains the complete analysis pipeline for assessing building wind damage losses from Hurricane Ida across different climate scenarios using NCAR climate model data and the FEMA Hazus wind damage methodology.

---

## 📋 Quick Navigation

| Document | Description |
|----------|-------------|
| **[QUICK_START.md](QUICK_START.md)** | Get started in 5 minutes |
| **[README.md](README.md)** | Complete documentation (data, usage, methodology) |
| **[STRUCTURE.md](STRUCTURE.md)** | Code architecture and developer guide |

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run pipeline
python main_pipeline.py \
  --ncar-dir ./data/ncar_netcdf \
  --nsi-path ./data/nsi/nsi_2022_22.gpkg \
  --hazus-dir ./data/hazus \
  --output-dir ./output
```

**First run:** ~1-2 hours | **Subsequent runs:** ~15-30 minutes (with checkpoint)

📖 See [QUICK_START.md](QUICK_START.md) for detailed instructions

---

## 📁 Repository Structure

```
github_publication/
├── 📄 main_pipeline.py       # Main orchestrator (run this!)
├── ⚙️  config.py              # Configuration constants
├── 📦 requirements.txt        # Python dependencies
├── 📚 README.md               # Complete documentation
├── 🚀 QUICK_START.md          # 5-minute quick start
├── 🏗️  STRUCTURE.md           # Code architecture
├── 🔒 .gitignore              # Git ignore rules
└── 📂 modules/                # Processing modules
    ├── __init__.py
    ├── netcdf_processor.py   # Step 1: NetCDF → CSV
    ├── spatial_join.py       # Step 2: Join buildings + wind
    └── building_losses.py    # Step 3: Calculate losses
```

---

## 🔬 What This Pipeline Does

### Input Data
- 🌍 **NCAR NetCDF files**: Hurricane Ida wind swaths (3 climate scenarios: 1971, 2021, 2071)
- 🏘️ **NSI building inventory**: Geospatial building database
- 📊 **Hazus files**: FEMA wind damage functions

### Processing Steps
1. **NetCDF Processing** - Convert climate model data to CSV format
2. **Spatial Join** - Assign wind speeds to each building
3. **Loss Calculation** - Calculate building-level wind damage losses

### Output
- 📈 County-level loss aggregations
- 💰 Building-level loss details
- 📊 Summary comparison across climate scenarios

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| ⚡ **Checkpointing** | Expensive operations cached (~30-60 min saved) |
| 🔍 **Error Handling** | Clear messages when data missing |
| 📝 **Logging** | Console + file logging with timestamps |
| 🎯 **Reproducible** | Fixed random seed (121) for consistency |
| 🏗️ **Modular** | Clean separation of concerns |
| 📖 **Documented** | Comprehensive docstrings and guides |

---

## 📊 Example Results

After running the pipeline, you'll get `TotalLoss.csv`:

| Year | Building Loss | Contents Loss | Total Loss |
|------|--------------|---------------|------------|
| ida_1971 | $1.5B | $750M | $2.25B |
| ida_2021 | $2.0B | $1.0B | $3.0B |
| ida_2071 | $2.5B | $1.25B | $3.75B |

This demonstrates increasing hurricane damage losses across climate scenarios.

---

## 🛠️ Installation

### Requirements
- Python 3.10+
- pip package manager
- ~16GB RAM (for large datasets)
- ~10GB disk space (for outputs)

### Install Dependencies

```bash
pip install -r requirements.txt
```

**Installs:**
- numpy, pandas, scipy (numerical computing)
- geopandas, shapely (geospatial analysis)
- netCDF4 (climate data)
- openpyxl (Excel support)

---

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| **[README.md](README.md)** | Complete documentation including:<br>• Data requirements and sources<br>• Detailed usage examples<br>• Pipeline methodology<br>• Output formats<br>• Troubleshooting guide |
| **[QUICK_START.md](QUICK_START.md)** | Fast-track guide:<br>• Installation<br>• Basic usage<br>• Example commands<br>• Common issues |
| **[STRUCTURE.md](STRUCTURE.md)** | Developer documentation:<br>• Code architecture<br>• Module descriptions<br>• Data flow diagrams<br>• Extension guide |

---

## 💡 Usage Examples

### Basic Run
```bash
python main_pipeline.py \
  --ncar-dir ./data/ncar_netcdf \
  --nsi-path ./data/nsi/nsi_2022_22.gpkg \
  --hazus-dir ./data/hazus \
  --output-dir ./output
```

### Use Existing Checkpoint (Fast!)
```bash
python main_pipeline.py \
  --ncar-dir ./data/ncar_netcdf \
  --nsi-path ./data/nsi/nsi_2022_22.gpkg \
  --hazus-dir ./data/hazus \
  --output-dir ./output \
  --building-inventory ./output/building_inventory/nsi_wbId_sr.csv
```

### Run Specific Steps
```bash
# Only process NetCDF files
python main_pipeline.py --steps 1 [other args...]

# Only calculate losses (requires steps 1-2 done)
python main_pipeline.py --steps 3 [other args...]
```

### Get Help
```bash
python main_pipeline.py --help
```

---

## 📥 Data Sources

| Data | Source |
|------|--------|
| **NCAR NetCDF files** | [Add NCAR data repository URL] |
| **NSI building inventory** | https://www.hec.usace.army.mil/confluence/nsi |
| **Hazus damage functions** | https://www.fema.gov/flood-maps/products-tools/hazus |

See [README.md](README.md) for detailed data requirements.

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "NetCDF file not found" | Verify 3 NetCDF files in `--ncar-dir` |
| "NSI file not found" | Check `--nsi-path` points to .gpkg file |
| "Hazus files not found" | Ensure Mapping.xlsx and huDamLossFunc.csv in `--hazus-dir` |
| Pipeline too slow | Normal first run (~1-2 hrs). Use `--building-inventory` flag on subsequent runs |
| Out of memory | Need 16GB+ RAM or reduce dataset size |

See [README.md](README.md) Troubleshooting section for more details.

---

## 📜 Citation

If you use this code, please cite:

```bibtex
@article{ida_windloss_2024,
  title={Attribution Impacts of Climate Change on Hurricane Ida Wind Losses},
  author={[Authors]},
  journal={Nature Climate Change},
  year={2024},
  note={Code available at: [GitHub URL]}
}
```

---

## 📧 Contact

For questions about this code or the associated research:

- **[Author Name]** - [email@example.com]
- **[Institution]**

For data questions:
- NCAR data: [Contact/URL]
- NSI data: https://www.hec.usace.army.mil/confluence/nsi
- Hazus: https://www.fema.gov/flood-maps/products-tools/hazus

---

## 🙏 Acknowledgments

This research was supported by [Funding source].

- NCAR climate model simulations provided by [Institution/Project]
- Building inventory data from FEMA's National Structure Inventory
- Wind damage methodology based on FEMA's Hazus model

---

## 📄 License

[Add appropriate license - MIT, GPL, etc.]

---

## 🎯 Publication Status

This code accompanies the manuscript:

> **"Attribution Impacts of Climate Change on Hurricane Ida Wind Losses"**
>
> Submitted to: *Nature Climate Change*
>
> Status: [Under Review / Accepted / Published]

---

## 🔗 Quick Links

- 📖 [Complete Documentation](README.md)
- 🚀 [Quick Start Guide](QUICK_START.md)
- 🏗️ [Code Architecture](STRUCTURE.md)
- 🐛 [Issue Tracker](https://github.com/[your-repo]/issues)
- 💬 [Discussions](https://github.com/[your-repo]/discussions)

---

**Ready to analyze hurricane wind losses? Start with [QUICK_START.md](QUICK_START.md)! 🌪️📊**
