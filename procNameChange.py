from Levenshtein import distance as levenshtein_distance

def go_resf():
    # contains list of analysis results
    resf = open("10k_music_ana_results.csv", "r")

    lines = resf.readlines()
    lines = [l.replace('\n', '').split('\t') for l in lines]

    res = []

    for l in lines[1:]:
        #print(l)
        loc1 = l[0].find('- ', (l[0].find("_10k/") + 5)) + 2
        loc2 = l[0].find(".m4a")
        song_name = l[0][loc1:loc2]
        values = l[1:]

        res.append((song_name, values))

    resf.close()

    return res

def go_pairsf():
    # input pairs w/ ratings
    pairsf = open("rating_pairs_10k.csv", "r")

    lines = pairsf.readlines()
    lines = [l.replace('\n', '').split('\t') for l in lines]

    res = []

    for l in lines:
        rating = l[1]
        song_info = l[2].split(',')

        title = song_info[0]
        artist = song_info[1]
        album = song_info[2]

        synth_name = f"{artist} - {album} - {title}"

        res.append((synth_name, rating))

    pairsf.close()

    return res

values = go_resf()
results = go_pairsf()

print(len(values))
print(len(results))
#assert len(values) == len(results)

# this will contain synthesized list of songs + ratings + analysis
newf = open("rating_10k_synths.csv", "w")

for i in range(len(values)):
    res = values[i]
    name = res[0]
    vals = res[1]

    closest_r = None
    closest_score = 100000000

    for r in results:
        dist = levenshtein_distance(name, r[0], weights=(1,1,10))
        if dist < closest_score:
            closest_score = dist
            closest_r = r

    prepped_values = '\t'.join(vals)
    newf.write(f"{name}\t{closest_r[1]}\t{prepped_values}\n")

    print(f"target name {name}\tclosest name {closest_r[0]}")
    #print(f"closest name {closest_r[0]}")

newf.close()
#print(go_resf()[:10])
#print(go_pairsf()[:10])


#print(lines)
