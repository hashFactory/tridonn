import json
import random

# folder which contains endsong files
filename = "MyData/endsong_"

def c(string):
    return string.replace(';', '').replace(',', '').replace("/", " ")

megasongs = []
repo = {}
reposongs = {}

# add up time played of all songs since 2020
for n in range(0,15):
    f = open(filename + str(n) + ".json", 'r')
    j = json.loads(f.read())

    for song in j:
        if song.get('master_metadata_track_name') and song.get('ts').startswith('202'):
            csv_string = f"{c(song['master_metadata_track_name'])},{c(song['master_metadata_album_artist_name'])},{c(song['master_metadata_album_album_name'])}"

            reposongs[song['spotify_track_uri']] = csv_string

            if song.get("spotify_track_uri") in repo:
                repo[song["spotify_track_uri"]] += song["ms_played"]
            else:
                repo[song["spotify_track_uri"]] = song["ms_played"]

    f.close()

# _tracklist_ contains list of songs to import to soundiiz
t = open("rating_tracklist_10k.txt", "w")
# _pairs contains song names + total ms played (the actual rating)
f = open("rating_pairs_10k.csv", "w")
# _indices contains which songs were picked for archival purposes
ind = open("rating_indices_10k.txt", "w")

t.write("title,artist,album\n")

repolist = sorted(repo.items(), key=lambda x:x[1], reverse=True)
#for k, v in repo.items():
#    if v > 1:
#        print(f"{k}: {reposongs[k]}")
#        #f.write(reposongs[k] + "\n")
indexes = [i for i in range(len(repolist))]
newindexes = random.choices(indexes, k=10000)

selection = [repolist[i] for i in newindexes]
#print(selection)

index = 0
# write out resulting files
for k in selection:
    if k[1] > 0:
        print(f"{k[1]}: {reposongs[k[0]]}")
        f.write(f"{k[0]}\t{k[1]}\t{reposongs[k[0]]}\n")
        t.write(f"{reposongs[k[0]]}\n")
        ind.write(f"{newindexes[index]}\n")
    index += 1

# output
print(f"selected {len(megasongs)} songs")
print(f"found {len(reposongs)} total songs")

f.close()
t.close()
ind.close()

"""
f = open("arjun_all_ms_played.csv", "w")

f.write("title,artist,album\n")

repolist = sorted(repo.items(), key=lambda x:x[1], reverse=True)

total = 0
for r in repolist:
    total += r[1]
#for k, v in repo.items():
#    if v > 1:
#        print(f"{v}ms: {reposongs[k]}")
#for k in repolist[0:4000]:
#    print(f"{int(k[1]/1000)}s: {reposongs[k[0]]}")
#        #f.write(reposongs[k] + "\n")
for k in repolist[:100]:
#    if k[1] > 3:
    print(f"{k[1]}: {reposongs[k[0]]}")
    f.write(reposongs[k[0]] + "\n")

for k in repolist[-100:]:
#    if k[1] > 3:
    print(f"{k[1]}: {reposongs[k[0]]}")
    f.write(reposongs[k[0]] + "\n")
print(len(megasongs))

print(f"Total listening time: {int(total/1000)} sec")
"""
