# Quick Start Guide

Get started with the Hurricane Ida Wind Loss Analysis Pipeline in 5 minutes.

## Prerequisites

- Python 3.10+
- pip package manager

## Installation

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Organize your data
mkdir -p data/ncar_netcdf data/nsi data/hazus
# Copy your NetCDF files, NSI GeoPackage, and Hazus files to respective folders
```

## Basic Usage

### Run Complete Pipeline

```bash
python main_pipeline.py \
  --ncar-dir ./data/ncar_netcdf \
  --nsi-path ./data/nsi/nsi_2022_22.gpkg \
  --hazus-dir ./data/hazus \
  --output-dir ./output
```

### Use Existing Checkpoint (Fast!)

After first run, reuse the building characterization checkpoint:

```bash
python main_pipeline.py \
  --ncar-dir ./data/ncar_netcdf \
  --nsi-path ./data/nsi/nsi_2022_22.gpkg \
  --hazus-dir ./data/hazus \
  --output-dir ./output \
  --building-inventory ./output/building_inventory/nsi_wbId_sr.csv
```

## Check Results

Final results are in:
```
output/results/TotalLoss.csv
```


## Pipeline Steps

The pipeline runs 3 main steps automatically:

1. **NetCDF Processing** 
   - Converts NCAR NetCDF → CSV wind data

2. **Spatial Join** 
   - Assigns wind speeds to buildings

3. **Loss Calculation** 
   - Calculates building-level losses
   - Aggregates to county level

## Output Files

After successful run, check:

```
output/
├── processed_wind/
│   ├── ida_1971.csv          # 1971 climate wind data
│   ├── ida_2021.csv          # 2021 climate wind data
│   └── ida_2071.csv          # 2071 climate wind data
├── building_inventory/
│   └── nsi_wbId_sr.csv       # Checkpoint
├── joined_data/
│   ├── ida_1971/ida_1971.csv # Buildings + 1971 wind
│   ├── ida_2021/ida_2021.csv # Buildings + 2021 wind
│   └── ida_2071/ida_2071.csv # Buildings + 2071 wind
└── results/
    ├── ida_1971/Losses.csv   # Individual losses (1971)
    ├── ida_2021/Losses.csv   # Individual losses (2021)
    ├── ida_2071/Losses.csv   # Individual losses (2071)
    └── TotalLoss.csv         # FINAL SUMMARY
```

## Logs

Check execution log for details:
```
logs/pipeline_YYYYMMDD_HHMMSS.log
```

## Troubleshooting

### "NetCDF file not found"
**Solution:** Verify you have all 3 files in `--ncar-dir`:
- ida_1971.nc
- ida_2021.nc
- ida_2071.nc

### "NSI file not found"
**Solution:** Check path to NSI GeoPackage (.gpkg file) in `--nsi-path`

### "Hazus files not found"
**Solution:** Verify both files exist in `--hazus-dir`:
- Mapping.xlsx
- huDamLossFunc.csv

### Pipeline taking too long
**Normal:** First run takes 1-2 hours (building characterization is slow)
**Solution:** After first run, use `--building-inventory` flag to reuse checkpoint

## Advanced Usage

### Run Specific Steps Only

```bash
# Run only Steps 1 and 2
python main_pipeline.py \
  --ncar-dir ./data/ncar_netcdf \
  --nsi-path ./data/nsi/nsi_2022_22.gpkg \
  --hazus-dir ./data/hazus \
  --output-dir ./output \
  --steps 1,2

# Run only Step 3 (requires 1-2 completed)
python main_pipeline.py \
  --ncar-dir ./data/ncar_netcdf \
  --nsi-path ./data/nsi/nsi_2022_22.gpkg \
  --hazus-dir ./data/hazus \
  --output-dir ./output \
  --steps 3
```

### Force Reprocessing

Ignore existing outputs and reprocess everything:

```bash
python main_pipeline.py \
  --ncar-dir ./data/ncar_netcdf \
  --nsi-path ./data/nsi/nsi_2022_22.gpkg \
  --hazus-dir ./data/hazus \
  --output-dir ./output \
  --force-rerun
```

### Get Help

```bash
python main_pipeline.py --help
```

## Example Results

Example `TotalLoss.csv`:

```csv
Year,Building,Contents,Total
ida_1971,1500000000,750000000,2250000000
ida_2021,2000000000,1000000000,3000000000
ida_2071,2500000000,1250000000,3750000000
```

This shows increasing losses from 1971 → 2021 → 2071 climate scenarios.
