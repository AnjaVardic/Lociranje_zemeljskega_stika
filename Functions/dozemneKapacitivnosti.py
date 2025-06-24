import pandas as pd
import re

def extract_material_properties(material_str):
    if pd.isna(material_str):
        return None, None, None

    material_str = material_str.upper()

    if "KABEL" in material_str:
        tip = "kabel"
    elif "VODNIK" in material_str or "GOLI" in material_str:
        tip = "vodnik"
    else:
        tip = "drugo"

    if "24KV" in material_str or "SN" in material_str:
        napetost = "SN"
    else:
        napetost = "NN"

    match = re.search(r'(\d{2,3})\s*MM2', material_str)
    presek = int(match.group(1)) if match else None

    return tip, napetost, presek


def doloci_dozemne_kapacitivnosti(lines_gdf):
    # Extract type info
    lines_gdf[["tip", "napetost", "presek_mm2"]] = lines_gdf["MATERIAL"].apply(
        lambda x: pd.Series(extract_material_properties(x))
    )

    # Capacitance lookup table (EDIT THESE VALUES based on engineering assumptions!)
    lookup_data = [
        {"tip": "kabel", "napetost": "SN", "presek_mm2": 150, "c_nf_per_km": 240},
        {"tip": "kabel", "napetost": "SN", "presek_mm2": 95,  "c_nf_per_km": 220},
        {"tip": "vodnik", "napetost": "SN", "presek_mm2": 120, "c_nf_per_km": 20},
        # Add more rules as needed...
    ]
    lookup_df = pd.DataFrame(lookup_data)

    # Merge with original lines
    lines_gdf = lines_gdf.merge(
        lookup_df,
        how="left",
        on=["tip", "napetost", "presek_mm2"]
    )

    # Default to 0 for unmatched entries
    lines_gdf["c_nf_per_km"] = lines_gdf["c_nf_per_km"].fillna(0)

    return lines_gdf
