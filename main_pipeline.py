"""
Hurricane Ida Wind Loss Analysis Pipeline

This is the main entry point for the Hurricane Ida wind loss analysis pipeline.
It orchestrates the processing of NCAR climate model data, spatial joining with
building inventories, and calculation of wind damage losses.

Usage:
------
python main_pipeline.py --ncar-dir ./data/ncar_netcdf --nsi-path ./data/nsi/nsi_2022_22.gpkg --hazus-dir ./data/hazus --output-dir ./output

For full usage information:
python main_pipeline.py --help

Author: Claude Code Pipeline Generator
Date: 2025
"""

import os
import sys
import argparse
import logging
from datetime import datetime
import config
from modules import netcdf_processor, spatial_join, building_losses


def setup_logging(output_dir):
    """
    Set up logging to both console and file.

    Parameters:
    -----------
    output_dir : str
        Output directory where logs/ subdirectory will be created

    Returns:
    --------
    str
        Path to the created log file
    """
    # Create logs directory
    logs_dir = os.path.join(output_dir, '../logs')
    os.makedirs(logs_dir, exist_ok=True)

    # Generate log filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(logs_dir, f'pipeline_{timestamp}.log')

    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Remove any existing handlers
    logger.handlers = []

    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter(
        '%(levelname)-8s | %(message)s'
    )

    # File handler
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return log_file


def validate_inputs(args):
    """
    Validate all input paths and files exist.

    Parameters:
    -----------
    args : argparse.Namespace
        Parsed command-line arguments

    Raises:
    -------
    FileNotFoundError
        If any required input files or directories are missing
    """
    logger = logging.getLogger(__name__)

    logger.info("="*70)
    logger.info("INPUT VALIDATION")
    logger.info("="*70)

    errors = []

    # Check NCAR directory
    logger.info(f"\nChecking NCAR NetCDF directory: {args.ncar_dir}")
    if not os.path.exists(args.ncar_dir):
        errors.append(f"NCAR directory not found: {args.ncar_dir}")
        logger.error(f"  ✗ Directory not found")
    else:
        logger.info(f"  ✓ Directory exists")
        # Check for NetCDF files
        for nc_file in config.NETCDF_FILES:
            nc_path = os.path.join(args.ncar_dir, nc_file)
            if not os.path.exists(nc_path):
                errors.append(f"NetCDF file not found: {nc_path}")
                logger.error(f"    ✗ Missing: {nc_file}")
            else:
                logger.info(f"    ✓ Found: {nc_file}")

    # Check NSI file
    logger.info(f"\nChecking NSI building inventory: {args.nsi_path}")
    if not os.path.exists(args.nsi_path):
        errors.append(f"NSI file not found: {args.nsi_path}")
        logger.error(f"  ✗ File not found")
    else:
        logger.info(f"  ✓ File exists")

    # Check Hazus directory
    logger.info(f"\nChecking Hazus directory: {args.hazus_dir}")
    if not os.path.exists(args.hazus_dir):
        errors.append(f"Hazus directory not found: {args.hazus_dir}")
        logger.error(f"  ✗ Directory not found")
    else:
        logger.info(f"  ✓ Directory exists")
        # Check for Hazus files
        for file_type, filename in config.HAZUS_FILES.items():
            hazus_path = os.path.join(args.hazus_dir, filename)
            if not os.path.exists(hazus_path):
                errors.append(f"Hazus {file_type} file not found: {hazus_path}")
                logger.error(f"    ✗ Missing: {filename}")
            else:
                logger.info(f"    ✓ Found: {filename}")

    # Check building inventory if provided
    if args.building_inventory:
        logger.info(f"\nChecking building inventory checkpoint: {args.building_inventory}")
        if not os.path.exists(args.building_inventory):
            errors.append(f"Building inventory file not found: {args.building_inventory}")
            logger.error(f"  ✗ File not found")
        else:
            logger.info(f"  ✓ File exists (will use for Step 3)")

    # Report errors
    if errors:
        logger.error(f"\n{'='*70}")
        logger.error("VALIDATION FAILED")
        logger.error(f"{'='*70}")
        logger.error(f"\nFound {len(errors)} error(s):")
        for i, error in enumerate(errors, 1):
            logger.error(f"  {i}. {error}")
        logger.error(f"\nPlease ensure all required data files are available.")
        logger.error(f"See README.md for data requirements and sources.")
        raise FileNotFoundError(f"Missing required input files ({len(errors)} errors)")

    logger.info(f"\n{'='*70}")
    logger.info("VALIDATION SUCCESSFUL - All required files found")
    logger.info(f"{'='*70}\n")


