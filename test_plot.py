from simulation.plotter import Plotter

if __name__ == "__main__":
    plotter = Plotter(None)
    #trials = [7, 18, 20, 27, 29, 30, 36, 37, 46, 50]
    trials = range(1, 51)
    for i in trials:
        plotter.plot_SE_files(i, 1.0)

# Tentar o 46
# Trial 9 tirando o UE 9
# Trial 19 tirando o UE 3
# Trial 31 tirando o UE 4
# Trial 50 tirando o UE 4