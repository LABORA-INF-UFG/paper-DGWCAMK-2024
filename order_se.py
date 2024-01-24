from typing import List, Tuple
import numpy as np
import os 

trials: List[Tuple[List[Tuple[int, float, float, float]]]] = []

for trial in range (1, 51):
    ues: List[Tuple[int, float, float, float]] = []
    for u in range(1, 11):
        file_string = "se/trial{}_f{}_ue{}.npy".format(trial, 2, u)
        se = np.load(file_string)
        #ues.append((u, np.mean(np.load(file_string))))
        #ues.append((u, np.max(np.load(file_string))))
        ues.append((u, np.min(se), np.max(se), np.max(se) - np.min(se)))
    ues.sort(key=lambda x: x[1]*x[3], reverse=False) # 1 = min, 2 = max, 3 = dist

    for i in range(10):
        old = "se/trial{}_f{}_ue{}.npy".format(trial, 2, ues[i][0])
        new = "se/trial{}_f{}_ue{}_temp.npy".format(trial, 2, i+1)
        print("Renaming {} to {}".format(old, new))
        os.rename(old, new)
    for i in range(10):
        old = "se/trial{}_f{}_ue{}_temp.npy".format(trial, 2, i+1)
        new = "se/trial{}_f{}_ue{}.npy".format(trial, 2, i+1)
        print("Renaming {} to {}".format(old, new))
        os.rename(old, new)
        print("{} - UE {}".format(i+1, ues[i][0]))
        se = np.load(new)
        print("{} = {}".format(np.mean(ues[i][1]), np.min(se)))

    '''
    if trial == 27:
        for u in range(1,11):
            print("UE {}: Min: {:.2f} - Max: {:.2f} - Dist: {:.2f}".format(ues[u-1][0], ues[u-1][1], ues[u-1][2], ues[u-1][3]))
            pass
    trials.append(tuple([trial, ues]))
    '''
    
trials.sort(key=lambda x: x[1], reverse=False)
for t in trials:
    print("Trial {} - Min: {:.2f} - Med: {:.2f} - Max: {:.2f} - Dist: {:.2f}".format(t[0], t[1][0][1], t[1][4][1], t[1][9][1], t[1][9][1] - t[1][0][1]))


# Worst UE
# Trial 2 - Min: 0.222876610264871 - Med: 0.29965021729907454 - Max: 0.8821877013341034 - Dist: 0.6593110910692324
# Trial 18 - Min: 0.30653808423254275 - Med: 0.5396009653883164 - Max: 2.6402405933570123 - Dist: 2.3337025091244694
# Trial 27 - Min: 0.25553356352898215 - Med: 0.5043601321090633 - Max: 1.1244421208266888 - Dist: 0.8689085572977067
# Trial 33 - Min: 0.1773874203340523 - Med: 0.367562098299949 - Max: 0.9427708526737302 - Dist: 0.7653834323396779
# Trial 36 - Min: 0.18997018828957252 - Med: 0.4405045002427382 - Max: 1.4604837105214878 - Dist: 1.2705135222319153
# Trial 46 - Min: 0.18568053518868172 - Med: 0.6174417026087097 - Max: 1.3391396460777407 - Dist: 1.153459110889059
# Trial 47 - Min: 0.022482337660282348 - Med: 0.3593242481558061 - Max: 1.5249568508164588 - Dist: 1.5024745131561765

# Best UE
# Trial 2 - Min: 0.9427708526737302 - Med: 1.929548185808102 - Max: 6.747550601629224 - Dist: 5.804779748955494
# Trial 18 - Min: 2.807805250628136 - Med: 3.944097609551016 - Max: 16.946745964776003 - Dist: 14.138940714147868
# Trial 27 - Min: 1.3985742988903158 - Med: 3.171273289304911 - Max: 6.747550601629224 - Dist: 5.348976302738908
# Trial 33 - Min: 1.2820928453389664 - Med: 2.4306936750347146 - Max: 4.021654136589946 - Dist: 2.73956129125098
# Trial 36 - Min: 2.1898419976641676 - Med: 3.7927479098947687 - Max: 9.856191332942947 - Dist: 7.666349335278779
# Trial 46 - Min: 1.5581831756766902 - Med: 3.5047531980638973 - Max: 9.155494242195122 - Dist: 7.597311066518431
# Trial 47 - Min: 0.2735941796143956 - Med: 2.2362097581401064 - Max: 8.296031403282303 - Dist: 8.022437223667907