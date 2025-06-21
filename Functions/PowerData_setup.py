# import pandas as pd
# import plotly.graph_objects as go
# import pandapower as pp  # make sure you import pandapower if not already

# def interactive_power_viewer(csv_path, points_gdf, net, node_id_map):
#     df = pd.read_csv(csv_path, sep=";", encoding="utf-8", decimal=".")
#     df["Time"] = pd.to_datetime(df["Time"])
#     df["p_mw"] = df["Pp"] - df["Pm"]
#     df["q_mvar"] = df["Qp"] - df["Qm"]

#     # Fill missing values with 0
#     df["p_mw"] = df["p_mw"].fillna(0)
#     df["q_mvar"] = df["q_mvar"].fillna(0)

#     # Extract geometry coordinates indexed by ST_MM
#     coords = points_gdf.set_index("ST_MM").geometry

#     df["x"] = df["mp_id"].map(lambda mp: coords[mp].x if mp in coords else None)
#     df["y"] = df["mp_id"].map(lambda mp: coords[mp].y if mp in coords else None)

#     # Get last data per mp_id
#     latest_df = df.sort_values("Time").groupby("mp_id").last().reset_index()

#     # Include ALL metering points, even missing in df
#     all_mp_ids = points_gdf["ST_MM"].astype(str).tolist()
#     load_data = {}

#     for mp_id in all_mp_ids:
#         mp_id_str = str(mp_id)
#         if mp_id_str in latest_df["mp_id"].astype(str).values:
#             row = latest_df[latest_df["mp_id"].astype(str) == mp_id_str].iloc[0]
#             load_data[mp_id_str] = {
#                 "p_mw": row["p_mw"],
#                 "q_mvar": row["q_mvar"],
#                 "x": row["x"],
#                 "y": row["y"]
#             }
#         else:
#             geometry = coords.get(mp_id)
#             load_data[mp_id_str] = {
#                 "p_mw": 0.0,
#                 "q_mvar": 0.0,
#                 "x": geometry.x if geometry else None,
#                 "y": geometry.y if geometry else None
#             }

#     # ----------------------- Create Loads with initial zero values
#     points_gdf["NODE_clean"] = points_gdf["OBJ_ID"].astype(str).str.strip()
#     mpid_to_load_idx = {}

#     for i, row in points_gdf.iterrows():
#         mp_id = str(row["ST_MM"]).strip()
#         node_id = row["NODE_clean"]
#         if node_id not in node_id_map:
#             print(f"Skipping MP {mp_id}: node {node_id} not found")
#             continue
#         bus = node_id_map[node_id]
        
#         # Create load with zero initial values
#         load_idx = pp.create_load(net, bus=bus, p_mw=0.0, q_mvar=0.0, name=f"Load {mp_id}")
        
#         # Store mapping for later updates
#         mpid_to_load_idx[mp_id] = load_idx

#     # ----------------------- Update Loads with actual measurement data
#     for mp_id, load_params in load_data.items():
#         load_idx = mpid_to_load_idx.get(str(mp_id))
#         if load_idx is None:
#             print(f"No load created for MP ID {mp_id}, skipping update.")
#             continue
#         net.load.at[load_idx, "p_mw"] = load_params.get("p_mw", 0.0)
#         net.load.at[load_idx, "q_mvar"] = load_params.get("q_mvar", 0.0)

#     print("Loads updated with measurement data.")

#     # Plotly helper function for graph
#     def get_timeseries_figure(mp_id):
#         subset = df[df["mp_id"].astype(str) == str(mp_id)]
#         if subset.empty:
#             fig = go.Figure()
#             fig.add_annotation(text=f"Ni podatkov za mp_id: {mp_id}", showarrow=False)
#             return fig

#         fig = go.Figure()
#         fig.add_trace(go.Scatter(x=subset["Time"], y=subset["p_mw"], name="P (MW)"))
#         fig.add_trace(go.Scatter(x=subset["Time"], y=subset["q_mvar"], name="Q (MVAr)"))
#         fig.update_layout(
#             title=f"Časovni potek moči za mp_id: {mp_id}",
#             xaxis_title="Čas",
#             yaxis_title="Moč",
#             legend_title="Legenda"
#         )
#         return fig

#     return load_data, get_timeseries_figure, net


#------------------------------------------------------------------
#-----------working version VERSION 4------------------------------
#------------------------------------------------------------------

import pandas as pd
import plotly.graph_objects as go

