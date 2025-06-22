import geopandas as gpd
import plotly.graph_objects as go
import dash
from dash import dcc, html
import os
import pandapower as pp
from shapely.geometry import Point
import pandas as pd

clickable_el = []

def add_click(item):
    global clickable_el
    clickable_el.append(item)

def get_clicks():
    global clickable_el
    return clickable_el

def clear_clicks():
    global clickable_el
    clickable_el = []

def run_interactive_map(folder_path):
    clear_clicks()

    # Load shapefiles only (avoid .dbf)
    lines_gdf = gpd.read_file(os.path.join(folder_path, "BRANCH.shp"))
    nodes_gdf = gpd.read_file(os.path.join(folder_path, "NODES.shp"))
    points_gdf = gpd.read_file(os.path.join(folder_path, "MM.shp"))
    TR_gdf = gpd.read_file(os.path.join(folder_path, "TR.shp"))
    RTP_gdf = gpd.read_file(os.path.join(folder_path, "RTP.shp"))

    # Print all columns of lines_gdf
    #with pd.option_context('display.max_columns', None):
        #print(lines_gdf.head())
        #print(TR_gdf.head())
        #print(RTP_gdf.head())
        #print(points_gdf.head())

    print("lines :",lines_gdf.shape)
    print("nodes :",nodes_gdf.shape)
    print("points :",points_gdf.shape)
    print("TR :",TR_gdf.shape)
    print("RTP :",RTP_gdf.shape)

    fig = go.Figure()

    # Draw lines
    for _, row in lines_gdf.iterrows():
        if row.geometry.geom_type == "LineString":
            x_coords, y_coords = zip(*[(pt[0], pt[1]) for pt in row.geometry.coords])
            fig.add_trace(go.Scatter(
                x=x_coords, y=y_coords,
                mode="lines",
                line=dict(color="blue", width=2),
                name="Električne linije",
                showlegend=False
            ))

    # Draw nodes
    fig.add_trace(go.Scatter(
        x=nodes_gdf.geometry.apply(lambda geom: geom.x if geom.geom_type == 'Point' else None),
        y=nodes_gdf.geometry.apply(lambda geom: geom.y if geom.geom_type == 'Point' else None),
        mode="markers",
        marker=dict(color="red", size=4),
        name="Vozlišča"
    ))
    for i in nodes_gdf.index:
        add_click({"type": "node", "id": i})

    # Split odjem/proizvodnja
    odjem_mask = points_gdf["TIP_MM"] == "Odjem elektricne energije"
    fig.add_trace(go.Scatter(
        x=points_gdf[odjem_mask].geometry.apply(lambda geom: geom.x if geom.geom_type == 'Point' else None),
        y=points_gdf[odjem_mask].geometry.apply(lambda geom: geom.y if geom.geom_type == 'Point' else None),
        mode="markers+text",
        marker=dict(color="blue", size=7, symbol="square"),
        name="Porabnik odjem",
        text=points_gdf[odjem_mask]["ST_MM"],
        textposition="top center",
        textfont=dict(size=5)
    ))
    for i in points_gdf[odjem_mask].index:
        add_click({"type": "odjem", "mp_id": points_gdf.loc[i, "ST_MM"]})

    proizvodnja_mask = ~odjem_mask
    fig.add_trace(go.Scatter(
        x=points_gdf[proizvodnja_mask].geometry.apply(lambda geom: geom.x if geom.geom_type == 'Point' else None),
        y=points_gdf[proizvodnja_mask].geometry.apply(lambda geom: geom.y if geom.geom_type == 'Point' else None),
        mode="markers+text",
        marker=dict(color="green", size=7, symbol="triangle-up"),
        name="Porabnik proizvodnja",
        text=points_gdf[proizvodnja_mask]["ST_MM"],
        textposition="top center",
        textfont=dict(size=5)
    ))
    for i in points_gdf[proizvodnja_mask].index:
        add_click({"type": "proizvodnja", "mp_id": points_gdf.loc[i, "ST_MM"]})

    # TR and RTP
    fig.add_trace(go.Scatter(
        x=TR_gdf.geometry.apply(lambda geom: geom.x if geom.geom_type == 'Point' else None),
        y=TR_gdf.geometry.apply(lambda geom: geom.y if geom.geom_type == 'Point' else None),
        mode="markers+text",
        marker=dict(color="darkblue", size=10),
        name="TP",
        text=TR_gdf["naziv_rtp"],
        textposition="top center"
    ))
    for i in TR_gdf.index:
        add_click({"type": "TP", "id": i})

    fig.add_trace(go.Scatter(
        x=RTP_gdf.geometry.apply(lambda geom: geom.x if geom.geom_type == 'Point' else None),
        y=RTP_gdf.geometry.apply(lambda geom: geom.y if geom.geom_type == 'Point' else None),
        mode="markers+text",
        marker=dict(color="purple", size=10),
        name="RTP",
        text=RTP_gdf["NAZIV"],
        textposition="top center"
    ))
    for i in RTP_gdf.index:
        add_click({"type": "RTP", "id": i})

    fig.update_layout(
        title="Geografski prikaz RTP Žiri omrežja",
        xaxis_title="Longitude",
        yaxis_title="Latitude",
        showlegend=True
    )

    # tells Dash: Some components may appear later dynamically. Don’t error if you don’t see them right now.
    app = dash.Dash(__name__, suppress_callback_exceptions=True)
    app.layout = html.Div([
        html.H1("Interaktivni prikaz omrežja"),
        dcc.Graph(id="main-map", figure=fig),
    ])

    # -------------------------------------------------
    # Add pandapower network generation here
    # -------------------------------------------------

    net = pp.create_empty_network()
    # It contains:
    # - net.bus: the buses (nodes) in your network
    # - net.line: transmission lines
    # - net.load: loads (like from points_gdf)
    # - net.trafo: transformers
    # - net.ext_grid: external grid (slack bus)
    # - and many other tables

    # Create buses for all nodes
    # Ensure consistent ID mapping between shapefiles
    # Clean up node IDs
    #------------------------NODES
    nodes_gdf["CIMID_clean"] = nodes_gdf["CIMID"].astype(str).str.strip()
    node_id_map = {}

    for i, row in nodes_gdf.iterrows():
        node_id = row["CIMID_clean"]
        bus = pp.create_bus(net, vn_kv=20.0, name=f"Bus {node_id}")
        node_id_map[node_id] = bus

    #--------------LINES Clean node identifiers
    lines_gdf["NODE1_clean"] = lines_gdf["NODE1"].astype(str).str.strip()
    lines_gdf["NODE2_clean"] = lines_gdf["NODE2"].astype(str).str.strip()

    for i, row in lines_gdf.iterrows():
        from_id = row["NODE1_clean"]
        to_id = row["NODE2_clean"]

        if from_id not in node_id_map or to_id not in node_id_map:
            print(f"Line {i} skipped: node not in map ({from_id}, {to_id})")
            continue

        from_bus = node_id_map[from_id]
        to_bus = node_id_map[to_id]

        try:
            # Use real values with conversion
            length_km = float(row["LENGHT"]) / 1000  # meters to km
            r_ohm_per_km = float(row["R"])
            x_ohm_per_km = float(row["X"])
            c_nf_per_km = float(row["BC"]) if not pd.isna(row["BC"]) else 0.0
            max_i_ka = float(row["I_MAX"]) / 1000  # A to kA

            pp.create_line_from_parameters(
                net,
                from_bus=from_bus,
                to_bus=to_bus,
                length_km=length_km,
                r_ohm_per_km=r_ohm_per_km,
                x_ohm_per_km=x_ohm_per_km,
                c_nf_per_km=c_nf_per_km,
                max_i_ka=max_i_ka,
                name=f"Line {i}"
            )
        except Exception as e:
            print(f"Skipping line {i} due to error: {e}")

    # ----------------------- Create Loads -----------------------

    # Clean up node identifiers in points_gdf
    points_gdf["NODE_clean"] = points_gdf["NODE1"].astype(str).str.strip()
    points_gdf["ST_MM_clean"] = points_gdf["ST_MM"].astype(str).str.strip()

    # Initialize dictionary to track mp_id -> load index
    mpid_to_load_idx = {}

    # Loop through metering points and create loads
    for i, row in points_gdf.iterrows():
        # mp_id = row["ST_MM_clean"]
        # node_id = row["NODE_clean"]
        mp_id = str(row.get("ST_MM", "")).strip()
        node_id = str(row.get("NODE_clean", "")).strip()

        # Skip if node is not mapped to a bus
        if node_id not in node_id_map:
            print(f"⚠️ Skipping metering point {mp_id}: node '{node_id}' not found in node_id_map.")
            continue

        bus = node_id_map[node_id]

        if bus not in net.bus.index:
            print(f"❌ Bus index {bus} for node {node_id} is not in net.bus!")
            continue

        try:
            # Create load with initial zero values
            load_idx = pp.create_load(
                net,
                bus=bus,
                p_mw=0.0,
                q_mvar=0.0,
                name=f"Load {mp_id}"
            )
            mpid_to_load_idx[mp_id] = load_idx
            #print(f"✅ Load created for MP {mp_id} on bus {bus}")
        except Exception as e:
            print(f"❌ Failed to create load for MP {mp_id} on bus {bus}: {e}")


    #-------------------- External Grid (nearest node to each RTP)
    # Initialize the RTP bus map
    rtp_bus_map = {}

    # Normalize RTP column names
    # So the column name is likely "OBJECTID", but it might be uppercase, have extra spaces, or be renamed during import.
    # Step 1: Uppercase all columns (including geometry)
    RTP_gdf.columns = RTP_gdf.columns.str.strip().str.upper()

    # Step 2: Set geometry explicitly to the uppercased geometry column
    RTP_gdf = RTP_gdf.set_geometry("GEOMETRY")

    # Step 3: Use row["GEOMETRY"] to access geometry in your loop
    for i, row in RTP_gdf.iterrows():
        rtp_point = row["GEOMETRY"]  # Access geometry via column name since attribute .geometry won't work
        nearest_idx = nodes_gdf.geometry.distance(rtp_point).idxmin()
        node_id = nodes_gdf.loc[nearest_idx, "CIMID_clean"]

        if node_id not in node_id_map:
            print(f"RTP {i}: nearest node {node_id} not mapped")
            continue

        bus = node_id_map[node_id]
        pp.create_ext_grid(net, bus=bus, vm_pu=1.0, name=f"RTP {row['NAZIV']}")

        rtp_id = str(row["OBJECTID"]).strip()
        rtp_bus_map[rtp_id] = bus


    #---------------------------- Transformers TR
    # Normalize column names for safety
    TR_gdf.columns = TR_gdf.columns.str.strip().str.lower()

    TR_gdf["node1_clean"] = TR_gdf["node1"].astype(str).str.strip()

    for i, row in TR_gdf.iterrows():
        node_id = row["node1_clean"]
        if node_id not in node_id_map:
            print(f"Skipping TR {i}: node {node_id} not found")
            continue

        lv_bus = node_id_map[node_id]

        # Use RTP info to get the correct HV bus
        rtp_id = str(row["id_rtp"]).strip()
        if rtp_id not in rtp_bus_map:
            print(f"Skipping TR {i}: RTP ID {rtp_id} not found in RTP bus map")
            continue

        hv_bus = rtp_bus_map[rtp_id]

        try:
            # Convert strings to float values using comma as decimal
            sn_mva = float(str(row["nazivna_mo"]).replace(",", ".")) / 1e6           # MVA
            vn_hv_kv = float(str(row["u_prim"]).replace(",", ".")) / 1000            # kV
            vn_lv_kv = float(str(row["u_sek"]).replace(",", ".")) / 1000             # kV
            p_cu_kw = float(str(row["p_cu"]).replace(",", "."))                      # kW
            p_fe_kw = float(str(row["p_fe"]).replace(",", "."))                      # kW
            i0_percent = float(str(row["i_o"]).replace(",", "."))                    # %

            # Calculate vkr_percent (resistive part of impedance)
            vkr_percent = (p_cu_kw * 100) / (sn_mva * 1e3)

            # Use a typical default or inferred short-circuit impedance
            vk_percent = 6.0  # Can be adjusted per real data if available

        except Exception as e:
            print(f"Transformer {i} parse failed: {e}")
            sn_mva, vn_hv_kv, vn_lv_kv = 20.0, 110.0, 21.0
            vk_percent, vkr_percent = 6.0, 0.5
            p_fe_kw, i0_percent = 1.0, 0.1

        # Create transformer using actual or fallback values
        pp.create_transformer_from_parameters(
            net,
            hv_bus=hv_bus,
            lv_bus=lv_bus,
            sn_mva=sn_mva,
            vn_hv_kv=vn_hv_kv,
            vn_lv_kv=vn_lv_kv,
            vk_percent=vk_percent,
            vkr_percent=vkr_percent,
            pfe_kw=p_fe_kw,
            i0_percent=i0_percent,
            name=f"trafoPostaja {i}"
        )

    return app, fig, points_gdf, net, node_id_map  # <-- return values instead of calling run()


