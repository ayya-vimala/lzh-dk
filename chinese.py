# -*- coding: utf-8 -*-
""" 

To do before running this file:
- create a dictionary from the files, removing the "T28_1548_001:".
- Make sure all characters like `[，、」：？。]` are moved to the previous entry. 

```
",
    "(.*?)": "([，、」：？。])
```
    to
```
\2",
    "\1": "
```
and 
```
",
    "(.*?)": "(.[，、」：？。])"
```
    to 
```
\2"
```

- Remove the header of each facsicle and put that in HeadingRoot together with the rest of the info.

- add a '$' in front of each new SC file to be made (in front of each chapter/sutta)

- Make sure last line is a dummy line for each facsicle.

- Add `"end": "$1",` before the last line in the last file.

- Save everything to `segments_edited`

- I changed this:
```
"(.*?)_([0-9]+)": "(\$.*?第[一二三四五六七八九十]+)(.*?)",\n
```
to
```
"\1_\2": "\3",\n    "\1_99": "\4",\n
```
as per Charles instructions.

"""

import re
import os
import json

class HeadingRoot:
    """Heading info for all files"""
    def __init__(self):
        self.textname = "阿毘達磨法蘊足論"
        self.textwriter = "尊者大目乾連造"
        self.textsub = "三藏法師玄奘奉　詔譯"
        self.reference = "t26.1537"
        self.filename = "t1537."
        self.basefilename = "ZH_T26_1537_"

def addHeader(counter, heading):

    root_list = {}
    reference_list = {}
    html_list = {}

    root_list[heading.filename+str(counter)+":0.1"] = heading.textname
    root_list[heading.filename+str(counter)+":0.2"] = heading.textwriter
    root_list[heading.filename+str(counter)+":0.3"] = heading.textsub
    root_list[heading.filename+str(counter)+":0.4"] = "("+str(counter)+")"
    reference_list[heading.filename+str(counter)+":0.1"] = heading.reference+"."+str(counter)

    html_list[heading.filename+str(counter)+":0.1"] = "<article id='"+heading.filename+str(counter)+"'><header><ul><li class='division'>{}</li>"
    html_list[heading.filename+str(counter)+":0.2"] = "<li class='subdivision'>{}</li>"
    html_list[heading.filename+str(counter)+":0.3"] = "<li class='subheading'>{}</li></ul>"
    html_list[heading.filename+str(counter)+":0.4"] = "<h1 class='sutta-title'>{}</h1></header>"

    return root_list, reference_list, html_list


base_dir = os.environ['HOME']+'/lzh-dk/segments_edited/'
outputroot_dir = os.environ['HOME']+'/lzh-dk/root/'
outputreference_dir = os.environ['HOME']+'/lzh-dk/reference/'
outputhtml_dir = os.environ['HOME']+'/lzh-dk/html/'

parcounter = 1
secparcounter = 1
counter = 1
heading=HeadingRoot()

paragraphmarks = ["？", "。"]

filecounterlist = ["{0:03}".format(i) for i in range(1,13)]

for filecounter in filecounterlist:

    print(filecounter+'.json')
    fileIn = open(base_dir+heading.basefilename+filecounter+'.json','r', encoding='utf8').read()
    jsonobject = json.loads(fileIn)
    endpar = ""
    beginpar = "<p>"
    versebegin = ""

    for item, item_next in zip(jsonobject, list(jsonobject)[1:]):
            if jsonobject[item].startswith("$"):
                if 'fileOut' in locals():
                    fileOut.write(json.dumps(root_list, ensure_ascii=False, indent=2))
                    fileOutReference.write(json.dumps(reference_list, ensure_ascii=False, indent=2))
                    fileOuthtml.write(json.dumps(html_list, ensure_ascii=False, indent=2))
                    counter += 1

                print(counter)

                root_list, reference_list, html_list = addHeader(counter, heading)

                root_list[heading.filename+str(counter)+":1.0"] = jsonobject[item].lstrip("$")
                reference_list[heading.filename+str(counter)+":1.0"] = "t"+item.split("_")[0]
                html_list[heading.filename+str(counter)+":1.0"] = "<p>"+"{}"+"</p>"

                fileOut = open(outputroot_dir+heading.filename+str(counter)+'_root-lzh-sct.json','w', encoding='utf8')
                fileOutReference = open(outputreference_dir+heading.filename+str(counter)+'_reference.json','w', encoding='utf8')
                fileOuthtml = open(outputhtml_dir+heading.filename+str(counter)+'_html.json','w', encoding='utf8')

                parcounter = 1
                secparcounter = 1

            else:
                middlepar = "{}"
                verseend = ""
                if "　　" in jsonobject[item]:
                    middlepar = "<span class='verse-line'>{}</span>"
                    if "　　" not in jsonobject[item_next]:
                        verseend = "</blockquote>"

                if beginpar.startswith("<p>"):
                    parcounter += 1
                    secparcounter = 0
                if jsonobject[item].endswith("？") or jsonobject[item].endswith("。") or jsonobject[item].endswith("：") or jsonobject[item].endswith("？」") or jsonobject[item].endswith("。」"):
                    endpar = "</p>"
                    html_list[heading.filename+str(counter)+":"+str(parcounter)+'.'+str(secparcounter)] = versebegin+beginpar+middlepar+endpar+verseend
                    beginpar = "<p>"
                    endpar = ""
                else:
                    html_list[heading.filename+str(counter)+":"+str(parcounter)+'.'+str(secparcounter)] = versebegin+beginpar+middlepar+endpar+verseend
                    beginpar = ""

                versebegin = ""
                if middlepar == "{}" and "　　" in jsonobject[item_next]:
                    versebegin = "<blockquote class = 'gatha'>"

                root_list[heading.filename+str(counter)+":"+str(parcounter)+'.'+str(secparcounter)] = jsonobject[item]
                    
                if not "t"+item.split("_")[0] in reference_list.values():
                    reference_list[heading.filename+str(counter)+":"+str(parcounter)+'.'+str(secparcounter)] = "t"+item.split("_")[0]
                secparcounter += 1

