"""
Configuration file for Hurricane Ida Wind Loss Analysis Pipeline

This module contains all configuration constants, physical parameters,
and file specifications used throughout the analysis pipeline.
"""

# ==============================================================================
# PHYSICAL CONSTANTS
# ==============================================================================

# Gust factor based on ASCE 7-16 standard
# Converts sustained wind speed to gust wind speed (~1.3x sustained)
GUST_FACTOR_NCAR = 1.28

# Unit conversion: meters per second to miles per hour
# 1 m/s = 2.23694 mph
MS_TO_MPH = 2.23694

# Longitude coordinate adjustment
# NCAR data uses 0-360° longitude, need to convert to -180-180°
LONGITUDE_ADJUSTMENT = -360

# ==============================================================================
# HAZUS DAMAGE FUNCTION IDS
# ==============================================================================

# Damage function descriptor IDs from Hazus
BUILDING_DAMAGE_ID = 5  # Building structural damage
CONTENTS_DAMAGE_ID = 6  # Contents damage

# ==============================================================================
# REPRODUCIBILITY
# ==============================================================================

# Random seed for probabilistic building characteristic assignment
# Ensures reproducible results across runs
RANDOM_SEED = 121

# ==============================================================================
# CLIMATE SCENARIOS
# ==============================================================================

# Three climate scenarios for Hurricane Ida simulation
SCENARIOS = ['ida_1971', 'ida_2021', 'ida_2071']

# Expected NetCDF filenames
NETCDF_FILES = ['ida_1971.nc', 'ida_2021.nc', 'ida_2071.nc']

# ==============================================================================
# COORDINATE REFERENCE SYSTEMS
# ==============================================================================

# Input CRS for geographic coordinates (latitude/longitude)
INPUT_CRS = "EPSG:4326"  # WGS 84

# Projected CRS for accurate distance calculations
# NAD83 / UTM zone 15N - appropriate for Louisiana/Gulf Coast region
PROJECTED_CRS = "EPSG:26915"

# ==============================================================================
# TERRAIN CLASSIFICATION
# ==============================================================================

# Terrain roughness thresholds for wind exposure classification
# Based on surface roughness values to determine terrain ID
TERRAIN_THRESHOLDS = {
    1: (0.0, 0.03),         # Open terrain (water, flat open land)
    2: (0.03, 0.15),        # Light suburban
    3: (0.15, 0.35),        # Suburban
    4: (0.35, 0.7),         # Light urban
    5: (0.7, float('inf'))  # Urban
}

# ==============================================================================
# HAZUS DATA FILES
# ==============================================================================

# Required Hazus files for building damage analysis
HAZUS_FILES = {
    'mapping': 'Mapping.xlsx',              # Building type mappings
    'damage_functions': 'huDamLossFunc.csv' # Wind damage functions
}

# Sheet names in the Hazus Mapping.xlsx workbook
HAZUS_SHEETS = {
    'county_mapping': 'huMappingSchemesByCountyFips',  # County-level mapping schemes
    'occ_mapping': 'huGbsOccMapping',                  # Occupancy type mappings
    'bldg_mapping': 'huBldgMapping',                   # Building characteristic mappings
    'bldg_char': 'huListofBldgChar',                   # Building characteristic list
    'wind_types': 'huListOfWindBldgTypes',             # Wind building types
    'terrain': 'huTerrain'                             # Terrain definitions
}

# ==============================================================================
# BUILDING TYPE CODES
# ==============================================================================

# Hazus building type codes
BUILDING_TYPES = {
    'W': 'Wood',      # Wood frame construction
    'M': 'Masonry',   # Masonry construction
    'C': 'Concrete',  # Concrete construction
    'S': 'Steel',     # Steel construction
    'H': 'Mobile Home' # Manufactured housing
}

# Building subtype index ranges by building type
# Used to map occupancy schemes to specific building subtypes
BUILDING_SUBTYPE_RANGES = {
    'W': (0, 5),     # Wood: columns 0-4
    'M': (5, 19),    # Masonry: columns 5-18
    'C': (19, 25),   # Concrete: columns 19-24
    'S': (25, 34),   # Steel: columns 25-33
    'H': (34, None)  # Mobile Home: columns 34+
}

# ==============================================================================
# OUTPUT FILE NAMES
# ==============================================================================

# Checkpoint file for building characterization
BUILDING_INVENTORY_CHECKPOINT = 'nsi_wbId_sr.csv'

# Final aggregated loss results
TOTAL_LOSS_OUTPUT = 'TotalLoss.csv'

# Individual building losses filename pattern
BUILDING_LOSSES_PATTERN = 'Losses.csv'

# ==============================================================================
# NETCDF VARIABLE NAMES
# ==============================================================================

# Required variables in NCAR NetCDF files
NETCDF_VARIABLES = {
    'wind': 'swath_wind',   # Wind speed swath data
    'longitude': 'lon_2d',  # 2D longitude array
    'latitude': 'lat_2d'    # 2D latitude array
}

# Output CSV column names for processed wind data
WIND_CSV_COLUMNS = ['Longitude', 'Latitude', 'Wind_Speed', 'Gust_Wind_Speed']

# ==============================================================================
# NSI (NATIONAL STRUCTURE INVENTORY) COLUMNS
# ==============================================================================

# Key NSI columns used in analysis
NSI_COLUMNS = {
    'foundation_id': 'fd_id',           # Foundation ID (unique building identifier)
    'county_fips': 'cbfips',            # Census block FIPS code
    'occupancy': 'occtype',             # Occupancy type
    'building_type': 'bldgtype',        # Building construction type
    'surface_roughness': 'nsi_val.SURFACEROU',  # Surface roughness for terrain
    'structure_value': 'val_struct',    # Structural replacement value
    'contents_value': 'val_cont'        # Contents replacement value
}
