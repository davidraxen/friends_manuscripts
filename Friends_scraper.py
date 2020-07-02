#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 22 19:44:20 2020

@author: davidraxen

"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Friends_scraper.py - Structuring friends-data
import time
start_time = time.time()

import re
import logging
import pandas as pd
logging.basicConfig(filename='myProgramLog.txt', level=logging.DEBUG, format=' %(asctime)s - %(levelname)s - %(message)s')
logging.debug('Start of program')
import requests

print("Loading data...") # display some text to make it clear stuff is happening

def cHtml(x):
    return x.replace("&nbsp;", " ").replace(
            "&quot;", '"').replace("&amp;", "&").replace("&#8217;", "'").replace(
            "&#8230;", "...").replace("&eacute;", "é").replace(
            "&Eacute;", "É").replace("&#8212;", "-").replace("&rsquo;", "'").replace(
            "&ccedil;", "ç").replace("&#8221;", '"').replace("&#8220;", "“").replace(
            "&#8216;", "‘").replace("&#150;", "-").replace("&#133;", "...").replace(
            "&lt;", "(").replace("&gt;", ")").replace("&#146;", "'").replace(
                "&egrave;", "è").replace("&iacute;", "í").replace("    "," ").replace(
                    "&ndash;", "-").replace("&#151;", "-").replace("&#145;", "'").replace(
                        "&#147;", '"').replace("&#148;", '"').replace("&#173;", "-")


#getting html from main repository
main = "https://fangj.github.io/friends/"
res = requests.get(main)
res.raise_for_status()
res = res.text # making a string of the request object.
res = cHtml(res) # replacing strings that should be encoded as symbols
res = res.splitlines() # create a list where each row is an item


# ----- Regex's needed for finding each character's line per episode.
link_re = "(?<=\<a\shref\=\")(.*?)(?=\")" # Finding the link to the episodes
epi_re = "(?<=\"\>)(.*?)(?=\<)" # Finding the name of the episode

# --- Things to remove from strings to make sure the right things gets captured
clean1 = "\<a\sname.*?\>" 
clean2 = "\<.*?\>"

# - Patterns to find rows that indicates a character line or a new scene.
t = "(?<=\<p)(.*?)(?=\<\/p)" #everything between <p and /p -> >"line"<
t2 = "Scene:|[A-Z]+[A-Z]\:.*?<" #the word string Scene: or everything including and after 2 (or more) capital letters followed by a : until a "<"
t3 = "Scene:|\<b\>.*?<"  # The string Scene: or <b>some string<
# -------------------------

Episodes = {}
for line in res:
    if "<li><a href=" in line and "outtakesFriends" not in line: # iterate through each line in res and find links for all episodes except the blooper one.
        #----------
        epi_link = main + re.search(link_re, line).group(0) #finding the link to the episode in the main repository by using the link_re-regex
        res2 = requests.get(epi_link)
        res2.raise_for_status()
        res2 = res2.text.replace('\r', ' ').replace('\n', ' ').replace('strong>', 'b>').replace('B>', 'b>').replace('P>', 'p>').replace('I>', 'i>')
        res2 = re.sub(clean1, "", res2) # removing all <a name(something)> from the texts.
        res2 = cHtml(res2)

        res2_list = re.findall(t, res2) #Finding all character lines and indication for a new scene in Most episodes.
        if len(res2_list) < 50: # The episodes structured in this way will have Way more lines than 50 - so if there is less it's structured in a different way
            res2 = res2.replace("<br>", "<").replace(
                            "<i>", "").replace("</i>", "").replace("</a>", "") #removing some unecissary html and creating a symbol "<" that i can reference later.
            res3 = re.sub("\>\(.*?\)\<", "Scene:", res2) # Inserting "Scene:"-indications based on how it's structured in Most of the episodes that the first method didn't work for.
            res2_list = re.findall(t2, res3) #A new try to find all scenes and character lines. -> This time with a new regex "t2".
        if len(res2_list) < 50: #If it still didn't work this will catch the remaining episodes.
            res2 = res2.replace("</b>", "") #remove <"/b" from the string.
            res2_list = re.findall(t3, res2) #finds everything between <b> and "<" (which was created on line 74)
        for i, s in enumerate(res2_list): #iterate through each index and resp. string in the res2_list
            res2_list[i] = re.sub(clean2, "", s) #removes lingering html-tags
            if ">" in res2_list[i]: #Splits in a remaining ">" to find the actual line.
                res2_list[i] = res2_list[i].split(">")[1]
            if "<" in res2_list[i]: #Splits in a remaining "<" (created on line 74) to find the actual line.
                res2_list[i] = res2_list[i].split("<")[0]
        Episodes[re.search(epi_re, line).group(0)] = res2_list #Creates a dictionary where the title of each episode is a key and the list of lines and scenes are are the corresponding value

