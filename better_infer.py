import os
import argparse
import torch
#import librosa
import numpy as np
from torch import autocast
from contextlib import nullcontext

from models.MobileNetV3 import get_model as get_mobilenet, get_ensemble_model
from models.preprocess import AugmentMelSTFT
from helpers.utils import NAME_TO_WIDTH, labels

import ffmpeg

float_formatter = "{:.5f}".format
np.set_printoptions(formatter={'float_kind':float_formatter})

#target_dir = "/tmp/tri/testaudio/rising/"

# find ./ -name '*.m4a' -exec ffmpeg -i "{}" -c:v pcm_f32le -ar 32k -ac 1 -y "{}.wav" \;

dedup = []

def audio_tagging(args):
    """
    Running Inference on an audio clip.
    """
    model_name = args.model_name
    device = torch.device('cuda') if args.cuda and torch.cuda.is_available() else torch.device('cpu')
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
    model.to(device)
    model.eval()

    # model to preprocess waveform into mel spectrograms
    mel = AugmentMelSTFT(n_mels=n_mels, sr=sample_rate, win_length=window_size, hopsize=hop_size)
    mel.to(device)
    mel.eval()

    output_filename = "arjun_rating_ana_results.csv"

    audio_split = audio_path.split("/")
    if len(audio_split) > 1:
        if len(audio_split[-2]) > 0:
            output_filename = audio_split[-2] + "_ana_results.csv"
        if len(audio_split[-1]) > 0:
            output_filename = audio_split[-1] + "_ana_results.csv"

    existed = os.path.isfile(output_filename)

    prev = []
    of = None

    if existed:
        get = open(output_filename, "r")
        prev = [l.split("\t")[0] for l in get.readlines()[1:]]
        get.close()
        of = open(output_filename, "a")
    else:
        of = open(output_filename, "w")
        of.write("song name\t" + "\t".join(labels) + "\n")


    print(prev)
    found_names = os.listdir(audio_path)
    found_names = [audio_path + f for f in found_names if ".m4a" in f and audio_path + f not in prev]

    #of.write("song name\t" + "\t".join(labels) + "\n")
    count = 0

    for song_filename in found_names:
        print(f"----  COUNT {count} / {len(found_names)} -----")
        #(waveform, _) = librosa.core.load(song_filename, sr=sample_rate, mono=True)
        rawaudio, _out  = (ffmpeg.input(song_filename).output('-', format='f32le', acodec='pcm_f32le', ac=1, ar='32000').run(capture_stdout=True, capture_stderr=True))
        print("GOT HERE")

        audio = np.frombuffer(rawaudio, dtype=np.float32).copy()
        waveform = torch.from_numpy(audio[None, :]).to(device)

        # our models are trained in half precision mode (torch.float16)
        # run on cuda with torch.float16 to get the best performance
        # running on cpu with torch.float32 gives similar performance, using torch.bfloat16 is worse
        with torch.no_grad(), autocast(device_type=device.type) if args.cuda else nullcontext():
            spec = mel(waveform)
            preds, features = model(spec.unsqueeze(0))
        preds = torch.sigmoid(preds.float()).squeeze().cpu().numpy()

        #sorted_indexes = np.argsort(preds)[::-1]

        # Print audio tagging top probabilities
        #print("************* Acoustic Event Detected: *****************")
        #for k in range(10):
        #    print('{}: {:.3f}'.format(labels[sorted_indexes[k]],
        #        preds[sorted_indexes[k]]))
        #print("********************************************************")

        dedup.append(song_filename)
        out_str = song_filename + "\t"

        #for k in range(len(labels)):
        out_str += "\t".join([float_formatter(k) for k in preds])
        out_str += "\n"

        of.write(out_str)
        count += 1
        #as_a_str = [float_formatter(k) for k in preds[sorted_indexes[k]]))]
    of.close()



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Example of parser. ')
    # model name decides, which pre-trained model is loaded
    parser.add_argument('--model_name', type=str, default='mn40_as_ext')
    parser.add_argument('--strides', nargs=4, default=[2, 2, 2, 2], type=int)
    parser.add_argument('--head_type', type=str, default="mlp")
    parser.add_argument('--cuda', action='store_true', default=False)
    parser.add_argument('--audio_path', type=str, required=False)

    # preprocessing
    parser.add_argument('--sample_rate', type=int, default=32000)
    parser.add_argument('--window_size', type=int, default=800)
    parser.add_argument('--hop_size', type=int, default=320)
    parser.add_argument('--n_mels', type=int, default=128)

    # overwrite 'model_name' by 'ensemble_model' to evaluate an ensemble
    parser.add_argument('--ensemble', nargs='+', default=[])

    args = parser.parse_args()

    audio_tagging(args)