def interactive_power_viewer(csv_path, points_gdf):
    df = pd.read_csv(csv_path, sep=";", encoding="utf-8", decimal=".")
    df["Time"] = pd.to_datetime(df["Time"])
    df["p_mw"] = df["Pp"] - df["Pm"]
    df["q_mvar"] = df["Qp"] - df["Qm"]

    # Fill missing values with 0
    df["p_mw"] = df["p_mw"].fillna(0)
    df["q_mvar"] = df["q_mvar"].fillna(0)

    # Extract geometry coordinates
    coords = points_gdf.set_index("ST_MM").geometry
    df["x"] = df["mp_id"].map(lambda mp: coords[mp].x if mp in coords else None)
    df["y"] = df["mp_id"].map(lambda mp: coords[mp].y if mp in coords else None)

    # Get last data per mp_id
    latest_df = df.sort_values("Time").groupby("mp_id").last().reset_index()

    # Now include ALL metering points from points_gdf, even those missing in df
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
            # Missing in CSV → Fill default values
            geometry = coords.get(mp_id)
            load_data[mp_id_str] = {
                "p_mw": 0.0,
                "q_mvar": 0.0,
                "x": geometry.x if geometry else None,
                "y": geometry.y if geometry else None
            }

    # Plotly helper function for graph
    def get_timeseries_figure(mp_id):
        subset = df[df["mp_id"].astype(str) == str(mp_id)]
        if subset.empty:
            fig = go.Figure()
            fig.add_annotation(text=f"Ni podatkov za mp_id: {mp_id}", showarrow=False)
            return fig

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=subset["Time"], y=subset["p_mw"], name="P (MW)"))
        fig.add_trace(go.Scatter(x=subset["Time"], y=subset["q_mvar"], name="Q (MVAr)"))
        fig.update_layout(
            title=f"Časovni potek moči za mp_id: {mp_id}",
            xaxis_title="Čas",
            yaxis_title="Moč",
            legend_title="Legenda"
        )
        return fig

    return load_data, get_timeseries_figure


#------------------------------------------------------------------
#-----------working version VERSION 3------------------------------
#------------------------------------------------------------------

# import pandas as pd
# import plotly.graph_objects as go

# def interactive_power_viewer(csv_path, points_gdf):
#     df = pd.read_csv(csv_path, sep=";", encoding="utf-8", decimal=".")
#     df["Time"] = pd.to_datetime(df["Time"])
#     df["p_mw"] = df["Pp"] - df["Pm"]
#     df["q_mvar"] = df["Qp"] - df["Qm"]

#     #-----TO DO: fill missing data so it insures the simulation for pandapower works


#     coords = points_gdf.set_index("ST_MM").geometry
#     df["x"] = df["mp_id"].map(lambda mp: coords[mp].x if mp in coords else None)
#     df["y"] = df["mp_id"].map(lambda mp: coords[mp].y if mp in coords else None)

#     # This dictionary is used elsewhere in your app logic
#     load_data = {
#         str(row["mp_id"]): {
#             "p_mw": row["p_mw"],
#             "q_mvar": row["q_mvar"],
#             "x": row["x"],
#             "y": row["y"]
#         }
#         for _, row in df.sort_values("Time").groupby("mp_id").last().reset_index().iterrows()
#     }

#     # Inner function: build figure from mp_id
#     def get_timeseries_figure(mp_id):
#         subset = df[df["mp_id"].astype(str) == str(mp_id)]
#         if subset.empty:
#             fig = go.Figure()
#             fig.add_annotation(text=f"Ni podatkov za mp_id: {mp_id}", showarrow=False)
#             return fig

#         fig = go.Figure()
#         fig.add_trace(go.Scatter(x=subset["Time"], y=subset["p_mw"], name="P (MW)"))
#         fig.add_trace(go.Scatter(x=subset["Time"], y=subset["q_mvar"], name="Q (MVAr)"))
#         fig.update_layout(
#             title=f"Časovni potek moči za mp_id: {mp_id}",
#             xaxis_title="Čas",
#             yaxis_title="Moč",
#             legend_title="Legenda"
#         )
#         return fig

#     return load_data, get_timeseries_figure

#------------------------------------------------------------------
#-----------working version VERSION 2------------------------------
#------------------------------------------------------------------

# import pandas as pd
# import plotly.graph_objects as go
# from dash import dcc, html, Input, Output

# def interactive_power_viewer(app, fig, csv_path, points_gdf):
#     df = pd.read_csv(csv_path, sep=";", encoding="utf-8", decimal=".")
#     df["Time"] = pd.to_datetime(df["Time"])
#     df["p_mw"] = df["Pp"] - df["Pm"]
#     df["q_mvar"] = df["Qp"] - df["Qm"]

#     latest = df.sort_values("Time").groupby("mp_id").last().reset_index()

#     coords = points_gdf.set_index("ST_MM").geometry
#     latest["x"] = latest["mp_id"].map(lambda mp: coords[mp].x if mp in coords else None)
#     latest["y"] = latest["mp_id"].map(lambda mp: coords[mp].y if mp in coords else None)

