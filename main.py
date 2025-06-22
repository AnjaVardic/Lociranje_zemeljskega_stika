# klici funkcije
from Functions.IzrisOmrezja import run_interactive_map, get_clicks
from Functions.PowerData_setup import interactive_power_viewer
from Functions.add_buttons_to_app import add_buttons_to_app
from Functions.pozeniSimulacijo import zazeni_simulacijo


def dodaj_ozemljitev(): return "Dodana ozemljitev."
def dodaj_pmu(): return "Dodan PMU."
#def zazeni_simulacijo(click): return f"Simulacija zagnana na: {click}"


def main():
    folder_path = r"C:\Users\Uporabnik\Desktop\faks\magisterska\magisterska podatki\RTP Žiri"
    csv_path = r"c:\Users\Uporabnik\Desktop\faks\magisterska\magisterska podatki\meritve\Power2023_5.csv"

    #--------------------------------------------------------
    #--------Funkcija, ki izriše interaktive zemljevid-------
    #--------------------------------------------------------
    app, fig, points_gdf, net, node_id_map = run_interactive_map(folder_path)

    #-------------------------------------------------------------
    #--------Funkcija, ki veže podatke meritev na zemljevid-------
    #-------------------------------------------------------------
    load_data, get_timeseries_figure, net = interactive_power_viewer(csv_path, points_gdf, net, node_id_map)

    #print(net.trafo.head())
    print(net)

    #print("Prepared power load data:")
    # for mp_id, data in load_data.items():
    #     print(mp_id, data)

    #--------TO BE DONE--------------------------
    #--------add function dodaj_ozemljitev-------
    #--------------------------------------------


    #--------TO BE DONE--------------------------
    #--------add function dodaj_PMU--------------
    #--------------------------------------------

    #--------TO BE DONE NOW--------------------------
    #--------add function pozeniSimulacijo-------
    #--------------------------------------------
    # result = zazeni_simulacijo(click, load_data, net)
    # print(result)

    #--------call function add_buttons_to_app
    #Inject buttons into layout and setup interactivity
    #Add UI buttons + callbacks, all args passed by name
    add_buttons_to_app(
        app=app,
        fig=fig,
        points_gdf=points_gdf,
        get_timeseries_figure=get_timeseries_figure,
        func_add_grounding=dodaj_ozemljitev,
        func_add_pmu=dodaj_pmu,
        net=net,
        func_run_simulation=zazeni_simulacijo
    )

    app.run(debug=True)

if __name__ == "__main__":
    main()
