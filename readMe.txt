1. Activate your virtual environment

2. The network will be configured by using pandaPower, but the simulation will take place using an open source programm openDSS-G, which is used for simulations on distribution network.
    The following source free programm is used for transient simulations, while pandaPower is used for static simulations. 
    Because the programm simulates faults and PMU devices (3 phases, transient, 20 ms) the transient simulations are a better choice.
    DOWNLOAD openDSS-G and not openDSS. The simulation will run multiple times, and the openDSS-G is a GPU accelerated version.

3. Fo C++ in visual studio code install a C++ extension. You also need to install a compiler for C++

4. Run in terminal to install all the libraries-----> pip install -r requirements.txt 

5. Step-by-step instructions
    5.1 Interactive network plot
    5.2 Add the metering data for power to the points
    5.3 ---dodaj----