#------------------------------------------------------------------
#-----------working version VERSION 1------------------------------
#------------------------------------------------------------------

# import geopandas as gpd
# import plotly.graph_objects as go
# import dash
# from dash import dcc, html
# import os


# def run_interactive_map(folder_path):
#     path_lines_dbf = os.path.join(folder_path, "BRANCH.dbf")
#     path_nodes_dbf = os.path.join(folder_path, "NODES.dbf")
#     path_points_dbf = os.path.join(folder_path, "MM.dbf")
#     path_TR_dbf = os.path.join(folder_path, "TR.dbf")
#     path_RTP_dbf = os.path.join(folder_path, "RTP.dbf")
#     path_lines_shp = os.path.join(folder_path, "BRANCH.shp")
#     path_nodes_shp = os.path.join(folder_path, "NODES.shp")
#     path_points_shp = os.path.join(folder_path, "MM.shp")
#     path_TR_shp = os.path.join(folder_path, "TR.shp")
#     path_RTP_shp = os.path.join(folder_path, "RTP.shp")

#     lines_dbf = gpd.read_file(path_lines_dbf)
#     nodes_dbf = gpd.read_file(path_nodes_dbf)
#     points_dbf = gpd.read_file(path_points_dbf)
#     TR_dbf = gpd.read_file(path_TR_dbf)
#     RTP_dbf = gpd.read_file(path_RTP_dbf)

