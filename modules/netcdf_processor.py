"""
NCAR NetCDF Climate Model Data Processor

This module processes NCAR climate model NetCDF files containing Hurricane Ida
wind swath data across different climate scenarios (1971, 2021, 2071).

Functions:
----------
process_ncar_netcdf : Main function to process all NetCDF files to CSV format
"""

import os
import logging
import netCDF4
import pandas as pd
import config

logger = logging.getLogger(__name__)


def process_ncar_netcdf(ncar_dir, output_dir, force_rerun=False):
    """
    Process NCAR NetCDF climate model output to CSV format.

    This function extracts wind speed data from NCAR climate model NetCDF files
    and converts it to CSV format with gust wind speeds calculated according to
    ASCE 7-16 standards.

    Parameters:
    -----------
    ncar_dir : str
        Directory containing NetCDF files (ida_1971.nc, ida_2021.nc, ida_2071.nc)
    output_dir : str
        Directory for processed CSV outputs
    force_rerun : bool, optional
        If True, reprocess even if output files exist. Default is False.

    Returns:
    --------
    dict
        Dictionary mapping scenario names to output CSV file paths
        Example: {'ida_1971': '/path/to/ida_1971.csv', ...}

    Raises:
    -------
    FileNotFoundError
        If any required NetCDF files are not found in ncar_dir
    KeyError
        If NetCDF file is missing required variables (swath_wind, lon_2d, lat_2d)
    ValueError
        If NetCDF data has unexpected structure or dimensions

    Processing Steps:
    -----------------
    1. Validate all NetCDF files exist
    2. For each NetCDF file:
       a. Extract 2D arrays: swath_wind, lon_2d, lat_2d
       b. Flatten to 1D arrays
       c. Apply gust factor: gust = wind × 1.28 (ASCE 7-16 standard)
       d. Convert units: m/s to mph (× 2.23694)
       e. Adjust longitude: -360 to convert from [0,360°] to [-180,180°]
    3. Save to CSV with columns: Longitude, Latitude, Wind_Speed, Gust_Wind_Speed

    Output CSV Format:
    ------------------
    - Longitude : float, degrees [-180, 180]
    - Latitude : float, degrees [-90, 90]
    - Wind_Speed : float, mph (sustained wind)
    - Gust_Wind_Speed : float, mph (3-second gust)

    Notes:
    ------
    - Gust factor of 1.28 is based on ASCE 7-16 Section 26.5
    - Longitude adjustment accounts for NCAR's 0-360° convention
    - Output files are named ida_YYYY.csv where YYYY is the climate year

    Example:
    --------
    >>> output_files = process_ncar_netcdf(
    ...     ncar_dir='./data/ncar_netcdf',
    ...     output_dir='./output/processed_wind'
    ... )
    >>> print(output_files)
    {'ida_1971': './output/processed_wind/ida_1971.csv', ...}
    """

    logger.info("="*70)
    logger.info("STEP 1: Processing NCAR NetCDF Files")
    logger.info("="*70)

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Validate all NetCDF files exist before processing
    logger.info(f"Checking for NetCDF files in: {ncar_dir}")
    missing_files = []
    for netcdf_file in config.NETCDF_FILES:
        netcdf_path = os.path.join(ncar_dir, netcdf_file)
        if not os.path.exists(netcdf_path):
            missing_files.append(netcdf_file)
            logger.error(f"  ✗ Missing: {netcdf_file}")
        else:
            logger.info(f"  ✓ Found: {netcdf_file}")

    if missing_files:
        error_msg = f"Missing NetCDF files: {', '.join(missing_files)}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    # Process each NetCDF file
    output_files = {}

    for netcdf_file in config.NETCDF_FILES:
        # Extract scenario name (e.g., 'ida_1971' from 'ida_1971.nc')
        scenario = os.path.splitext(netcdf_file)[0]
        output_csv = os.path.join(output_dir, f"{scenario}.csv")

        # Skip if output already exists and force_rerun is False
        if os.path.exists(output_csv) and not force_rerun:
            logger.info(f"\nScenario: {scenario}")
            logger.info(f"  Output already exists: {output_csv}")
            logger.info(f"  Skipping processing (use --force-rerun to reprocess)")
            output_files[scenario] = output_csv
            continue

        logger.info(f"\nProcessing scenario: {scenario}")
        logger.info(f"  Input: {netcdf_file}")

        try:
            # Open NetCDF file
            netcdf_path = os.path.join(ncar_dir, netcdf_file)
            nc = netCDF4.Dataset(netcdf_path, 'r')

            # Validate required variables exist
            required_vars = config.NETCDF_VARIABLES
            missing_vars = []
            for var_name, var_key in required_vars.items():
                if var_key not in nc.variables:
                    missing_vars.append(var_key)

            if missing_vars:
                nc.close()
                error_msg = f"NetCDF file {netcdf_file} missing variables: {', '.join(missing_vars)}"
                logger.error(f"  ✗ {error_msg}")
                raise KeyError(error_msg)

            # Extract 2D arrays
            logger.info(f"  Extracting wind swath data...")
            swath_wind = nc[required_vars['wind']][:]
            lon_2d = nc[required_vars['longitude']][:]
            lat_2d = nc[required_vars['latitude']][:]

            # Log array dimensions
            logger.info(f"    Wind array shape: {swath_wind.shape}")
            logger.info(f"    Longitude array shape: {lon_2d.shape}")
            logger.info(f"    Latitude array shape: {lat_2d.shape}")

            # Close NetCDF file
            nc.close()

            # Flatten arrays to 1D
            logger.info(f"  Flattening 2D arrays to 1D...")
            longitude = lon_2d.flatten()
            latitude = lat_2d.flatten()
            wind_speed = swath_wind.flatten()

            # Calculate gust wind speed
            # gust = sustained_wind × gust_factor × unit_conversion
            logger.info(f"  Calculating gust wind speeds...")
            logger.info(f"    Gust factor: {config.GUST_FACTOR_NCAR}")
            logger.info(f"    Unit conversion (m/s to mph): {config.MS_TO_MPH}")
            gust_wind_speed = wind_speed * config.GUST_FACTOR_NCAR * config.MS_TO_MPH

            # Adjust longitude from [0,360] to [-180,180]
            logger.info(f"  Adjusting longitude coordinates...")
            longitude_adjusted = longitude + config.LONGITUDE_ADJUSTMENT

            # Create DataFrame
            df = pd.DataFrame({
                'Longitude': longitude_adjusted,
                'Latitude': latitude,
                'Wind_Speed': wind_speed,
                'Gust_Wind_Speed': gust_wind_speed
            })

            # Log statistics
            logger.info(f"  Data statistics:")
            logger.info(f"    Total grid points: {len(df):,}")
            logger.info(f"    Max gust wind speed: {df['Gust_Wind_Speed'].max():.2f} mph")
            logger.info(f"    Longitude range: [{df['Longitude'].min():.2f}, {df['Longitude'].max():.2f}]")
            logger.info(f"    Latitude range: [{df['Latitude'].min():.2f}, {df['Latitude'].max():.2f}]")

            # Save to CSV
            logger.info(f"  Saving to: {output_csv}")
            df.to_csv(output_csv, index=False)
            logger.info(f"  ✓ Successfully processed {scenario}")

            output_files[scenario] = output_csv

        except Exception as e:
            logger.error(f"  ✗ Error processing {netcdf_file}: {str(e)}")
            raise

    logger.info(f"\n{'='*70}")
    logger.info(f"Step 1 Complete: Processed {len(output_files)} scenarios")
    logger.info(f"{'='*70}\n")

    return output_files
