import torch
from torch import nn
from collections import OrderedDict
import time

model_filename = "tridonn"

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using {device} device")

N0 = 527
N1 = 10
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

model.load_state_dict(torch.load(model_filename))
model.eval()

def rate_file(filename):
    rate_file = open(filename, "r").readlines()
    rate_lines = [l.replace('\n', '').split('\t') for l in rate_file]

    my_test_x = [[float(i) for i in l[1:]] for l in rate_lines[1:]]
    song_names = [l[0] for l in rate_lines[1:]]

    print("Song ratings: [0-1]")

    results = {}

    for i in range(len(my_test_x)):
        X = torch.tensor(my_test_x[i])
        song_name = song_names[i].split('/')[-1]
        logits = model(X)
        results[song_name] = float(logits[0])
    return results

values = rate_file("my_fun_playlist.csv")
ratings = sorted(values.items(), key=lambda x: -x[1])

print("Top 5:")
for r in ratings[:5]:
    print(f"{r[0]}: {r[1]}")

print("\nBottom 5:")
for r in ratings[-5:]:
    print(f"{r[0]}: {r[1]}")
