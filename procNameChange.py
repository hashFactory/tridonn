import random
from Levenshtein import distance as levenshtein_distance

def go_resf():
    # contains list of analysis results
    resf = open("10k_music_ana_results2.csv", "r")

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
    pairsf = open("arjall/arjall_pairs_10k.csv", "r")

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
newf = open("arjall_10k_synths.csv", "w")

total_dist = 0

found_songs = 0

round2 = []
iteration = 0

for i in range(len(values)):
    res = values[i]
    name = res[0]
    vals = res[1]

    closest_r = None
    closest_score = 100000000

    for r in results:
        dist = levenshtein_distance(name.replace("(", "").replace(")", "").lower(), r[0].replace("(", "").replace(")", "").lower(), weights=(1, 1, 5))
        #dist = levenshtein_distance(name.lower(), r[0].lower(), weights=(1,1,10))
        if dist < closest_score:
            closest_score = dist
            closest_r = r

    if closest_score == 0 and closest_score < len(name) / 2:
        results.remove(closest_r)
        prepped_values = '\t'.join(vals)
        newf.write(f"{name}\t{closest_r[1]}\t{prepped_values}\n")
        total_dist += closest_score
        found_songs += 1
    else:
        print(f"SKIPPING for round 2! {closest_score} vs len {len(name) / 2}")
        round2.append(res)

    print(f"sim: {closest_score}\tTARGET: {name}\tCLOSEST: {closest_r[0]}")

def run_iter(remaining):
    global total_dist, found_songs, iteration
    iteration += 1
    if iteration > 10:
        return
    print(f"-------- ROUND {iteration} --------")
    random.shuffle(remaining)
    #results = results[::-1]

    for i in range(len(round2)):
        res = round2[i]
        name = res[0]
        vals = res[1]

        closest_r = None
        closest_score = 100000000

        for r in remaining:
            dist = levenshtein_distance(name.replace("(", "").replace(")", "").lower(), r[0].replace("(", "").replace(")", "").lower(), weights=(1, 1, 8))
            #dist = levenshtein_distance(name.lower(), r[0].lower(), weights=(1,1,10))
            if dist < closest_score:
                closest_score = dist
                closest_r = r

        if closest_score == 0:
            remaining.remove(closest_r)

        if closest_score < len(name) / 2:
            prepped_values = '\t'.join(vals)
            newf.write(f"{name}\t{closest_r[1]}\t{prepped_values}\n")
            total_dist += closest_score
            remaining.remove(closest_r)
            found_songs += 1
        else:
            print(f"SKIPPING! {closest_score} vs len {len(name) / 2}")

        print(f"sim: {closest_score}\tTARGET: {name}\tCLOSEST: {closest_r[0]}")
        #print(f"closest name {closest_r[0]}")

    #total_dist += closest_score
    print(f"total songs: {len(values)}")
    print(f"songs in round 2: {len(remaining)}")
    print(f"total songs matched: {found_songs}")
    print(f"total dist: {total_dist}")
    run_iter(remaining)

run_iter(results)

newf.close()

#print(go_resf()[:10])
#print(go_pairsf()[:10])


#print(lines)