def run_pipeline(args):
    """
    Execute the full analysis pipeline.

    Parameters:
    -----------
    args : argparse.Namespace
        Parsed command-line arguments

    Returns:
    --------
    dict
        Dictionary containing paths to all output files
    """
    logger = logging.getLogger(__name__)

    # Determine which steps to run
    if args.steps:
        steps_to_run = [int(s.strip()) for s in args.steps.split(',')]
        logger.info(f"Running selected steps: {steps_to_run}")
    else:
        steps_to_run = [1, 2, 3]
        logger.info(f"Running all steps: {steps_to_run}")

    outputs = {}

    # STEP 1: Process NCAR NetCDF files
    if 1 in steps_to_run:
        wind_output_dir = os.path.join(args.output_dir, 'processed_wind')
        os.makedirs(wind_output_dir, exist_ok=True)

        wind_csv_paths = netcdf_processor.process_ncar_netcdf(
            ncar_dir=args.ncar_dir,
            output_dir=wind_output_dir,
            force_rerun=args.force_rerun
        )
        outputs['wind_csvs'] = wind_csv_paths
    else:
        # If step 1 skipped, need to find existing wind CSVs
        logger.info("Step 1 skipped - looking for existing wind CSV files...")
        wind_output_dir = os.path.join(args.output_dir, 'processed_wind')
        wind_csv_paths = {}
        for scenario in config.SCENARIOS:
            csv_path = os.path.join(wind_output_dir, f"{scenario}.csv")
            if os.path.exists(csv_path):
                wind_csv_paths[scenario] = csv_path
                logger.info(f"  Found: {csv_path}")
            else:
                logger.error(f"  Missing: {csv_path}")
                raise FileNotFoundError(f"Wind CSV not found (run with step 1): {csv_path}")
        outputs['wind_csvs'] = wind_csv_paths

    # STEP 2: Spatial join
    if 2 in steps_to_run:
        joined_output_dir = os.path.join(args.output_dir, 'joined_data')
        os.makedirs(joined_output_dir, exist_ok=True)

        joined_csv_paths = spatial_join.join_buildings_wind(
            nsi_path=args.nsi_path,
            wind_csv_paths=outputs['wind_csvs'],
            output_dir=joined_output_dir,
            force_rerun=args.force_rerun
        )
        outputs['joined_csvs'] = joined_csv_paths
    else:
        # If step 2 skipped, need to find existing joined CSVs
        logger.info("Step 2 skipped - looking for existing joined CSV files...")
        joined_output_dir = os.path.join(args.output_dir, 'joined_data')
        joined_csv_paths = {}
        for scenario in config.SCENARIOS:
            csv_path = os.path.join(joined_output_dir, scenario, f"{scenario}.csv")
            if os.path.exists(csv_path):
                joined_csv_paths[scenario] = csv_path
                logger.info(f"  Found: {csv_path}")
            else:
                logger.error(f"  Missing: {csv_path}")
                raise FileNotFoundError(f"Joined CSV not found (run with step 2): {csv_path}")
        outputs['joined_csvs'] = joined_csv_paths

    # STEP 3: Loss calculation
    if 3 in steps_to_run:
        inventory_output_dir = os.path.join(args.output_dir, 'building_inventory')
        results_output_dir = os.path.join(args.output_dir, 'results')
        os.makedirs(inventory_output_dir, exist_ok=True)
        os.makedirs(results_output_dir, exist_ok=True)

        # Step 3A: Building characterization (with checkpointing)
        if args.building_inventory:
            # Use provided checkpoint
            logger.info(f"Using provided building inventory: {args.building_inventory}")
            import pandas as pd
            building_inventory = pd.read_csv(args.building_inventory)
        else:
            # Run characterization (or load checkpoint if exists)
            # Need to load NSI data from one of the joined files
            import pandas as pd
            first_scenario = list(outputs['joined_csvs'].keys())[0]
            nsi_data = pd.read_csv(outputs['joined_csvs'][first_scenario])

            building_inventory = building_losses.characterize_buildings(
                nsi_data=nsi_data,
                hazus_dir=args.hazus_dir,
                output_dir=inventory_output_dir,
                force_rerun=args.force_rerun
            )

        outputs['building_inventory'] = building_inventory

        # Step 3B: Calculate individual building losses
        loss_csv_paths = building_losses.calculate_building_losses(
            building_inventory=building_inventory,
            joined_data_paths=outputs['joined_csvs'],
            hazus_dir=args.hazus_dir,
            output_dir=results_output_dir,
            force_rerun=args.force_rerun
        )
        outputs['loss_csvs'] = loss_csv_paths

        # Step 3C: Aggregate to county level
        total_loss_csv = building_losses.aggregate_county_losses(
            loss_data_paths=loss_csv_paths,
            output_dir=results_output_dir,
            force_rerun=args.force_rerun
        )
        outputs['total_loss_csv'] = total_loss_csv

    return outputs


