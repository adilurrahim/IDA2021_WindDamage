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

**Expected runtime:** ~1-2 hours first run

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

**Expected runtime:** ~15-30 minutes (skips 30-60 min building characterization)

## Check Results

Final results are in:
```
output/results/TotalLoss.csv
```

View with:
```bash
# On Linux/Mac
cat output/results/TotalLoss.csv

# On Windows
type output\results\TotalLoss.csv

# Or open in Excel/spreadsheet application
```

## Pipeline Steps

The pipeline runs 3 main steps automatically:

1. **NetCDF Processing** (~2-5 min)
   - Converts NCAR NetCDF → CSV wind data

2. **Spatial Join** (~10-20 min)
   - Assigns wind speeds to buildings

3. **Loss Calculation** (~30-60 min first run, ~5-10 min with checkpoint)
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
│   └── nsi_wbId_sr.csv       # Checkpoint (SAVE THIS!)
├── joined_data/
│   ├── ida_1971/ida_1971.csv # Buildings + 1971 wind
│   ├── ida_2021/ida_2021.csv # Buildings + 2021 wind
│   └── ida_2071/ida_2071.csv # Buildings + 2071 wind
└── results/
    ├── ida_1971/Losses.csv   # Individual losses (1971)
    ├── ida_2021/Losses.csv   # Individual losses (2021)
    ├── ida_2071/Losses.csv   # Individual losses (2071)
    └── TotalLoss.csv         # ⭐ FINAL SUMMARY
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

### Out of memory
**Solution:**
- Close other applications
- Need 16GB+ RAM for large datasets
- Or process smaller geographic subset

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

## Data Sources

You need to obtain:

1. **NCAR NetCDF files**: Contact [NCAR data provider]
2. **NSI building data**: https://www.hec.usace.army.mil/confluence/nsi
3. **Hazus files**: https://www.fema.gov/flood-maps/products-tools/hazus

See [README.md](README.md) for detailed data requirements.

## Next Steps

1. ✅ Run pipeline on your data
2. ✅ Review `TotalLoss.csv` results
3. ✅ Check logs for any warnings
4. ✅ Save checkpoint file for future runs
5. 📖 Read [README.md](README.md) for detailed documentation
6. 🏗️ See [STRUCTURE.md](STRUCTURE.md) for architecture details

## Support

For questions:
1. Check [README.md](README.md) - comprehensive documentation
2. Review log file in `logs/` directory
3. See [STRUCTURE.md](STRUCTURE.md) for code architecture
4. Open GitHub issue with error details

## Example Results

Example `TotalLoss.csv`:

```csv
Year,Building,Contents,Total
ida_1971,1500000000,750000000,2250000000
ida_2021,2000000000,1000000000,3000000000
ida_2071,2500000000,1250000000,3750000000
```

This shows increasing losses from 1971 → 2021 → 2071 climate scenarios.

## Tips

💡 **Save the checkpoint!** The `nsi_wbId_sr.csv` file saves 30-60 minutes on future runs

💡 **Check logs** for detailed statistics and progress updates

💡 **Start small** if testing - use subset of data first

💡 **Monitor resources** - pipeline needs ~16GB RAM for large datasets

💡 **Be patient** - First run takes time, but subsequent runs are much faster

---

**Happy analyzing! 🌪️📊**

For detailed documentation, see [README.md](README.md)
