import os
import argparse
import torch
from torch import nn
from collections import OrderedDict
import time

import numpy as np
from contextlib import nullcontext

from models.MobileNetV3 import get_model as get_mobilenet, get_ensemble_model
from models.preprocess import AugmentMelSTFT
from helpers.utils import NAME_TO_WIDTH

import ffmpeg

# tidal login management
import tidal_dl.events as ev
import tidal_dl.settings as tdlset

tdlset.SETTINGS.read(ev.getProfilePath())
tdlset.SETTINGS.audioQuality = tdlset.AudioQuality.Normal
ev.TOKEN.read(ev.getTokenPath())
ev.TIDAL_API.apiKey = ev.apiKey.getItem(tdlset.SETTINGS.apiKeyIndex)

if not ev.apiKey.isItemValid(tdlset.SETTINGS.apiKeyIndex):
    ev.changeApiKey()
    ev.loginByWeb()
elif not ev.loginByConfig():
    ev.loginByWeb()

#import intel_extension_for_pytorch as ipex

float_formatter = "{:.6f}".format
np.set_printoptions(formatter={'float_kind':float_formatter})

#target_dir = "/tmp/tri/testaudio/rising/"

dedup = []

import http.server
import csv

results_filename = "../arjall_10k_synths_matched.csv"
results_songcache = "songcache_additions.csv"
cache_writer = None
should_cache = True
SERVER_ADRESS = "192.168.1.86"
PORT = 25125

db = {}
ids = []

device = ""
audio_path = ""

model = None
mel = None

model_filename = "tridonn"

N0 = 96
N1 = 192
N2 = 20
N3 = 1
NX = 1

tridonn_model = nn.Sequential(OrderedDict([
    ('dense1', nn.Linear(N0, N1, True)),
    ('act1', nn.Tanh()),
    ('dense2', nn.Linear(N1, N2, True)),
    ('act2', nn.Tanh()),
    ('output', nn.Linear(N2, N3)),
    #('act3', nn.ReLU()),
    #('output2', nn.Linear(N3, NX)),
    ('outact', nn.Sigmoid()),
]))

def populate_db(results_filename, results_songcache):
    global db, cache_writer
    get = open(results_filename, "r")
    lines = csv.reader(get, delimiter='\t')

    for l in lines:
        db[l[1]] = [float(v) for v in l[2:]]
        #print(f"Added {l[1]} with vals {db[l[1]]}")

    get.close()

    get = open(results_songcache, "r")
    lines = csv.reader(get, delimiter='\t')

    for l in lines:
        db[l[1]] = [float(v) for v in l[2:]]
        #print(f"Added {l[1]} with vals {db[l[1]]}")

    get.close()

    if should_cache:
        cache_writer = open(results_songcache, "a")

def setup_models(args):
    global device, audio_path, model, mel, tridonn_model
    model_name = args.model_name
    #device = torch.device('cuda') if args.cuda and torch.cuda.is_available() else torch.device('cpu')
    #device = torch.device('xpu') if args.intel else torch.device('cpu')
    device = torch.device('cpu')
    audio_path = args.audio_path
    sample_rate = args.sample_rate
    window_size = args.window_size
    hop_size = args.hop_size
    n_mels = args.n_mels

    # load pre-trained model
    if len(args.ensemble) > 0:
        model = get_ensemble_model(args.ensemble)
    else:
        model = get_mobilenet(width_mult=NAME_TO_WIDTH(model_name), pretrained_name=model_name, strides=args.strides,
                              head_type=args.head_type)
    model.eval()
    #model = model.to(device)
    #if args.cuda:
    #    model = ipex.optimize(model)

    # model to preprocess waveform into mel spectrograms
    mel = AugmentMelSTFT(n_mels=n_mels, sr=sample_rate, win_length=window_size, hopsize=hop_size)
    mel.eval()

    tridonn_model.load_state_dict(torch.load(model_filename))
    #model.to("xpu")
    tridonn_model.eval()