df = pd.DataFrame(columns=["EpiNo", "EpiTitl", "Scene", "Character", "Line"]) #Creates an empty DataFrame
for key, lst in Episodes.items(): # Loop through keys and lists
    scene = 0 #starting value to not get title as lines.
    for i in range(0,len(lst)): #loop through whole list och lines and scenes
        if "Scene:" in lst[i] or ("Scene:" not in lst[i] and "[at" in lst[i]) or (
                "Scene:" not in lst[i] and "[Central" in lst[i]) or (
                    "Scene:" not in lst[i] and "(At" in lst[i]) or (
                        "Scene:" not in lst[i] and "(at" in lst[i]): #different types of indication for a new scene
            scene += 1 # Add one when an indiciation of a new scene is found.
        if scene > 0: 
            if "Scene:" not in lst[i] and ":" in lst[i]: #Find character lines
                row = [key.split(" ", 1)[0], key.split(" ", 1)[1].strip() #Separate numbers from the name for each episode.
                       , scene, lst[i].split(":", 1)[0].strip() #Get the scene number and the name for the character (exceptions will get handled further down)
                       , lst[i].split(":", 1)[1].strip()] # Add the line the character says
                row = pd.Series(row, index = df.columns) # make the list of information into a series
                df = df.append(row, ignore_index=True) # append the series as a row in the dataframe
    if scene == 0: #handle exception for episode with no indication for new scenes. (Mostly the same as above)
        for i in range(0,len(lst)):
            if ":" in lst[i] and "Originally written by Michael Curtis" not in lst[i]:
                row = [key.split(" ", 1)[0], key.split(" ", 1)[1].strip(), "-", lst[i].split(":", 1)[0].strip(), lst[i].split(":", 1)[1].strip()]
                row = pd.Series(row, index = df.columns)
                df = df.append(row, ignore_index=True)

#--- Cleaning up the Character-column and dropping none-character-line.

        
df['Character'] = df['Character'].str.replace(r"\(.*\)","") #remove paranthesis and text inside them
df['Character'] = df['Character'].apply(lambda x: x.strip()) # remove lingering whitespace

df = df.dropna().reset_index(drop=True) #Drop na-values.

#finding index for Character-values that starts with a letter.
idx = []
for i in df.index:
    if len(df["Character"][i]) > 0:
        if str(df["Character"][i][0]).isalpha():
            idx.append(i)

df2 = df.iloc[idx,:].reset_index(drop=True) #drop all rows that doesn't start with a letter and re-index the dataframe (as a new dataframe)

df2["Character"] = df2["Character"].apply(lambda x: x.lower().title()) # Makes all names start with capital letters and the rest are lowercase.

df2["Character"] = df2["Character"].apply(lambda x: x.replace(
                "And ", ",").replace("& ", ",").replace("/", ", ").replace(" ,", ", ").replace(",,", ",")) #Clean upp values with multiple characters (and some exceptions)
df2["Character"] = df2["Character"].apply(lambda x: "Amy" if x[0:3] == "Amy" else x) # Clean up Characters from an episode where the character "Amy" had alot of extra information connected to her name


def cRemover(x): #Handle the rest of the cases with multiple character or "," in them.
    if x == "Mr., Mrs. Geller":
        return ("Jack, Judy")
    if x == "Buffay, The Vampire Layer":
        return "Buffay - The Vampire Layer"
    if x == "Rachel, Actress":
        return "Rachel"
    y = x.split(", ")
    for i in y:
        z = i.split()
        if len(z) > 1:
            return x.split()[0].replace(",", "")
    x = x.replace("Actress, ", "Actress ").replace(", Shocked", "")
    return x

df2["Character"] = df2["Character"].apply(lambda x: cRemover(x) if "," in x else x) #- Run the above function

#- Handle a few cases where the character name was shortened.
df2["Character"] = df2["Character"].apply(lambda x: re.sub(r'\bRach\b', 'Rachel', x))
df2["Character"] = df2["Character"].apply(lambda x: re.sub(r'\bChan\b', 'Chandler', x))
df2["Character"] = df2["Character"].apply(lambda x: re.sub(r'\bPhoe\b', 'Phoebe', x))
df2["Character"] = df2["Character"].apply(lambda x: re.sub(r'\bMnca\b', 'Monica', x))
df2["Character"] = df2["Character"].apply(lambda x: re.sub(r'\bEstl\b', 'Estelle', x))
df2["Character"] = df2["Character"].apply(lambda x: re.sub(r'\bRahcel\b', 'Rachel', x))

df2["Character"] = df2["Character"].apply(lambda x: x if "," not in x else ", ".join(sorted(x.replace(",", "").split()))) #make the final step in formatting the values with multiple characters by separating them with a comma.
df2["Character"] = df2["Character"].apply(lambda x: x.replace("'S", "'s")) #fix Joey'S as Joey's


#remove instructions to actors from the lines (saving in a new column and keeping the instruction if there is a need for them)
df2["Line_cl"] = df2["Line"].str.replace(r"\(.*?\)","")
df2["Line_cl"] = df2["Line_cl"].str.replace(r"\[.*?\]","")
df2["Line_cl"] = df2["Line_cl"].str.replace(r"\*.*?\*","")
df2["Line_cl"] = df2["Line_cl"].apply(lambda x: " ".join(x.replace('"', "").split()))

#removing lines that Only was instructions.
idx = []
for i in df2.index:
    if len(df2["Line_cl"][i]) > 0:
        idx.append(i)

df2 = df2.iloc[idx,:].reset_index(drop=True)
#------------------------------
#-- Removing scenes from episode where 908 since I haven't found a smart way of finding the scenes in that episode yet.
df2.loc[df2.EpiNo == "908", 'Scene'] = "-"

df2.to_csv (r'friends.csv', index = False, header=True)

print("Done! This took %s seconds" % (time.time() - start_time))