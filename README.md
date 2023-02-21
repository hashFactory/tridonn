# tridonn
A PyTorch NN trained to recognize songs I might like based on Spotify listening history.

### To train

1. get complete Spotify listening history and move into `MyData`
2. run `procRatingsEndsongs.py` to guess rating and select subset of songs
3. clone [fschimd56/EfficientAT](https://github.com/fschmid56/EfficientAT)
4. copy `better_infer.py` into `EfficientAT` and run from there
5. copy back analyzed `.csv` into this folder and run `procNameChange.py`
6. can now start training using `tridonn.ipynb`

### To infer

(only once you have `_synth.csv` and a target `.csv` to rate)
1. run `infer.py`
