from dash import html, dcc, Input, Output, State, callback_context
import dash
import plotly.graph_objs as go

def add_buttons_to_app(app, fig, points_gdf, get_timeseries_figure, func_add_grounding, func_add_pmu, func_run_simulation):
    app.layout = html.Div([
        html.Div([
            html.Button("DODAJ OZEMLJITEV", id="btn-add-grounding"),
            html.Button("DODAJ PMU", id="btn-add-pmu"),
            html.Button("ZAŽENI SIMULACIJO", id="btn-run-simulation"),
            html.Button("CHECK DATA", id="btn-check-data", n_clicks=0, style={'backgroundColor': 'lightgray'}),
        ], style={'display': 'flex', 'gap': '10px', 'margin-bottom': '10px'}),

        dcc.Graph(id="map-graph", figure=fig),
        dcc.Store(id="stored-click-info"),
        dcc.Store(id="check-data-enabled", data=False),
        dcc.Graph(id="data-graph")
    ])

    # Store latest click from map
    @app.callback(
        Output("stored-click-info", "data"),
        Input("map-graph", "clickData"),
        prevent_initial_call=True
    )
    def store_click_info(clickData):
        return clickData

    # Unified update of map
    @app.callback(
        Output("map-graph", "figure", allow_duplicate=True),
        Input("btn-add-grounding", "n_clicks"),
        Input("btn-add-pmu", "n_clicks"),
        Input("btn-run-simulation", "n_clicks"),
        State("stored-click-info", "data"),
        State("map-graph", "figure"),
        prevent_initial_call=True
    )
    def handle_map_updates(n_ground, n_pmu, n_sim, click_data, fig):
        ctx = callback_context
        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate

        btn_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if btn_id == "btn-add-grounding":
            return func_add_grounding(fig)
        elif btn_id == "btn-add-pmu":
            return func_add_pmu(fig)
        elif btn_id == "btn-run-simulation":
            return func_run_simulation(click_data, fig)

        return fig

    # Toggle CHECK DATA mode
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

    # Display graph when clicking a metering point (only if CHECK DATA is active)
    @app.callback(
        Output("data-graph", "figure"),
        Input("map-graph", "clickData"),
        State("check-data-enabled", "data"),
        prevent_initial_call=True
    )
    def update_data_graph(clickData, check_data_enabled):
        if not check_data_enabled or clickData is None:
            return go.Figure()  # Empty graph

        mp_id = clickData["points"][0]["text"]  # assumes `text` holds mp_id
        return get_timeseries_figure(mp_id)
