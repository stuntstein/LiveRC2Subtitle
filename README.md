# LiveRC2Subtitle

usage: `LiveRC2Subtitle.py -u="url to main result on liverc.com"`

This pyhton script will fetch the race results from a race on http://www.liverc.com and generate a .srt subtitle file for each heat for that race. The subtitle can be uploaded to youtube for each heat.
The script will find the number of heats and ask for the time offset for when the race actually start in the video.
The files will be stored in a new folder with the trace name and date as folder name.

Note that the URL must be from the Mains Heat Sheet page and in quotes.
ex.
```
python LiveRC2Subtitle.py -u="http://norcalhobbies.liverc.com/results/?p=view_heat_sheet&id=1348298/"

Please type the time ofset from when the race starts.
Time offset for 17.5 Sportsman Buggy A-Main : -28
Please type the time ofset from when the race starts.
Time offset for 17.5 Intermediate Buggy A-Main : 19
Please type the time ofset from when the race starts.
Time offset for 17.5 Expert Buggy A-Main : 29
Please type the time ofset from when the race starts.
Time offset for 4WD Short Course A-Main : 8
Please type the time ofset from when the race starts.
Time offset for 13.5 Stadium Truck A-Main : 10
Please type the time ofset from when the race starts.
Time offset for 4WD Modified Buggy A-Main : 12
```

See result of above example on
https://www.youtube.com/playlist?list=PLY2Ln0z8U2dlg6JRZaTiwtbakxM3cVWb0
