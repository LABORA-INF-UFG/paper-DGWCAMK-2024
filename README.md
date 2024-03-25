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

The repository contains the best-trained DRL agent used in the paper's evaluation, located in `./best_sac/best_model.zip`. To train again, you can execute:
```bash
python train_agent.py
```

## Experiments
There are three implemented experiments:
- **standard**: SOA uses minimal resources while the DRL agent and RR use 100%;
- **minimum**: SOA, the DRL agent and RR use limited resources as calculated by SOA;
- **full**: SOA, the DRL agent, and RR use 100% of the resources. SOA uses 100% by allocating all resources at the same proportion of the minimum needed for each slice. As this behavior does not have interesting results, it is not used in the paper.

To run the experiment, execute:
```bash
python main.py <experiment_name>
```

This will execute the chosen experiment and save the simulation data as `./experiment_data/<experiment_name>_experiment_data.pickle`.

To generate plots, execute:
```bash
python plot_metrics.py <experiment_name>
```
This will generate plots in the `./plots/` folder using the saved experiment data. It also prints general metrics, like the execution time for each scheduler and the set of DRL chosen actions.

To generate plots for the spectral efficiency dataset used in the experiments, execute:
```bash
python plot_se.py <experiment_name>
```
The experiment data is used only for setting up the Plotter class. The spectral efficiency data is the same for every experiment.

The scheduling time for each scheduler can be checked with:
```bash
python check_scheduling_time.py <experiment_name>
```
