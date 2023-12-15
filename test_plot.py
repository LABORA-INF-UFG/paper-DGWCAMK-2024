from simulation.plotter import Plotter

if __name__ == "__main__":
    plotter = Plotter(None)
    trials = [7, 18, 20, 27, 29, 30, 36, 37, 46, 50]
    for i in trials:
        plotter.plot_SE_files(i, 1.0)