#     app.layout = html.Div([
#         html.H2("Omrežje in merilne točke"),
#         dcc.Graph(id="main-map", figure=fig),
#         html.Div(id="graph-output")
#     ])

#     @app.callback(
#         Output("graph-output", "children"),
#         Input("main-map", "clickData")
#     )
#     def show_timeseries(clickData):
#         if clickData is None:
#             return html.Div("Kliknite na merilno točko za prikaz podatkov.")
#         clicked_id = clickData["points"][0]["text"]
#         subset = df[df["mp_id"].astype(str) == str(clicked_id)]

#         if subset.empty:
#             return html.Div(f"Ni podatkov za mp_id: {clicked_id}")

#         ts_fig = go.Figure()
#         ts_fig.add_trace(go.Scatter(x=subset["Time"], y=subset["p_mw"], name="P (MW)"))
#         ts_fig.add_trace(go.Scatter(x=subset["Time"], y=subset["q_mvar"], name="Q (MVAr)"))
#         ts_fig.update_layout(
#             title=f"Časovni potek moči za mp_id: {clicked_id}",
#             xaxis_title="Čas",
#             yaxis_title="Moč",
#             legend_title="Legenda"
#         )
#         return dcc.Graph(figure=ts_fig)

#     load_data = {
#         str(row["mp_id"]): {
#             "p_mw": row["p_mw"],
#             "q_mvar": row["q_mvar"],
#             "x": row["x"],
#             "y": row["y"]
#         }
#         for _, row in latest.iterrows()
#     }

#     return load_data



#------------------------------------------------------------------
#-----------working version VERSION 1------------------------------
#------------------------------------------------------------------

# import pandas as pd
# import plotly.graph_objects as go
# from dash import Dash, dcc, html, Input, Output
# import numpy as np

# def interactive_power_viewer(csv_path: str):
#     # Load metering data
#     df = pd.read_csv(csv_path, sep=";", encoding="utf-8", decimal=".")

#     # Clean & process data
#     df["Time"] = pd.to_datetime(df["Time"])
#     df["p_mw"] = df["Pp"] - df["Pm"]
#     df["q_mvar"] = df["Qp"] - df["Qm"]

#     # Get latest P, Q per mp_id
#     latest = df.sort_values("Time").groupby("mp_id").last().reset_index()
    
#     # If x, y not provided, assign fake coordinates in grid
#     if "x" not in df.columns or "y" not in df.columns:
#         mp_ids = latest["mp_id"].unique()
#         n = len(mp_ids)
#         latest["x"] = np.linspace(0, 10, n)
#         latest["y"] = np.linspace(0, 10, n)

#     # Create main Plotly figure
#     fig = go.Figure()
#     fig.add_trace(go.Scatter(
#         x=latest["x"], y=latest["y"],
#         mode="markers+text",
#         marker=dict(size=10, color="blue", symbol="square"),
#         text=latest["mp_id"],
#         name="Metering Points",
#         hovertemplate="mp_id: %{text}<br>X: %{x}<br>Y: %{y}<extra></extra>"
#     ))

#     fig.update_layout(
#         title="Metering Points - Click to View Time Series",
#         xaxis_title="X",
#         yaxis_title="Y"
#     )

#     # Create Dash app
#     app = Dash(__name__)
#     app.layout = html.Div([
#         html.H2("Metering Point Dashboard"),
#         dcc.Graph(id="main-map", figure=fig),
#         html.Div(id="graph-output")
#     ])

#     # Callback for time series plot
#     @app.callback(
#         Output("graph-output", "children"),
#         Input("main-map", "clickData")
#     )
#     def show_timeseries(clickData):
#         if clickData is None:
#             return html.Div("Click on a metering point to view its power graph.")
        
#         mp_id = clickData["points"][0]["text"]
#         subset = df[df["mp_id"] == mp_id]

#         ts_fig = go.Figure()
#         ts_fig.add_trace(go.Scatter(x=subset["Time"], y=subset["p_mw"], name="P (MW)"))
#         ts_fig.add_trace(go.Scatter(x=subset["Time"], y=subset["q_mvar"], name="Q (MVAr)"))
#         ts_fig.update_layout(
#             title=f"Power Time Series for Metering Point: {mp_id}",
#             xaxis_title="Time",
#             yaxis_title="Power",
#             legend_title="Legend"
#         )
#         return dcc.Graph(figure=ts_fig)

#     # Prepare data for pandapower use
#     load_data = {
#         row["mp_id"]: {
#             "p_mw": row["p_mw"],
#             "q_mvar": row["q_mvar"],
#             "x": row["x"],
#             "y": row["y"]
#         }
#         for _, row in latest.iterrows()
#     }

#     # Launch app
#     app.run(debug=True)

#     return load_data
