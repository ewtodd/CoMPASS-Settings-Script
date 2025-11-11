These scripts extracts human-readable settings from CoMPASS settings.xml files, prints them, and returns a pandas dataframe containing them. There are now two versions because the scenarios were significantly different. 

ANSG Usage: 
```
python ANSG-getCoMPASS.py /path/to/settings.xml 
```

MUSIC Usage:
```
# Show all boards and channels
python MUSIC-getCoMPASS.py settings.xml

# Show only board 0
python MUSIC-getCoMPASS.py settings.xml --board 0

# Show only channels 3 and 11 from all boards
python MUSIC-getCoMPASS.py settings.xml --channels 3 11

# Show channels 3 and 11 from board 0 only
python MUSIC-getCoMPASS.py settings.xml --board 0 --channels 3 11
```


```
