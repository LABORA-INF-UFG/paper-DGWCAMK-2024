import numpy as np
import matplotlib.pyplot as plt

if __name__ == "__main__":
    data = np.load("evaluations/evaluations.npz")
    arr = []
    for i in data["results"]:
        arr.append(np.mean(i))
    plt.plot(arr)
    plt.savefig("evaluations/evaluations.png")