def fetch(trackid):
    global db
    if db.get(trackid) is not None:
        print(f"Found {trackid} in database!")
        inference = infer(db.get(trackid))
        return inference
    else:
        print(f"Downloading {trackid}")
        #result = subprocess.run(['tidal-dl', '-l', trackid, '-q', 'High', '-o', 'songcache/'], capture_output=True, text=True)
        ev.start(trackid)

        #lines = result.stdout.splitlines()
        #print(f"{lines}")
        filenames = [os.path.join(dp, f) for dp, dn, fn in os.walk(os.path.expanduser("songcache/")) for f in fn if ".m4a" in f]
        files = [f.split("/")[-1].split(" ")[0] for f in filenames]

        index = files.index(trackid)
        filename = filenames[index]

        print(f"For trackid {trackid} found {filename}")

        preds = analyze(trackid, filename)

        inference = infer(preds)
        print(f"--- guessed score: {inference} ---")
        return inference
        #print(f"line: {l}")

        #print(f"found path: {}")


def analyze(trackid, trackfilename):
    global device, model, mel

    rawaudio, _out = (ffmpeg.input(trackfilename).output('-', format='f32le', acodec='pcm_f32le', ac=1, ar='32000').run(capture_stdout=True, capture_stderr=True))
    print(f"GOT to {trackfilename}")

    if len(rawaudio) < 230400000:
        audio = np.frombuffer(rawaudio, dtype=np.float32).copy()
        waveform = torch.from_numpy(audio[None, :])#.to(device)

        # our models are trained in half precision mode (torch.float16)
        # run on cuda with torch.float16 to get the best performance
        # running on cpu with torch.float32 gives similar performance, using torch.bfloat16 is worse
        #with torch.no_grad(), autocast(device_type=device.type) if "" == " " else nullcontext():
        with torch.no_grad(), nullcontext():
            spec = mel(waveform)
            preds, features = model(spec.unsqueeze(0))
            preds = torch.sigmoid(preds.float()).squeeze().cpu().numpy()
            #print(preds)
            db[trackid] = preds.tolist()
            if should_cache:
                #preds_string = [float_formatter(p)+"\t" for p in preds.tolist()][:-1]
                preds_string = "\t".join([float_formatter(k) for k in preds])
                #print(preds_string)
                cache_writer.write(f"{trackfilename.split('/')[-1].replace('.m4a', '')}" + "\t" + f"{trackid}" + "\t" + f"{preds_string}" + "\n")
                cache_writer.flush()
                print(f"Added {trackid} to database")
            return preds

def infer(preds):
    global tridonn_model
    my_test_x = preds[163:259]

    print("Song ratings: [0-1]")

    with torch.no_grad():
        #for i in range(len(my_test_x)):
        X = torch.tensor(my_test_x)
        #X = X.to("xpu")
        start = time.perf_counter_ns()

        logits = tridonn_model(X)

        end = time.perf_counter_ns()
        print(f"Testing took: {(end - start)/1000000}ms")
        print(f"Score: f{logits[0]}")

        return logits[0]
    return 0

class Serv(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        split_path = self.path.split("/")

        if self.path == "/":
            print("Got empty request!")

        if split_path[-3] == "track":
            target = split_path[-2]
            result = fetch(target)

            """Respond to a GET request."""
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(bytes(f"{result}", 'utf-8'))

        else:
            print(f"Got invalid request: {self.path}")
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(bytes("Error", 'utf-8'))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Example of parser. ')
    # model name decides, which pre-trained model is loaded
    parser.add_argument('--model_name', type=str, default='mn40_as_ext')
    parser.add_argument('--strides', nargs=4, default=[2, 2, 2, 2], type=int)
    parser.add_argument('--head_type', type=str, default="mlp")
    parser.add_argument('--intel', action='store_true', default=False)
    parser.add_argument('--audio_path', type=str, required=False)

    # preprocessing
    parser.add_argument('--sample_rate', type=int, default=32000)
    parser.add_argument('--window_size', type=int, default=800)
    parser.add_argument('--hop_size', type=int, default=320)
    parser.add_argument('--n_mels', type=int, default=128)

    # overwrite 'model_name' by 'ensemble_model' to evaluate an ensemble
    parser.add_argument('--ensemble', nargs='+', default=[])

    args = parser.parse_args()

    setup_models(args)
    populate_db(results_filename, results_songcache)

    httpd = http.server.ThreadingHTTPServer((SERVER_ADRESS, PORT), Serv)
    httpd.serve_forever()