#     lines_gdf = gpd.read_file(path_lines_shp)
#     nodes_gdf = gpd.read_file(path_nodes_shp)
#     points_gdf = gpd.read_file(path_points_shp)
#     TR_gdf = gpd.read_file(path_TR_shp)
#     RTP_gdf = gpd.read_file(path_RTP_shp)

#     print(points_gdf)

#     fig = go.Figure()

#     for _, row in lines_gdf.iterrows():
#         if row.geometry.geom_type == "LineString":
#             x_coords, y_coords = zip(*[(point[0], point[1]) for point in row.geometry.coords])
#             fig.add_trace(go.Scatter(
#                 x=x_coords, y=y_coords,
#                 mode="lines",
#                 line=dict(color="blue", width=2),
#                 name="Električne linije" if _ == 0 else None,
#                 showlegend=(_ == 0)
#             ))

#     fig.add_trace(go.Scatter(
#         x=nodes_gdf.geometry.x,
#         y=nodes_gdf.geometry.y,
#         mode="markers",
#         marker=dict(color="red", size=4),
#         name="Vozlišča"
#     ))

#     odjem_mask = points_gdf["TIP_MM"] == "Odjem elektricne energije"
#     fig.add_trace(go.Scatter(
#         x=points_gdf[odjem_mask].geometry.apply(lambda geom: geom.x if geom.geom_type == 'Point' else None),
#         y=points_gdf[odjem_mask].geometry.apply(lambda geom: geom.y if geom.geom_type == 'Point' else None),
#         mode="markers+text",
#         marker=dict(color="blue", size=7, symbol="square"),
#         name="Porabnik odjem"
#     ))

