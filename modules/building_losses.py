"""
Building Loss Calculation Module

This module handles building characterization, damage function assignment, and
loss calculation for wind hazard analysis using Hazus methodology.

Functions:
----------
characterize_buildings : Assign Hazus building types to NSI buildings (with checkpointing)
calculate_building_losses : Calculate individual building wind losses
aggregate_county_losses : Aggregate losses to county level
"""

import os
import logging
import numpy as np
import pandas as pd
import config

logger = logging.getLogger(__name__)


def characterize_buildings(nsi_data, hazus_dir, output_dir, force_rerun=False):
    """
    Assign Hazus building types and damage functions to NSI buildings.

    ⚠️  COMPUTATIONALLY EXPENSIVE - Uses checkpointing (30-60 min runtime)

    This function maps NSI building records to Hazus building types (wbID) and
    terrain IDs through a multi-level probabilistic assignment process. Results
    are checkpointed to enable reuse across multiple runs.

    Parameters:
    -----------
    nsi_data : str or DataFrame
        Path to NSI CSV file or DataFrame containing NSI building data
    hazus_dir : str
        Directory containing Hazus mapping files (Mapping.xlsx, huDamLossFunc.csv)
    output_dir : str
        Output directory for checkpoint file
    force_rerun : bool, optional
        If True, ignore existing checkpoint and recompute. Default is False.

    Returns:
    --------
    DataFrame
        Building inventory with added columns:
        - wbID : Wind building type ID (Hazus)
        - terrainID : Terrain classification ID (1-5)

    Raises:
    -------
    FileNotFoundError
        If Hazus mapping files are not found
    KeyError
        If required columns are missing from input data

    Checkpointing:
    --------------
    - Checkpoint file: {output_dir}/nsi_wbId_sr.csv
    - If checkpoint exists and force_rerun=False: Load and return (FAST ~seconds)
    - If checkpoint missing or force_rerun=True: Run full characterization (SLOW ~30-60 min)

    Processing Steps:
    -----------------
    1. Load Hazus mapping schemes from Excel workbook
    2. For each county FIPS code:
       a. Determine applicable Hazus building scheme
       b. For each occupancy type:
          - Map to building subtypes using probabilistic distribution
       c. For each building type (Wood/Masonry/Concrete/Steel/Mobile):
          - Select appropriate subtype names
          - Assign building characteristics (shutters, garage, etc.)
       d. Match building characteristics to wind building type (wbID)
    3. Calculate terrain ID from surface roughness
    4. Save checkpoint file

    Building Type Mapping:
    ----------------------
    - W (Wood): Residential wood frame construction
    - M (Masonry): Masonry and brick construction
    - C (Concrete): Reinforced concrete construction
    - S (Steel): Steel frame construction
    - H (Mobile Home): Manufactured housing

    Terrain Classification:
    -----------------------
    Based on surface roughness (nsi_val.SURFACEROU):
    - ID 1: Open (0.00-0.03) - Water, flat open land
    - ID 2: Light suburban (0.03-0.15)
    - ID 3: Suburban (0.15-0.35)
    - ID 4: Light urban (0.35-0.70)
    - ID 5: Urban (>0.70)

    Notes:
    ------
    - Uses random seed {config.RANDOM_SEED} for reproducibility
    - All probabilistic assignments are deterministic given the seed
    - Checkpoint file contains full NSI dataset with wbID and terrainID added

    Example:
    --------
    >>> building_inventory = characterize_buildings(
    ...     nsi_data='./data/nsi_buildings.csv',
    ...     hazus_dir='./data/hazus',
    ...     output_dir='./output/building_inventory'
    ... )
    >>> print(building_inventory[['fd_id', 'wbID', 'terrainID']].head())
    """

    logger.info("="*70)
    logger.info("STEP 3A: Building Characterization")
    logger.info("="*70)

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Define checkpoint path
    checkpoint_path = os.path.join(output_dir, config.BUILDING_INVENTORY_CHECKPOINT)

    # Check for existing checkpoint
    if os.path.exists(checkpoint_path) and not force_rerun:
        logger.info(f"✓ Loading existing building characterization checkpoint")
        logger.info(f"  File: {checkpoint_path}")
        try:
            building_data = pd.read_csv(checkpoint_path)
            logger.info(f"  Loaded {len(building_data):,} buildings")
            logger.info(f"  Columns: {list(building_data.columns)}")
            logger.info(f"\n⚡ Using cached characterization (skipped ~30-60 min processing)")
            logger.info(f"{'='*70}\n")
            return building_data
        except Exception as e:
            logger.warning(f"  ⚠ Error loading checkpoint: {e}")
            logger.warning(f"  Will recompute characterization...")

    logger.info("⚠️  Running full building characterization (this may take 30-60 minutes)")
    logger.info("   This expensive operation will be cached for future runs\n")

    # Load NSI data
    if isinstance(nsi_data, str):
        logger.info(f"Loading NSI data: {nsi_data}")
        nsi_cb = pd.read_csv(nsi_data)
    else:
        nsi_cb = nsi_data.copy()

    logger.info(f"  ✓ Loaded {len(nsi_cb):,} buildings")

    # Validate Hazus files exist
    mapping_file = os.path.join(hazus_dir, config.HAZUS_FILES['mapping'])
    if not os.path.exists(mapping_file):
        raise FileNotFoundError(f"Hazus mapping file not found: {mapping_file}")

    logger.info(f"\nLoading Hazus mapping schemes...")
    logger.info(f"  File: {mapping_file}")

    try:
        # Load Hazus mapping tables
        huMappingSchemesByCountyFips = pd.read_excel(
            mapping_file, sheet_name=config.HAZUS_SHEETS['county_mapping'])
        huGbsOccMapping = pd.read_excel(
            mapping_file, sheet_name=config.HAZUS_SHEETS['occ_mapping'])
        huBldgMapping = pd.read_excel(
            mapping_file, sheet_name=config.HAZUS_SHEETS['bldg_mapping'])
        huListofBldgChar = pd.read_excel(
            mapping_file, sheet_name=config.HAZUS_SHEETS['bldg_char'])
        huListOfWindBldgTypes = pd.read_excel(
            mapping_file, sheet_name=config.HAZUS_SHEETS['wind_types'])

        logger.info(f"  ✓ Loaded all Hazus mapping tables")

    except Exception as e:
        logger.error(f"  ✗ Error loading Hazus mappings: {e}")
        raise

    # Extract unique character types
    charTypes = [i for i in huListofBldgChar['CharType'].unique()]
    logger.info(f"  Building characteristic types: {len(charTypes)}")

    # Create county FIPS column
    logger.info(f"\nPreparing county-level processing...")
    nsi_cb['countyFIPS'] = nsi_cb['cbfips'].astype(str).str[:5]
    cfips = [str(io) for i in nsi_cb['countyFIPS'].unique()]
    logger.info(f"  Counties to process: {len(cfips)}")

    # Initialize building list for results
    building_list = []
    seed = config.RANDOM_SEED
    np.random.seed(seed)

    logger.info(f"\nBeginning building characterization loop...")
    logger.info(f"  Using random seed: {seed} (for reproducibility)")
    logger.info(f"  This will process all counties, occupancy types, and building types")
    logger.info(f"  Progress updates every 10 counties...\n")

    # Main characterization loop
    county_count = 0
    for cfip in cfips:
        county_count += 1

        # Progress logging
        if county_count % 10 == 0:
            logger.info(f"  Processed {county_count}/{len(cfips)} counties...")

        df0 = nsi_cb.loc[nsi_cb['countyFIPS']==str(cfip)].copy()

        # Get Hazus building scheme for this county
        try:
            huBldgSchemeName = huMappingSchemesByCountyFips[
                huMappingSchemesByCountyFips['CountyFIPS']==int(cfip)
            ].iloc[0]['huBldgSchemeName']
        except:
            logger.warning(f"  ⚠ No mapping scheme for county {cfip}, skipping...")
            continue

        huOccMap = huGbsOccMapping[huGbsOccMapping['huOccMapSchemeName']==huBldgSchemeName]

        # Process each occupancy type
        occtypes = [i for i in df0['occtype'].unique()]
        for occ in occtypes:
            df1 = df0.loc[df0['occtype']==occ].copy()

            # Handle occupancy suffix
            if '-' in occ:
                indx = occ.find('-')
                occ = occ[:indx]

            huOcc = huOccMap[huOccMap['Occupancy'] == occ]
            if len(huOcc) == 0:
                continue

            Occschemes = huOcc.columns[2:]

            # Process each building type
            bldgTypes = [i for i in df1['bldgtype'].unique()]
            for bldgType in bldgTypes:
                df2 = df1.loc[df1['bldgtype']==bldgType].copy()

                # Select subtype names based on building type
                if bldgType == 'W':
                    sbtNames = Occschemes[0:5]
                elif bldgType == 'M':
                    sbtNames = Occschemes[5:19]
                elif bldgType == 'C':
                    sbtNames = Occschemes[19:25]
                elif bldgType == 'S':
                    sbtNames = Occschemes[25:34]
                elif bldgType == 'H':
                    sbtNames = Occschemes[34:]
                else:
                    continue

                # Probabilistic subtype assignment
                OccMapProb = [i/100 for i in huOcc[sbtNames].values.flatten().tolist()]

                df2['sbtName'] = pd.NA
                np.random.seed(seed)
                df2['sbtName'] = df2['sbtName'].apply(
                    lambda x: np.random.choice(sbtNames, p=OccMapProb))

                # Process each subtype
                sbts = [i for i in df2['sbtName'].unique()]
                for sbt in sbts:
                    df3 = df2.loc[df2['sbtName']==sbt].copy()

                    huBldg = huBldgMapping.loc[
                        (huBldgMapping['huBldgSchemeName']==huBldgSchemeName) &
                        (huBldgMapping['sbtName']==sbt)
                    ].copy()

                    if len(huBldg) == 0:
                        continue

                    bldgCharId = huBldg['BLDGCHARID'].values.flatten().tolist()
                    char_desc = []

                    # Assign building characteristics
                    for charType in charTypes:
                        main = huListofBldgChar.loc[
                            huListofBldgChar['CharType']==charType].copy()
                        main_list = main['BldgCharID'].values.flatten().tolist()
                        check = any(item in bldgCharId for item in main_list)

                        if check is True:
                            char_desc.append(charType)
                            bldgChar = main['BldgChar'].values.flatten().tolist()

                            probs_df = huBldg[huBldg['BLDGCHARID'].isin(main_list)]
                            probs_df = probs_df.sort_values(by=['BLDGCHARID'])
                            probs = [i/100 for i in probs_df['PercentDist'].values.flatten().tolist()]

                            if len(probs) < len(bldgChar):
                                bldgChar1 = bldgChar[0:len(probs)]
                            else:
                                bldgChar1 = bldgChar

                            df3[charType] = pd.NA
                            np.random.seed(seed)
                            df3[charType] = df3[charType].apply(
                                lambda x: np.random.choice(bldgChar1, p=probs))
                        else:
                            df3[charType] = pd.NA

                    # Match to wind building type and calculate terrain ID
                    for row in range(len(df3)):
                        rows = df3.iloc[row]
                        wbId_df = huListOfWindBldgTypes.loc[
                            huListOfWindBldgTypes['sbtName']==sbt]
                        char_desc1 = char_desc.copy()

                        # Handle shutter characteristic
                        if "Shutters" in char_desc1:
                            if rows["Shutters"] == "shtys":
                                if "Garage, Houses w/out Shutters" in char_desc1:
                                    char_desc1.remove("Garage, Houses w/out Shutters")
                            else:
                                if "Garage, Houses with Shutters" in char_desc1:
                                    char_desc1.remove("Garage, Houses with Shutters")

                        # Match characteristics to wbID
                        for char in char_desc1:
                            sample1 = wbId_df[wbId_df['charDescription'].str.contains(rows[char], na=False)]
                            if len(sample1) != 0:
                                wbId_df = sample1

                        wbID = wbId_df['wbID'].values.flatten().tolist()

                        if len(wbID) == 0:
                            wbID = pd.NA
                        elif len(wbID) == 1:
                            wbID = wbID[0]
                        else:
                            wbID = wbID[0]  # Take first if multiple matches

                        # Calculate terrain ID from surface roughness
                        terrain = rows['nsi_val.SURFACEROU']
                        if terrain <= 0.03:
                            terrain_ID = 1
                        elif 0.03 < terrain <= 0.15:
                            terrain_ID = 2
                        elif 0.15 < terrain <= 0.35:
                            terrain_ID = 3
                        elif 0.35 < terrain <= 0.7:
                            terrain_ID = 4
                        else:
                            terrain_ID = 5

                        # Append result
                        datas = [str(i) for i in rows]
                        datas.append(wbID)
                        datas.append(str(terrain_ID))
                        building_list.append(datas)

    logger.info(f"  ✓ Processed all {county_count} counties")

    # Create final DataFrame
    logger.info(f"\nCreating final building inventory DataFrame...")
    building_data = pd.DataFrame(building_list)
    building_data.columns = rows.index.tolist() + ["wbID", "terrainID"]
    logger.info(f"  ✓ Created DataFrame with {len(building_data):,} buildings")

    # Save checkpoint
    logger.info(f"\nSaving checkpoint: {checkpoint_path}")
    building_data.to_csv(checkpoint_path, index=False)
    logger.info(f"  ✓ Checkpoint saved successfully")
    logger.info(f"  Future runs will load this file instead of recomputing\n")

    logger.info(f"{'='*70}")
    logger.info(f"Step 3A Complete: Building Characterization")
    logger.info(f"{'='*70}\n")

    return building_data


