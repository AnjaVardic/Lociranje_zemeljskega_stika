# pozeniSimulacijo.py

import pandapower as pp
import pandapower.shortcircuit as sc
import pandas as pd

def zazeni_simulacijo(click, load_data, net):
    if not click or "points" not in click:
        return "Napaka: Ni bilo izbrane linije."

    #line_id = click["points"][0]["text"]  # or "customdata", depending on your map
    point = click["points"][0]
    line_id = point.get("text") or point.get("customdata") or f"{point['x']},{point['y']}"


    try:
        line_idx = net.line[net.line.name == str(line_id)].index[0]
    except IndexError:
        return f"Napaka: Linija {line_id} ni najdena v pandapower modelu."

    print(f"→ Izvajam simulacijo zemeljskega stika na liniji: {line_id}")

    # Step 1: Set short-circuit parameters (e.g., max Ika)
    net["line"].loc[line_idx, "std_type"] = "NAYY 4x50 SE"  # or your correct type

    # Step 2: Choose bus near the fault (assume from_line bus)
    fault_bus = net.line.from_bus[line_idx]

    # Step 3: Run short-circuit simulation
    sc.calc_sc(net, fault_bus, case='1ph', fault_impedance=0.0)

    # Step 4: Read results
    ika = net.res_bus_3ph.ikss_ka[fault_bus] if fault_bus in net.res_bus_3ph.index else None

    return f"Simulacija zaključena. Kratkostični tok: {ika:.2f} kA na busu {fault_bus}" if ika else "Napaka pri simulaciji."