#     proizvodnja_mask = ~odjem_mask
#     fig.add_trace(go.Scatter(
#         x=points_gdf[proizvodnja_mask].geometry.apply(lambda geom: geom.x if geom.geom_type == 'Point' else None),
#         y=points_gdf[proizvodnja_mask].geometry.apply(lambda geom: geom.y if geom.geom_type == 'Point' else None),
#         mode="markers+text",
#         marker=dict(color="green", size=7, symbol="triangle-up"),
#         name="Porabnik proizvodnja"
#     ))

#     fig.add_trace(go.Scatter(
#         x=TR_gdf.geometry.apply(lambda geom: geom.x if geom.geom_type == 'Point' else None),
#         y=TR_gdf.geometry.apply(lambda geom: geom.y if geom.geom_type == 'Point' else None),
#         mode="markers+text",
#         marker=dict(color="darkblue", size=10),
#         name="TP",
#         text=TR_gdf["naziv_rtp"],
#         textposition="top center"
#     ))

#     fig.add_trace(go.Scatter(
#         x=RTP_gdf.geometry.apply(lambda geom: geom.x if geom.geom_type == 'Point' else None),
#         y=RTP_gdf.geometry.apply(lambda geom: geom.y if geom.geom_type == 'Point' else None),
#         mode="markers+text",
#         marker=dict(color="purple", size=10),
#         name="RTP",
#         text=RTP_gdf["NAZIV"],
#         textposition="top center"
#     ))

#     fig.update_layout(
#         title="Geografski prikaz RTP Žiri omrežja",
#         xaxis_title="Longitude",
#         yaxis_title="Latitude",
#         showlegend=True
#     )

#     app = dash.Dash(__name__)
#     app.layout = html.Div([
#         html.H1("Interaktivni prikaz omrežja"),
#         dcc.Graph(id="map-graph", figure=fig),
#     ])

#     app.run(debug=True)