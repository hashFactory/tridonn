import torch
from torch import nn
from collections import OrderedDict
import time

model_filename = "tridonn"
#target_file = ".csv"

target_file1 = "BC_ana_results.csv"
target_file2 = "10k_music_ana_results.csv"

print(f"Infering with {model_filename} on {target_file1}")

ff = "{:.5f}".format

device = "cuda" if torch.cuda.is_available() else "cpu"
#print(f"Using {device} device")

N0 = 96
N1 = 192
N2 = 20
N3 = 1
NX = 1

model = nn.Sequential(OrderedDict([
    ('dense1', nn.Linear(N0, N1, True)),
    ('act1', nn.Tanh()),
    ('dense2', nn.Linear(N1, N2, True)),
    ('act2', nn.Tanh()),
    ('output', nn.Linear(N2, N3)),
    #('act3', nn.ReLU()),
    #('output2', nn.Linear(N3, NX)),
    ('outact', nn.Sigmoid()),
]))

"""
N0 = 527
N1 = 1000
N2 = 1
NX = 1

model = nn.Sequential(OrderedDict([
    ('dense1', nn.Linear(N0, N1)),
    ('act1', nn.ReLU()),
    ('dense2', nn.Linear(N1, N2)),
    #('act2', nn.ReLU()),
    #('output', nn.Linear(N2, NX)),
    ('outact', nn.Sigmoid()),
]))
"""
model.load_state_dict(torch.load(model_filename))
#model.to("xpu")
model.eval()

import intel_extension_for_pytorch as ipex

model = model.to("xpu")
model = ipex.optimize(model)

def rate_file(filename):
    rate_file = open(filename, "r").readlines()
    rate_lines = [l.replace('\n', '').split('\t') for l in rate_file]

    my_test_x = [[float(i) for i in l[1+163:1+259]] for l in rate_lines[1:]]
    song_names = [l[0].replace(".m4a.wav", "") for l in rate_lines[1:]]

    print("Song ratings: [0-1]")

    results = {}

    with torch.no_grad():
        #for i in range(len(my_test_x)):
        X = torch.tensor(my_test_x)
        X = X.to("xpu")

        #logits = model(X)

        start = time.perf_counter_ns()

        logits = model(X)

        end = time.perf_counter_ns()
        print(f"Testing took: {(end - start)/1000000}ms")


        for i in range(len(my_test_x)):
            song_name = song_names[i].split('/')[-1]
            results[song_name] = float(logits[i])
        """for i in range(len(my_test_x)):
            X = torch.tensor(my_test_x[i])
            X = X.to("xpu")
            song_name = song_names[i].split('/')[-1]
            logits = model(X)
            results[song_name] = float(logits[0])"""
    return results

def evaluate(target_file):
    values = rate_file(target_file)
    ratings = sorted(values.items(), key=lambda x: x[1], reverse=True)

    print("Top 5:")
    for r in ratings[:20]:
        print(f"{ff(r[1])}: {r[0]}")

    print("\nBottom 5:")
    for r in ratings[-10:]:
        print(f"{ff(r[1])}: {r[0]}")

for i in range(10):
    evaluate(target_file1)

#evaluate(target_file2)
#evaluate(target_file2)
#evaluate(target_file1)
#evaluate(target_file2)
#evaluate(target_file2)
#evaluate(target_file2)
