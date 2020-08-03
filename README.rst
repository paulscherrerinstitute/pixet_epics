This is a PCASpy server to integrate Medipix detectors, using Pixet Python API.

1. Inside the Python Scripting window,  select menu *File* -> *Install python module*.
   Type *pcaspy* and click Ok.

2. Still inside the Python Scripting window, open the *epics_server.py* file and
   select menu *Script* -> *Run Script*.

3. Open the medm panel,::

   $ medm -x -macro P=13PIXET:,R=cam1: Pixet.adl

4. The data can be retrieved,::

   $ caget 13PIXET:cam1:ArrayData

5. Stop the server before quit, select menu *Script* -> *Stop Script*.