def main():
    """
    Main entry point for the pipeline.
    """
    # Create argument parser
    parser = argparse.ArgumentParser(
        description='Hurricane Ida Wind Loss Analysis Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full pipeline run
  python main_pipeline.py --ncar-dir ./data/ncar_netcdf --nsi-path ./data/nsi/nsi_2022_22.gpkg --hazus-dir ./data/hazus --output-dir ./output

  # Use existing building characterization checkpoint
  python main_pipeline.py --ncar-dir ./data/ncar_netcdf --nsi-path ./data/nsi/nsi_2022_22.gpkg --hazus-dir ./data/hazus --output-dir ./output --building-inventory ./output/building_inventory/nsi_wbId_sr.csv

  # Run specific steps only
  python main_pipeline.py --ncar-dir ./data/ncar_netcdf --nsi-path ./data/nsi/nsi_2022_22.gpkg --hazus-dir ./data/hazus --output-dir ./output --steps 1,2

For more information, see README.md
        """
    )

    # Required arguments
    parser.add_argument(
        '--ncar-dir',
        required=True,
        help='Path to directory containing NCAR NetCDF files (ida_1971.nc, ida_2021.nc, ida_2071.nc)'
    )

    parser.add_argument(
        '--nsi-path',
        required=True,
        help='Path to NSI GeoPackage file (nsi_2022_22.gpkg)'
    )

    parser.add_argument(
        '--hazus-dir',
        required=True,
        help='Path to directory containing Hazus files (Mapping.xlsx, huDamLossFunc.csv)'
    )

    # Optional arguments
    parser.add_argument(
        '--output-dir',
        default='./output',
        help='Output directory for results (default: ./output)'
    )

    parser.add_argument(
        '--building-inventory',
        help='Path to existing building characterization file (nsi_wbId_sr.csv) to skip expensive Step 3A'
    )

    parser.add_argument(
        '--steps',
        help='Comma-separated list of steps to run (e.g., "1,2" or "3"). Default: all steps (1,2,3)'
    )

    parser.add_argument(
        '--force-rerun',
        action='store_true',
        help='Force reprocessing even if output files already exist'
    )

    # Parse arguments
    args = parser.parse_args()

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Set up logging
    log_file = setup_logging(args.output_dir)

    # Get logger for main module
    logger = logging.getLogger(__name__)

    # Print header
    logger.info("")
    logger.info("="*70)
    logger.info("HURRICANE IDA WIND LOSS ANALYSIS PIPELINE")
    logger.info("="*70)
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Log file: {log_file}")
    logger.info("="*70)

    # Log configuration
    logger.info("\nPipeline Configuration:")
    logger.info(f"  NCAR directory: {args.ncar_dir}")
    logger.info(f"  NSI file: {args.nsi_path}")
    logger.info(f"  Hazus directory: {args.hazus_dir}")
    logger.info(f"  Output directory: {args.output_dir}")
    logger.info(f"  Building inventory: {args.building_inventory or 'Will compute/load checkpoint'}")
    logger.info(f"  Steps to run: {args.steps or 'All (1,2,3)'}")
    logger.info(f"  Force rerun: {args.force_rerun}")
    logger.info("")

    try:
        # Validate inputs
        validate_inputs(args)

        # Run pipeline
        start_time = datetime.now()
        logger.info(f"Starting pipeline execution at {start_time.strftime('%H:%M:%S')}\n")

        outputs = run_pipeline(args)

        end_time = datetime.now()
        elapsed = end_time - start_time

        # Print summary
        logger.info("="*70)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("="*70)
        logger.info(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Total elapsed time: {elapsed}")
        logger.info(f"\nOutput files:")

        if 'wind_csvs' in outputs:
            logger.info(f"\nProcessed wind data:")
            for scenario, path in outputs['wind_csvs'].items():
                logger.info(f"  {scenario}: {path}")

        if 'joined_csvs' in outputs:
            logger.info(f"\nSpatially joined data:")
            for scenario, path in outputs['joined_csvs'].items():
                logger.info(f"  {scenario}: {path}")

        if 'total_loss_csv' in outputs:
            logger.info(f"\nFinal results:")
            logger.info(f"  Total losses: {outputs['total_loss_csv']}")

        logger.info(f"\nLog file: {log_file}")
        logger.info("="*70)

        return 0

    except Exception as e:
        logger.error("")
        logger.error("="*70)
        logger.error("PIPELINE FAILED")
        logger.error("="*70)
        logger.error(f"Error: {str(e)}")
        logger.error(f"\nCheck log file for details: {log_file}")
        logger.error("="*70)
        return 1


if __name__ == '__main__':
    sys.exit(main())
