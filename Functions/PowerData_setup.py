import pandas as pd
import plotly.graph_objects as go
import pandapower as pp  # make sure you import pandapower if not already

def interactive_power_viewer(csv_path, points_gdf, net, node_id_map):

    # Clean node references
    points_gdf["NODE_clean"] = points_gdf["OBJ_ID"].astype(str).str.strip()
    node_id_map = {str(k).strip(): v for k, v in node_id_map.items()}

    # Read measurement CSV
    df = pd.read_csv(csv_path, sep=";", encoding="utf-8", decimal=".")
  
    df["Time"] = pd.to_datetime(df["Time"])
    df["p_mw"] = df["Pp"] - df["Pm"]
    df["q_mvar"] = df["Qp"] - df["Qm"]
    df["p_mw"] = df["p_mw"].fillna(0)
    df["q_mvar"] = df["q_mvar"].fillna(0)

    # Geometry coordinates for plotting
    coords = points_gdf.set_index("ST_MM").geometry
    df["x"] = df["mp_id"].map(lambda mp: coords[mp].x if mp in coords else None)
    df["y"] = df["mp_id"].map(lambda mp: coords[mp].y if mp in coords else None)

    # Latest values per mp_id
    latest_df = df.sort_values("Time").groupby("mp_id").last().reset_index()

    # Prepare load data dict
    all_mp_ids = points_gdf["ST_MM"].astype(str).tolist()
    load_data = {}

    for mp_id in all_mp_ids:
        mp_id_str = str(mp_id)
        if mp_id_str in latest_df["mp_id"].astype(str).values:
            row = latest_df[latest_df["mp_id"].astype(str) == mp_id_str].iloc[0]
            load_data[mp_id_str] = {
                "p_mw": row["p_mw"],
                "q_mvar": row["q_mvar"],
                "x": row["x"],
                "y": row["y"]
            }
        else:
            geometry = coords.get(mp_id)
            load_data[mp_id_str] = {
                "p_mw": 0.0,
                "q_mvar": 0.0,
                "x": geometry.x if geometry else None,
                "y": geometry.y if geometry else None
            }

    # ----------------------- Create and update loads
    mpid_to_load_idx = {}

    for i, row in points_gdf.iterrows():
        mp_id_raw = row.get("ST_MM")
        if pd.isna(mp_id_raw):
            continue

        # Normalize metering point ID to a consistent string format (e.g. "3335497")
        try:
            mp_id = str(int(float(mp_id_raw)))
        except ValueError:
            print(f"❌ Invalid MP ID format: {mp_id_raw}")
            continue

        node_id = row.get("NODE_clean", "").strip()
        if node_id not in node_id_map:
            #print(f"⚠️ Skipping MP {mp_id}: node {node_id} not found")
            continue

        bus = node_id_map[node_id]
        try:
            load_idx = pp.create_load(net, bus=bus, p_mw=0.0, q_mvar=0.0, name=f"Load {mp_id}")
            mpid_to_load_idx[mp_id] = load_idx
            print(load_idx)
        except Exception as e:
            print(f"❌ Failed to create load for MP {mp_id} on bus {bus}: {e}")
            continue

    # Update load values with actual measurements
    for raw_id, load_params in load_data.items():
        try:
            mp_id = str(int(float(raw_id)))  # Normalize again to same format
        except ValueError:
            print(f"❌ Invalid raw MP ID: {raw_id}")
            continue

        load_idx = mpid_to_load_idx.get(mp_id)
        if load_idx is None:
            #print(f"⚠️ No load created for MP {mp_id}, skipping update.")
            continue

        net.load.at[load_idx, "p_mw"] = load_params.get("p_mw", 0.0)
        net.load.at[load_idx, "q_mvar"] = load_params.get("q_mvar", 0.0)
        

    print("✅ Loads created and updated with measurement data.")

    # Plot helper
    def get_timeseries_figure(mp_id):
        subset = df[df["mp_id"].astype(str) == str(mp_id)]
        if subset.empty:
            fig = go.Figure()
            fig.add_annotation(text=f"No data for mp_id: {mp_id}", showarrow=False)
            return fig

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=subset["Time"], y=subset["p_mw"], name="P (MW)"))
        fig.add_trace(go.Scatter(x=subset["Time"], y=subset["q_mvar"], name="Q (MVAr)"))
        fig.update_layout(
            title=f"Load time series for mp_id: {mp_id}",
            xaxis_title="Time",
            yaxis_title="Power",
            legend_title="Legend"
        )
        return fig

    return load_data, get_timeseries_figure, net


