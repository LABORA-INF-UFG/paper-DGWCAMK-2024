from simulation.plotter import Plotter

if __name__ == "__main__":
    plotter = Plotter(None)
    #trials = [7, 18, 20, 27, 29, 30, 36, 37, 46, 50]
    #trials = range(1, 51)
    trials = [47]
    SE_multipliers = {
        1: 3.0,
        2: 3.0,
        3: 3.0,
        4: 3.0,
        5: 3.0,
        6: 3.0,
        7: 3.0,
        8: 2.0,
        9: 2.0,
        10: 2.0,
    }
    for i in trials:
        plotter.plot_SE_files(i, SE_multipliers, density=20)