from dash import html, dcc, Input, Output, State, callback_context
import dash
import plotly.graph_objs as go
import time  # for simulating long simulation run

def add_buttons_to_app(app, fig, points_gdf, get_timeseries_figure, func_add_grounding, func_add_pmu, net, func_run_simulation):
    app.layout = html.Div([
        html.Div([
            html.Button("DODAJ OZEMLJITEV", id="btn-add-grounding"),
            html.Button("DODAJ PMU", id="btn-add-pmu"),
            html.Button("IZBERI LOKACIJO OKVARE", id="btn-fault-location", style={'backgroundColor': 'lightgray'}),
            html.Button("ZAŽENI SIMULACIJO", id="btn-run-simulation", style={'backgroundColor': 'lightgray'}),
            html.Button("REZULTATI SIMULACIJE", id="btn-simulation-results", style={'backgroundColor': 'lightgray'}),
            html.Button("CHECK DATA", id="btn-check-data", n_clicks=0, style={'backgroundColor': 'lightgray'}),
        ], style={'display': 'flex', 'gap': '10px', 'margin-bottom': '10px'}),

        dcc.Graph(id="map-graph", figure=fig),

        # Data stores
        dcc.Store(id="stored-click-info"),
        dcc.Store(id="fault-location-coords"),
        dcc.Store(id="fault-location-enabled", data=False),  # track if fault location mode ON
        dcc.Store(id="simulation-running", data=False),      # track if sim running
        dcc.Store(id="simulation-result", data=""),
        dcc.Store(id="check-data-enabled", data=False),

        dcc.Graph(id="data-graph"),
        html.Div(id="simulation-output", style={'marginTop': '10px', 'fontWeight': 'bold'})
    ])

    # Store any click on map
    @app.callback(
        Output("stored-click-info", "data"),
        Input("map-graph", "clickData"),
        prevent_initial_call=True
    )
    def store_click_info(clickData):
        return clickData

    #--------------------------------------------------------------
    #----IZBERI lokacijo okvare------------------------------------
    #--------------------------------------------------------------

    # Toggle fault location mode on/off and update button color
    @app.callback(
        Output("fault-location-enabled", "data"),
        Output("btn-fault-location", "style"),
        Input("btn-fault-location", "n_clicks"),
        State("fault-location-enabled", "data"),
        prevent_initial_call=True
    )
    def toggle_fault_location_mode(n_clicks, enabled):
        # Toggle on each click
        enabled = not enabled
        color = 'lightgreen' if enabled else 'lightgray'
        return enabled, {'backgroundColor': color}

    # Fault location selection with triangle marker only if fault location mode is ON
    @app.callback(
        Output("fault-location-coords", "data"),
        Output("map-graph", "figure"),
        Input("map-graph", "clickData"),
        State("fault-location-enabled", "data"),
        State("map-graph", "figure"),
        prevent_initial_call=True
    )
    def store_fault_location(clickData, fault_enabled, fig):
        ctx = callback_context
        if not fault_enabled:
            # If fault location mode is OFF, ignore clicks for fault location
            raise dash.exceptions.PreventUpdate

        if not clickData or "points" not in clickData:
            return dash.no_update, fig

        point = clickData["points"][0]
        fault_x, fault_y = point["x"], point["y"]

        # Remove existing fault marker
        fig["data"] = [trace for trace in fig["data"] if trace.get("name") != "Lokacija okvare"]

        # Add new triangle marker for fault location
        fig["data"].append(go.Scatter(
            x=[fault_x],
            y=[fault_y],
            mode="markers+text",
            marker=dict(symbol="triangle-up", color="red", size=14),
            text=["⚠"],
            textposition="top center",
            name="Lokacija okvare"
        ))

        return {"x": fault_x, "y": fault_y}, fig

    #--------------------------------------------------------------
    #----DODAJ ozemljitev IN PMU-----------------------------------
    #--------------------------------------------------------------

    # Map updates for grounding and PMU buttons
    @app.callback(
        Output("map-graph", "figure", allow_duplicate=True),
        Input("btn-add-grounding", "n_clicks"),
        Input("btn-add-pmu", "n_clicks"),
        State("map-graph", "figure"),
        prevent_initial_call=True
    )
    def handle_map_updates(n_ground, n_pmu, current_fig):
        ctx = callback_context
        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate

        btn_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if btn_id == "btn-add-grounding":
            fig_updated = func_add_grounding(current_fig)
            return fig_updated
        elif btn_id == "btn-add-pmu":
            fig_updated = func_add_pmu(current_fig)
            return fig_updated

        raise dash.exceptions.PreventUpdate

    #--------------------------------------------------------------
    #----s KLIKOM zaženi simulacijo--------------------------------
    #--------------------------------------------------------------

    # Run simulation on button click, only if fault location mode is ON and location selected
    @app.callback(
        Output("simulation-result", "data"),
        Output("simulation-running", "data"),
        Output("btn-run-simulation", "style"),
        Input("btn-run-simulation", "n_clicks"),
        State("fault-location-enabled", "data"),
        State("fault-location-coords", "data"),
        State("map-graph", "figure"),
        prevent_initial_call=True
    )
    def handle_run_simulation(n_clicks, fault_enabled, fault_location, fig):
        if not fault_enabled:
            # Fault location mode must be on to run simulation
            return "Napaka: Lokacija okvare ni omogočena.", False, {'backgroundColor': 'lightgray'}
        if not fault_location:
            return "Napaka: Ni bila izbrana lokacija okvare.", False, {'backgroundColor': 'lightgray'}

        # Turn simulation button red during run
        sim_running_style = {'backgroundColor': 'red'}

        # Indicate simulation started
        simulation_result = "Simulacija teče..."
        simulation_running = True

        # Trigger update for button color immediately
        # Dash callbacks are synchronous, so UI will update only after this completes
        # To simulate delay, let's run simulation here (blocking)
        # You can replace this with your actual simulation call:
        fake_click = {
            "points": [{
                "x": fault_location["x"],
                "y": fault_location["y"]
            }]
        }

        # Run the actual simulation function (make sure it's blocking)
        result_str = func_run_simulation(fake_click, fig, net)

        # After simulation finishes, update button to green
        sim_done_style = {'backgroundColor': 'lightgreen'}

        return result_str, False, sim_done_style

    #--------------------------------------------------------------
    #----PRIKAŽI rezultate simulacije------------------------------
    #--------------------------------------------------------------

    # Show simulation results on button click, update button color too
    @app.callback(
        Output("simulation-output", "children"),
        Output("btn-simulation-results", "style"),
        Input("btn-simulation-results", "n_clicks"),
        State("simulation-result", "data"),
        prevent_initial_call=True
    )
    def show_simulation_results(n_clicks, result):
        # Turn button green when results viewed
        style = {'backgroundColor': 'lightgreen'}
        return result or "Ni rezultatov za prikaz.", style

    #--------------------------------------------------------------
    #----PRIKAŽI MERITVE s klikom na točko-------------------------
    #--------------------------------------------------------------

    # Toggle CHECK DATA mode button (independent, no interference)
    @app.callback(
        Output("check-data-enabled", "data"),
        Output("btn-check-data", "style"),
        Input("btn-check-data", "n_clicks"),
        State("check-data-enabled", "data"),
        prevent_initial_call=True
    )
    def toggle_check_data(n_clicks, is_enabled):
        is_enabled = not is_enabled
        color = 'lightgreen' if is_enabled else 'lightgray'
        return is_enabled, {'backgroundColor': color}

    # Show timeseries graph when clicking a point on map, only if CHECK DATA enabled
    @app.callback(
        Output("data-graph", "figure"),
        Input("map-graph", "clickData"),
        State("check-data-enabled", "data"),
        prevent_initial_call=True
    )
    def update_data_graph(clickData, check_data_enabled):
        if not check_data_enabled or clickData is None:
            return go.Figure()  # empty figure

        point = clickData["points"][0]

        # Use 'text' or 'customdata' as mp_id
        mp_id = point.get("text") or point.get("customdata")

        if not mp_id:
            # No valid mp_id found, return empty figure
            return go.Figure()

        return get_timeseries_figure(mp_id)
