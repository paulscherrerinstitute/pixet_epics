This is a PCASpy server to integrate Medipix detectors, using Pixet Python API.

1. Pixet 1.7.1 has Python 3.7 embedded. So download pcaspy package
   *pcaspy-0.7.2-py3.7-linux-x86_64.egg* from https://pypi.org/project/pcaspy/#files
   and unzip it under *PIXET/libs/python3.7/site-packages*.

2. Now start Pixet and select menu *Tool* -> *Python Scripting*.
   Inside the Python Scripting window, open the *epics_server.py* file and
   select menu *Script* -> *Run Script*.

3. Open the medm panel,::

   $ medm -x -macro P=13PIXET:,R=cam1: Pixet.adl

4. The data can be retrieved,::

   $ caget 13PIXET:cam1:ArrayData

5. Stop the server before quit, select menu *Script* -> *Stop Script*.
