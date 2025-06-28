import pandas as pd
import numpy as np
import re

# Step 1: Parse MATERIAL field
def extract_material_properties(material_str):
    if pd.isna(material_str):
        return None, None, None

    material_str = material_str.upper()

    # Line type
    if "KABEL" in material_str:
        tip = "kabel"
    elif "VODNIK" in material_str or "GOLI" in material_str:
        tip = "vodnik"
    else:
        tip = "drugo"

    # Voltage level
    napetost = "SN" if "24KV" in material_str or "SN" in material_str else "NN"

    # Cross-section extraction (e.g., 150mm2)
    match = re.search(r'(\d{2,3})\s*MM2', material_str)
    presek = int(match.group(1)) if match else None

    return tip, napetost, presek

# Step 2: Capacitance calculation using physics-based formulas
def calculate_geometry_based_capacitance(row):
    tip = row.get("tip")
    A = row.get("presek_mm2")

    if A is None or A <= 0:
        return np.nan

    r = np.sqrt(A / np.pi) / 1000  # Convert mm² to radius in meters
    ε0 = 8.854e-12  # Vacuum permittivity [F/m]

    if tip == "vodnik":
        h = 10  # Average pole height [m]
        if 2 * h <= r:
            return np.nan
        C_per_m = (2 * np.pi * ε0) / np.log(2 * h / r)

    elif tip == "kabel":
        εr = 3.5  # Relative permittivity for XLPE
        D = 3 * r  # Assume insulation outer diameter is 3×r
        if D <= r:
            return np.nan
        C_per_m = (2 * np.pi * ε0 * εr) / np.log(D / r)

    else:
        return np.nan  # Unknown line type

    return C_per_m * 1e12  # Convert to [nF/km]

# Step 3: Main function to apply everything and export
def doloci_dozemne_kapacitivnosti(lines_gdf, export_excel=True):
    """
    Calculate line capacitances and optionally export lookup table to Excel.
    Adds BC to lines_gdf for use in pandapower.
    """
    # Parse MATERIAL info
    lines_gdf[["tip", "napetost", "presek_mm2"]] = lines_gdf["MATERIAL"].apply(
        lambda x: pd.Series(extract_material_properties(x))
    )

    # if export_excel:
    #     lines_gdf.to_excel("lines_gdf_capacitances.xlsx", index=False)

    # Calculate BC (nF/km)
    lines_gdf["BC"] = lines_gdf.apply(calculate_geometry_based_capacitance, axis=1)

    # Build a lookup table of unique values (optional for inspection)
    filtered = lines_gdf.dropna(subset=["BC", "tip", "napetost", "presek_mm2"])
    lookup_df = (
        filtered
        .groupby(["tip", "napetost", "presek_mm2"], as_index=False)
        .agg(c_nf_per_km=("BC", "mean"))
        .sort_values(by=["tip", "napetost", "presek_mm2"])
        .reset_index(drop=True)
    )

    # if export_excel:
    #     lookup_df.to_excel("capacitance_lookup.xlsx", index=False)

    return lines_gdf
