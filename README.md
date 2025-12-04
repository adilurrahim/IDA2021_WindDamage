# Hurricane Ida Wind Loss Analysis Pipeline

This repository contains the analysis pipeline for assessing building wind damage losses from Hurricane Ida across different climate scenarios using NCAR climate model data and the Hazus wind damage methodology.

## Overview

This pipeline processes NCAR climate model simulations of Hurricane Ida under three climate scenarios (1971, 2021, 2071) and calculates building-level and county-level wind damage losses. The analysis combines:

- **NCAR climate model data**: NetCDF files containing wind swath data for Hurricane Ida
- **National Structure Inventory (NSI)**: Geospatial building inventory
- **Hazus methodology**: FEMA's standardized wind damage functions

The pipeline enables comparison of hurricane impacts across past, present, and future climate conditions.

## Citation

If you use this code, please cite:

```

```

## Installation

### Prerequisites

- Python 3.10 or higher
- pip package manager

### Setup

1. Clone or download this repository
2. Install required dependencies:

```bash
pip install -r requirements.txt
```

Alternatively, create a conda environment:

```bash
conda create -n ida_analysis python=3.10
conda activate ida_analysis
pip install -r requirements.txt
```

## Data Requirements

The pipeline requires the following input data:

### 1. NCAR NetCDF Files (3 files)

- `ida_1971.nc` - Hurricane Ida simulation with 1971 climate conditions
- `ida_2021.nc` - Hurricane Ida simulation with 2021 climate conditions (actual event)
- `ida_2071.nc` - Hurricane Ida simulation with 2071 projected climate conditions

**Required variables in each NetCDF file:**
- `swath_wind` - Maximum wind speed swath (m/s)
- `lon_2d` - 2D longitude array
- `lat_2d` - 2D latitude array

### 2. NSI Building Inventory

- `nsi_2022_22.gpkg` - National Structure Inventory GeoPackage for the study region

### 3. Hazus Mapping Files

- `Mapping.xlsx` - Hazus building type mappings (Excel workbook with multiple sheets)
- `huDamLossFunc.csv` - Hazus wind damage functions

**Required sheets in Mapping.xlsx:**
- `huMappingSchemesByCountyFips` - County-level mapping schemes
- `huGbsOccMapping` - Occupancy type mappings
- `huBldgMapping` - Building characteristic mappings
- `huListofBldgChar` - Building characteristic definitions
- `huListOfWindBldgTypes` - Wind building type definitions
- `huTerrain` - Terrain classification definitions

### Data Organization

Organize your data as follows:

```
data/
├── ncar_netcdf/
│   ├── ida_1971.nc
│   ├── ida_2021.nc
│   └── ida_2071.nc
├── nsi/
│   └── nsi_2022_22.gpkg
└── hazus/
    ├── Mapping.xlsx
    └── huDamLossFunc.csv
```

## Usage

### Basic Pipeline Run

Run the complete pipeline with all three steps:

```bash
python main_pipeline.py \
  --ncar-dir ./data/ncar_netcdf \
  --nsi-path ./data/nsi/nsi_2022_22.gpkg \
  --hazus-dir ./data/hazus \
  --output-dir ./output
```

### Using Existing Building Characterization

The building characterization step (Step 3A) is computationally expensive. Once computed, the results are automatically checkpointed. To explicitly use an existing checkpoint:

```bash
python main_pipeline.py \
  --ncar-dir ./data/ncar_netcdf \
  --nsi-path ./data/nsi/nsi_2022_22.gpkg \
  --hazus-dir ./data/hazus \
  --output-dir ./output \
  --building-inventory ./output/building_inventory/nsi_wbId_sr.csv
```

### Running Specific Steps

To run only certain pipeline steps (1=NetCDF processing, 2=Spatial join, 3=Loss calculation):

```bash
# Run only steps 1 and 2
python main_pipeline.py \
  --ncar-dir ./data/ncar_netcdf \
  --nsi-path ./data/nsi/nsi_2022_22.gpkg \
  --hazus-dir ./data/hazus \
  --output-dir ./output \
  --steps 1,2

# Run only step 3 (requires steps 1-2 completed)
python main_pipeline.py \
  --ncar-dir ./data/ncar_netcdf \
  --nsi-path ./data/nsi/nsi_2022_22.gpkg \
  --hazus-dir ./data/hazus \
  --output-dir ./output \
  --steps 3
```

### Force Reprocessing

By default, the pipeline skips steps if output files already exist. To force reprocessing:

```bash
python main_pipeline.py \
  --ncar-dir ./data/ncar_netcdf \
  --nsi-path ./data/nsi/nsi_2022_22.gpkg \
  --hazus-dir ./data/hazus \
  --output-dir ./output \
  --force-rerun
```

### Help

For complete usage information:

```bash
python main_pipeline.py --help
```

## Pipeline Steps

The analysis proceeds through three main steps:

### Step 1: NCAR NetCDF Processing

**Module:** `modules/netcdf_processor.py`

Processes NCAR climate model NetCDF files to CSV format:

1. Extracts wind swath data from NetCDF files
2. Converts to gust wind speeds (sustained wind × 1.28 per ASCE 7-16)
3. Converts units from m/s to mph (× 2.23694)
4. Adjusts longitude coordinates from [0°, 360°] to [-180°, 180°]

