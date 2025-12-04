"""
Spatial Join Module for NSI Buildings and NCAR Wind Data

This module performs nearest neighbor spatial joins between the National Structure
Inventory (NSI) building database and NCAR climate model wind data to assign wind
speeds to individual buildings.

Functions:
----------
join_buildings_wind : Spatially join NSI buildings with NCAR wind data
"""

import os
import logging
import pandas as pd
import geopandas as gpd
from shapely import Point
import config

logger = logging.getLogger(__name__)


def join_buildings_wind(nsi_path, wind_csv_paths, output_dir, force_rerun=False):
    """
    Spatially join NSI buildings with NCAR wind data using nearest neighbor.

    This function performs a spatial join between the NSI building inventory and
    processed NCAR wind data. Each building is assigned wind speeds from the
    nearest NCAR model grid point using projected coordinates for accurate
    distance calculations.

    Parameters:
    -----------
    nsi_path : str
        Path to NSI GeoPackage file (nsi_2022_22.gpkg)
    wind_csv_paths : dict
        Dictionary mapping scenario names to wind CSV file paths
        Example: {'ida_1971': '/path/to/ida_1971.csv', ...}
    output_dir : str
        Directory for joined data outputs
    force_rerun : bool, optional
        If True, rejoin even if output files exist. Default is False.

    Returns:
    --------
    dict
        Dictionary mapping scenario names to joined CSV file paths
        Example: {'ida_1971': '/path/to/joined/ida_1971.csv', ...}

    Raises:
    -------
    FileNotFoundError
        If NSI GeoPackage or wind CSV files are not found
    ValueError
        If CRS is incompatible or data structures are unexpected

    Processing Steps:
    -----------------
    1. Load NSI building inventory from GeoPackage
    2. For each climate scenario:
       a. Load wind CSV and convert to GeoDataFrame with Point geometries
       b. Set CRS to EPSG:4326 (WGS 84)
       c. Project both datasets to EPSG:26915 (NAD83 / UTM zone 15N)
       d. Perform nearest neighbor spatial join
       e. Calculate and log join distance statistics
       f. Save joined data to CSV

    Output Format:
    --------------
    Joined CSV contains all NSI building attributes plus:
    - Longitude : Wind grid point longitude
    - Latitude : Wind grid point latitude
    - Wind_Speed : Sustained wind speed (mph)
    - Gust_Wind_Speed : 3-second gust wind speed (mph)
    - distance : Distance from building to nearest wind grid point (meters)

    Notes:
    ------
    - Uses projected CRS (EPSG:26915) for accurate distance calculation
    - NAD83 / UTM zone 15N is appropriate for Louisiana/Gulf Coast region
    - Distance column helps assess quality of spatial join

    Example:
    --------
    >>> joined_files = join_buildings_wind(
    ...     nsi_path='./data/nsi/nsi_2022_22.gpkg',
    ...     wind_csv_paths={'ida_2021': './output/processed_wind/ida_2021.csv'},
    ...     output_dir='./output/joined_data'
    ... )
    >>> print(joined_files)
    {'ida_2021': './output/joined_data/ida_2021/ida_2021.csv'}
    """

    logger.info("="*70)
    logger.info("STEP 2: Spatial Join of Buildings and Wind Data")
    logger.info("="*70)

    # Validate NSI file exists
    if not os.path.exists(nsi_path):
        error_msg = f"NSI file not found: {nsi_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    logger.info(f"Loading NSI building inventory: {nsi_path}")

    try:
        # Load NSI data from GeoPackage
        nsi = gpd.read_file(nsi_path)
        logger.info(f"  ✓ Loaded {len(nsi):,} buildings")
        logger.info(f"  Original CRS: {nsi.crs}")

        # Project to target CRS for accurate distance calculations
        logger.info(f"  Projecting to {config.PROJECTED_CRS} for distance calculation...")
        nsi_projected = nsi.to_crs(config.PROJECTED_CRS)
        logger.info(f"  ✓ Projection complete")

    except Exception as e:
        logger.error(f"  ✗ Error loading NSI data: {str(e)}")
        raise

    # Process each scenario
    joined_files = {}

    for scenario, wind_csv in wind_csv_paths.items():
        logger.info(f"\nProcessing scenario: {scenario}")

        # Create scenario-specific output directory
        scenario_output_dir = os.path.join(output_dir, scenario)
        os.makedirs(scenario_output_dir, exist_ok=True)

        output_csv = os.path.join(scenario_output_dir, f"{scenario}.csv")

        # Skip if output already exists and force_rerun is False
        if os.path.exists(output_csv) and not force_rerun:
            logger.info(f"  Output already exists: {output_csv}")
            logger.info(f"  Skipping join (use --force-rerun to rejoin)")
            joined_files[scenario] = output_csv
            continue

        try:
            # Validate wind CSV exists
            if not os.path.exists(wind_csv):
                error_msg = f"Wind CSV not found: {wind_csv}"
                logger.error(f"  ✗ {error_msg}")
                raise FileNotFoundError(error_msg)

            logger.info(f"  Loading wind data: {os.path.basename(wind_csv)}")
            wind_df = pd.read_csv(wind_csv)
            logger.info(f"    ✓ Loaded {len(wind_df):,} wind grid points")

            # Create Point geometries from longitude/latitude
            logger.info(f"  Creating wind point geometries...")
            points = [Point(row["Longitude"], row["Latitude"])
                     for index, row in wind_df.iterrows()]
            wind_gdf = gpd.GeoDataFrame(wind_df, geometry=points)

            # Set CRS (WGS 84 geographic coordinates)
            wind_gdf.crs = config.INPUT_CRS
            logger.info(f"    Set CRS: {wind_gdf.crs}")

            # Project to same CRS as NSI for spatial join
            logger.info(f"  Projecting wind data to {config.PROJECTED_CRS}...")
            wind_gdf_projected = wind_gdf.to_crs(config.PROJECTED_CRS)
            logger.info(f"    ✓ Projection complete")

            # Perform nearest neighbor spatial join
            logger.info(f"  Performing nearest neighbor spatial join...")
            logger.info(f"    This may take several minutes for large datasets...")
            joined_gdf = gpd.sjoin_nearest(
                nsi_projected,
                wind_gdf_projected,
                how='left',
                distance_col='distance'
            )
            logger.info(f"    ✓ Join complete")

            # Log join statistics
            logger.info(f"  Join statistics:")
            logger.info(f"    Buildings joined: {len(joined_gdf):,}")
            logger.info(f"    Mean distance: {joined_gdf['distance'].mean():.2f} meters")
            logger.info(f"    Median distance: {joined_gdf['distance'].median():.2f} meters")
            logger.info(f"    Max distance: {joined_gdf['distance'].max():.2f} meters")
            logger.info(f"    Buildings with distance > 1km: {(joined_gdf['distance'] > 1000).sum():,}")

            # Check for any buildings without wind data
            missing_wind = joined_gdf['Gust_Wind_Speed'].isna().sum()
            if missing_wind > 0:
                logger.warning(f"    ⚠ {missing_wind} buildings missing wind data!")

            # Save to CSV
            logger.info(f"  Saving joined data: {output_csv}")
            joined_gdf.to_csv(output_csv, index=False)
            logger.info(f"  ✓ Successfully joined {scenario}")

            joined_files[scenario] = output_csv

        except Exception as e:
            logger.error(f"  ✗ Error joining {scenario}: {str(e)}")
            raise

    logger.info(f"\n{'='*70}")
    logger.info(f"Step 2 Complete: Joined {len(joined_files)} scenarios")
    logger.info(f"{'='*70}\n")

    return joined_files