def calculate_building_losses(building_inventory, joined_data_paths, hazus_dir, output_dir, force_rerun=False):
    """
    Calculate individual building losses for each climate scenario.

    This function calculates building and contents losses by interpolating damage
    ratios from Hazus damage functions based on wind speeds assigned to each building.

    Parameters:
    -----------
    building_inventory : DataFrame
        Building data with wbID and terrainID (from characterize_buildings)
    joined_data_paths : dict
        Dictionary mapping scenario names to joined CSV paths
        Example: {'ida_1971': '/path/to/joined/ida_1971.csv', ...}
    hazus_dir : str
        Directory containing Hazus damage functions (huDamLossFunc.csv)
    output_dir : str
        Directory for loss calculation outputs
    force_rerun : bool, optional
        If True, recalculate even if output files exist. Default is False.

    Returns:
    --------
    dict
        Dictionary mapping scenario names to loss CSV file paths
        Example: {'ida_1971': '/path/to/losses/ida_1971/Losses.csv', ...}

    Raises:
    -------
    FileNotFoundError
        If damage function file is not found

    Processing Steps:
    -----------------
    For each scenario (1971, 2021, 2071):
    1. Load joined building data with wind speeds
    2. Merge with building inventory (wbID, terrainID)
    3. For each building:
       a. Look up damage functions by wbID and terrainID
       b. Building damage function (DamLossDescID=5)
       c. Contents damage function (DamLossDescID=6)
       d. Interpolate loss ratio from wind speed
       e. Calculate dollar losses:
          - building_loss = loss_ratio × building_value
          - contents_loss = loss_ratio × contents_value
    4. Save individual building losses to CSV

    Output Format:
    --------------
    Loss CSV contains:
    - fd_id : Foundation ID (building identifier)
    - countyFIPS : County FIPS code
    - wbID : Wind building type ID
    - terrainID : Terrain classification ID
    - Wind_Speed : Gust wind speed (mph)
    - Building_Loss : Building structural loss ($)
    - Contents_Loss : Contents loss ($)

    Notes:
    ------
    - Loss ratios are interpolated linearly from Hazus damage curves
    - Wind speeds range typically from 50-250 mph in damage functions
    - Zero wind speeds result in zero losses

    Example:
    --------
    >>> loss_files = calculate_building_losses(
    ...     building_inventory=buildings_df,
    ...     joined_data_paths={'ida_2021': './output/joined/ida_2021.csv'},
    ...     hazus_dir='./data/hazus',
    ...     output_dir='./output/results'
    ... )
    """

    logger.info("="*70)
    logger.info("STEP 3B: Individual Building Loss Calculation")
    logger.info("="*70)

    # Load Hazus damage functions
    damage_func_file = os.path.join(hazus_dir, config.HAZUS_FILES['damage_functions'])
    if not os.path.exists(damage_func_file):
        raise FileNotFoundError(f"Damage function file not found: {damage_func_file}")

    logger.info(f"Loading Hazus damage functions: {damage_func_file}")
    huDamLossFunc = pd.read_csv(damage_func_file)
    logger.info(f"  ✓ Loaded damage functions")

    damLossDescID = [config.BUILDING_DAMAGE_ID, config.CONTENTS_DAMAGE_ID]

    loss_files = {}

    for scenario, joined_csv in joined_data_paths.items():
        logger.info(f"\nCalculating losses for scenario: {scenario}")

        # Create scenario output directory
        scenario_output_dir = os.path.join(output_dir, scenario)
        os.makedirs(scenario_output_dir, exist_ok=True)

        output_csv = os.path.join(scenario_output_dir, config.BUILDING_LOSSES_PATTERN)

        # Skip if already exists
        if os.path.exists(output_csv) and not force_rerun:
            logger.info(f"  Output already exists: {output_csv}")
            logger.info(f"  Skipping calculation (use --force-rerun to recalculate)")
            loss_files[scenario] = output_csv
            continue

        try:
            # Load joined data
            logger.info(f"  Loading joined data...")
            nsi_wrf = pd.read_csv(joined_csv)
            logger.info(f"    ✓ Loaded {len(nsi_wrf):,} building records")

            losses = []
            buildings_processed = 0

            logger.info(f"  Processing building losses...")

            for id in range(0, len(building_inventory)):
                row = building_inventory.iloc[id]
                row1 = row.dropna()
                fdid = row1.iloc[1]
                cbfip = row1.iloc[3]

                wbID = int(row1.iloc[-2])
                terrain_ID = int(row1.iloc[-1])

                # Get wind speed for this building
                wind_df = nsi_wrf.loc[nsi_wrf['fd_id'] == fdid]
                if len(wind_df) == 0:
                    continue

                wind_speed = wind_df['Gust_Wind_Speed'].iloc[0]

                # Look up damage functions
                bldgLossFunc = huDamLossFunc.loc[
                    (huDamLossFunc['wbID']==wbID) &
                    (huDamLossFunc['TERRAINID']==terrain_ID) &
                    (huDamLossFunc['DamLossDescID']==damLossDescID[0])
                ]
                contLossFunc = huDamLossFunc.loc[
                    (huDamLossFunc['wbID']==wbID) &
                    (huDamLossFunc['TERRAINID']==terrain_ID) &
                    (huDamLossFunc['DamLossDescID']==damLossDescID[1])
                ]

                if len(bldgLossFunc) == 0 or len(contLossFunc) == 0:
                    continue

                bldgLossFunc = bldgLossFunc.drop(['wbID','TERRAINID','DamLossDescID'], axis=1)
                contLossFunc = contLossFunc.drop(['wbID','TERRAINID','DamLossDescID'], axis=1)

                val_struct = row1.iloc[12]
                val_cont = row1.iloc[13]
                values_str = bldgLossFunc.values.flatten().tolist()
                values_cont = contLossFunc.values.flatten().tolist()
                wind_speeds = [int(i[2:]) for i in bldgLossFunc.columns]

                # Interpolate loss ratios
                building_loss = np.interp(wind_speed, wind_speeds, values_str) * val_struct
                contents_loss = np.interp(wind_speed, wind_speeds, values_cont) * val_cont

                losses.append([fdid, cbfip, wbID, terrain_ID, wind_speed,
                              building_loss, contents_loss])

                buildings_processed += 1

                if buildings_processed % 10000 == 0:
                    logger.info(f"    Processed {buildings_processed:,} buildings...")

            logger.info(f"    ✓ Processed {buildings_processed:,} buildings total")

            # Create losses DataFrame
            wind_losses = pd.DataFrame(losses)
            wind_losses.columns = ['fd_id', 'countyFIPS', 'wbID', 'terrainID',
                                   'Wind_Speed', 'Building_Loss', 'Contents_Loss']

            # Log statistics
            logger.info(f"  Loss statistics:")
            logger.info(f"    Total building loss: ${wind_losses['Building_Loss'].sum():,.2f}")
            logger.info(f"    Total contents loss: ${wind_losses['Contents_Loss'].sum():,.2f}")
            logger.info(f"    Total loss: ${(wind_losses['Building_Loss'].sum() + wind_losses['Contents_Loss'].sum()):,.2f}")

            # Save to CSV
            logger.info(f"  Saving losses: {output_csv}")
            wind_losses.to_csv(output_csv, index=False)
            logger.info(f"  ✓ Successfully calculated losses for {scenario}")

            loss_files[scenario] = output_csv

        except Exception as e:
            logger.error(f"  ✗ Error calculating losses for {scenario}: {str(e)}")
            raise

    logger.info(f"\n{'='*70}")
    logger.info(f"Step 3B Complete: Individual Building Losses")
    logger.info(f"{'='*70}\n")

    return loss_files


