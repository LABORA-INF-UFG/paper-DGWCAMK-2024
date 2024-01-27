# Optimal Inter-Slices Radio Resource Scheduling for Quality of Service Assurance
Generic simulation of RAN with support for slice scheduling

Runs with Python 3.7.17, which you can install via [Pyenv](https://github.com/pyenv/pyenv).

PIP dependencies:
- tqdm
- numpy
- matplotlib
- stable-baselines3
- seaborn
- tensorboard

Install pip dependencies
```bash
pip install tqdm numpy matplotlib stable-baselines3 seaborn tensorboard
```

The repository contains the best trained Nahum's agent used in the paper's evaluation, located in `./best_sac/best_model.zip`. To train again, you can execute:
```bash
python train_agent.py
```

## Experiments
There are three implemented experiments:
- **standard**: SAO uses minimal resources while Nahum's agent and RR use 100%;
- **minimum**: SAO, Nahum's agent and RR use limited resources as calculated by SAO;
- **full**: SAO, Nahum's agent and RR use 100% of the resources. SAO uses 100% by allocating all resources at the same proportion of the minimal needed for each slice. As this behaviour actually do not have interesting results, it is not used in the paper.

To run the experiment, simply execute:
```bash
python main.py <experiment_name>
```

This will execute the chosen experiment and save the simulation data as `./experiment_data/<experiment_name>_experiment_data.pickle`.

To generate plots, execute:
```bash
python plot_metrics.py <experiment_name>
```
This will use the saved experiment data to generate plots in the `./plots/` folder.

To generate plots for the spectral efficiency dataset used in the experiments, execute:
```bash
python plot_se.py <experiment_name>
```
The experiment data is used only for setting up the Plotter class. The spectral efficiency data is the same for every experiment.

The scheduling time for each scheduler can be checked with:
```bash
python check_scheduling_time.py <experiment_name>
```