**Outputs:** `output/processed_wind/ida_YYYY.csv` for each scenario


### Step 2: Spatial Join

**Module:** `modules/spatial_join.py`

Spatially joins NSI building locations with NCAR wind grid points:

1. Loads NSI building inventory from GeoPackage
2. Creates point geometries from wind CSV files
3. Projects both datasets to NAD83 / UTM zone 15N (EPSG:26915)
4. Performs nearest neighbor spatial join
5. Assigns wind speeds to each building

**Outputs:** `output/joined_data/ida_YYYY/ida_YYYY.csv` for each scenario


### Step 3: Loss Calculation

**Module:** `modules/building_losses.py`

Calculates building wind damage losses using Hazus methodology:

#### Step 3A: Building Characterization (with checkpointing)

Maps NSI buildings to Hazus building types and damage functions:

1. Assigns Hazus building scheme by county FIPS
2. Probabilistically assigns building subtypes
3. Assigns building characteristics (construction type, shutters, etc.)
4. Matches to Hazus wind building type (wbID)
5. Calculates terrain ID from surface roughness

**Checkpoint:** `output/building_inventory/nsi_wbId_sr.csv`


#### Step 3B: Individual Building Losses

Calculates losses for each building:

1. Looks up Hazus damage functions by building type and terrain
2. Interpolates loss ratios from wind speed
3. Calculates dollar losses: loss_ratio × replacement_value

**Outputs:** `output/results/ida_YYYY/Losses.csv` for each scenario

#### Step 3C: County-Level Aggregation

Aggregates building losses to county level and creates summary:

**Output:** `output/results/TotalLoss.csv`


## Output Directory Structure

```
output/
├── processed_wind/           # Step 1 outputs
│   ├── ida_1971.csv
│   ├── ida_2021.csv
│   └── ida_2071.csv
├── building_inventory/       # Step 3A checkpoint
│   └── nsi_wbId_sr.csv
├── joined_data/              # Step 2 outputs
│   ├── ida_1971/
│   │   └── ida_1971.csv
│   ├── ida_2021/
│   │   └── ida_2021.csv
│   └── ida_2071/
│       └── ida_2071.csv
├── results/                  # Step 3B-3C outputs
│   ├── ida_1971/
│   │   └── Losses.csv
│   ├── ida_2021/
│   │   └── Losses.csv
│   ├── ida_2071/
│   │   └── Losses.csv
│   └── TotalLoss.csv        # Final summary
└── logs/                     # Execution logs
    └── pipeline_YYYYMMDD_HHMMSS.log
```

## Output File Formats

### Processed Wind Data (`processed_wind/ida_YYYY.csv`)

| Column | Type | Description |
|--------|------|-------------|
| Longitude | float | Longitude in degrees [-180, 180] |
| Latitude | float | Latitude in degrees [-90, 90] |
| Wind_Speed | float | Sustained wind speed (mph) |
| Gust_Wind_Speed | float | 3-second gust wind speed (mph) |

### Individual Building Losses (`results/ida_YYYY/Losses.csv`)

| Column | Type | Description |
|--------|------|-------------|
| fd_id | string | Foundation ID (building identifier) |
| countyFIPS | string | County FIPS code |
| wbID | int | Hazus wind building type ID |
| terrainID | int | Terrain classification (1-5) |
| Wind_Speed | float | Gust wind speed assigned to building (mph) |
| Building_Loss | float | Structural damage loss ($) |
| Contents_Loss | float | Contents damage loss ($) |

### Total Losses Summary (`results/TotalLoss.csv`)

| Column | Type | Description |
|--------|------|-------------|
| Year | string | Scenario name (ida_1971, ida_2021, ida_2071) |
| Building | float | Total building structural loss ($) |
| Contents | float | Total contents loss ($) |
| Total | float | Combined building + contents loss ($) |



## Logging

All pipeline execution is logged to both console and file:

- **Log location:** `output/../logs/pipeline_YYYYMMDD_HHMMSS.log`
- **Log format:** Timestamped entries with module and severity level
- **Log contents:**
  - Input validation results
  - Processing progress for each step
  - Statistics (building counts, loss totals, etc.)
  - Warnings and errors
  - Execution time

Check the log file for detailed execution information and troubleshooting.

## Methodology

### Wind Speed Conversion

NCAR NetCDF files contain sustained wind speeds in m/s. The pipeline converts to 3-second gust wind speeds in mph:

```
Gust Wind Speed (mph) = Wind Speed (m/s) × 1.28 × 2.23694
```

Where:
- **1.28** = Gust factor (ASCE 7-16 Section 26.5)
- **2.23694** = m/s to mph conversion factor

### Spatial Join Methodology

Buildings are assigned wind speeds from the nearest NCAR grid point using:

1. Project both datasets to NAD83 / UTM zone 15N for accurate distances
2. Nearest neighbor join with distance calculation
3. Distances logged for quality assessment

### Loss Calculation Methodology

Building losses use FEMA Hazus wind damage functions:

1. **Building characterization:** Probabilistic assignment of Hazus building types
2. **Damage curve lookup:** Retrieve damage functions by building type and terrain
3. **Loss interpolation:** Linear interpolation of loss ratio from wind speed
4. **Dollar loss:** Loss ratio × replacement value

### Reproducibility

All probabilistic assignments use a fixed random seed (121) to ensure reproducible results across runs.