def aggregate_county_losses(loss_data_paths, output_dir, force_rerun=False):
    """
    Aggregate individual building losses to county level and create summary table.

    This function sums individual building and contents losses by county FIPS code
    and creates a summary table comparing losses across climate scenarios.

    Parameters:
    -----------
    loss_data_paths : dict
        Dictionary mapping scenario names to loss CSV file paths
        Example: {'ida_1971': '/path/to/losses/ida_1971/Losses.csv', ...}
    output_dir : str
        Directory for final aggregated results
    force_rerun : bool, optional
        If True, reaggregate even if output exists. Default is False.

    Returns:
    --------
    str
        Path to TotalLoss.csv file

    Raises:
    -------
    FileNotFoundError
        If loss CSV files are not found

    Processing Steps:
    -----------------
    1. For each scenario:
       a. Load individual building losses
       b. Extract county FIPS (first 5 digits)
       c. Sum building and contents losses by county
       d. Calculate total loss per scenario
    2. Create summary table with columns:
       - Year : Climate scenario year
       - Building : Total building structural loss
       - Contents : Total contents loss
       - Total : Combined building + contents loss
    3. Save to TotalLoss.csv

    Output Format:
    --------------
    TotalLoss.csv contains one row per scenario:
    - Year : 'ida_1971', 'ida_2021', 'ida_2071'
    - Building : Total building loss across all counties ($)
    - Contents : Total contents loss across all counties ($)
    - Total : Combined loss ($)

    Notes:
    ------
    - All dollar amounts are rounded to nearest dollar
    - County-level detail is preserved in individual loss files
    - Summary table enables easy comparison across climate scenarios

    Example:
    --------
    >>> total_loss_file = aggregate_county_losses(
    ...     loss_data_paths={'ida_2021': './output/results/ida_2021/Losses.csv'},
    ...     output_dir='./output/results'
    ... )
    >>> df = pd.read_csv(total_loss_file)
    >>> print(df)
           Year    Building    Contents       Total
    0  ida_2021  1000000000   500000000  1500000000
    """

    logger.info("="*70)
    logger.info("STEP 3C: County-Level Aggregation")
    logger.info("="*70)

    output_csv = os.path.join(output_dir, config.TOTAL_LOSS_OUTPUT)

    # Skip if already exists
    if os.path.exists(output_csv) and not force_rerun:
        logger.info(f"Output already exists: {output_csv}")
        logger.info(f"Skipping aggregation (use --force-rerun to reaggregate)")
        logger.info(f"{'='*70}\n")
        return output_csv

    total_losses = []

    for scenario, losses_csv in loss_data_paths.items():
        logger.info(f"\nAggregating scenario: {scenario}")

        if not os.path.exists(losses_csv):
            logger.error(f"  ✗ Loss file not found: {losses_csv}")
            raise FileNotFoundError(f"Loss file not found: {losses_csv}")

        # Load individual building losses
        logger.info(f"  Loading: {losses_csv}")
        df_indiv = pd.read_csv(losses_csv)
        logger.info(f"    ✓ Loaded {len(df_indiv):,} building records")

        # Extract county FIPS
        df_indiv['UcountyFIPS'] = df_indiv['countyFIPS'].astype(str).str[:5]
        cfips = [str(io) for io in df_indiv['UcountyFIPS'].unique()]
        logger.info(f"    Counties: {len(cfips)}")

        # Aggregate by county
        losses_county = []
        for cfip in cfips:
            df = df_indiv.loc[df_indiv['UcountyFIPS']==cfip].copy()
            bldg_loss = sum(df['Building_Loss'])
            cnt_loss = sum(df['Contents_Loss'])
            losses_county.append([cfip, bldg_loss, cnt_loss])

        df_county_losses = pd.DataFrame(losses_county)
        df_county_losses.columns = ['cfips', 'Building_Loss', 'Contents_Loss']

        # Calculate totals
        total_bldg = round(sum(df_county_losses['Building_Loss']), 0)
        total_cont = round(sum(df_county_losses['Contents_Loss']), 0)
        total_all = total_bldg + total_cont

        logger.info(f"  Total losses for {scenario}:")
        logger.info(f"    Building: ${total_bldg:,.0f}")
        logger.info(f"    Contents: ${total_cont:,.0f}")
        logger.info(f"    Total: ${total_all:,.0f}")

        total_losses.append([scenario, total_bldg, total_cont, total_all])

    # Create summary DataFrame
    df = pd.DataFrame(total_losses)
    df.columns = ["Year", "Building", "Contents", "Total"]

    # Save to CSV
    logger.info(f"\nSaving aggregated results: {output_csv}")
    df.to_csv(output_csv, index=False)
    logger.info(f"  ✓ Saved summary table")

    # Display final results
    logger.info(f"\nFinal Results Summary:")
    logger.info(f"{'-'*70}")
    for _, row in df.iterrows():
        logger.info(f"{row['Year']:>10} | Building: ${row['Building']:>15,.0f} | "
                   f"Contents: ${row['Contents']:>15,.0f} | "
                   f"Total: ${row['Total']:>15,.0f}")
    logger.info(f"{'-'*70}")

    logger.info(f"\n{'='*70}")
    logger.info(f"Step 3C Complete: County-Level Aggregation")
    logger.info(f"{'='*70}\n")

    return output_csv
