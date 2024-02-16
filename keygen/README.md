## For User 
 before update keys, you need to install some modules:

``pip install dataclasses_json``

Now just update some certain files and run main.py to update keys.json

## For Editor
If you want your game support decryption, please do as below:
1. Create a folder under this directory with the name of the game


2. Create a script named get_keys.py, which contains the function __get_keys__


3. __get_keys__ function must return audio encryption mode and keys dict(video name: key). In audio encryption mode, 0 stand for no encryption, 1 for USM encryption and 2 for HCA encryption(not supported yet).


3. You can add necessary files to the game folder.
