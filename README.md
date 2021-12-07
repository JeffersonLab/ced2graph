# ced2gnn
Script and supporting modules to extract data from CEBAF Element Database (CED) and the Mya archiver and output it in a format useful for generating graph neural networks.

## Usage
Since the tools have been written to use web API for both CED and Mya, it is not a requirement that they be executed from an accelerator workstation.  Any computer with python3 and the necessary modules that has access to https://ced.acc.jlab.org and https://myaweb.acc.jlab.org should be capable of using them.  However as a baseline example, running from an ACE linux host is outlined.

```csh
# Clone the repository into your home directory
cd ~
git clone https://github.com/JeffersonLab/ced2gnn.git
# Specify a version of python3 in pubtools that has necessary modules
setenv PATH /usr/csite/pubtools/python/3.7/bin:$PATH

# Run the script with -h or --help to see available arguments
python3 main.py --help

usage: main.py [-h] [-c CONFIG_FILE] [-d OUTPUT_DIR] [-o] [--read-json] [--save-json]

Command Line Options

optional arguments:
  -h, --help      show this help message and exit
  -c CONFIG_FILE  Name of a yaml formatted config file
  -d OUTPUT_DIR   Directory where generated graph file hierarchy will be written
  -o              Overwrite existing files
  --read-json     Read data from tree.json, nodes.json, and global.json instead of CED and Mya
  --save-json     Save fetched data in tree.json, nodes.json, and global.json

```
Example:

```
theo@devl77 > python3 main.py
setenv PATH /usr/csite/pubtools/python/3.7/bin:$PATH
Fetch Data: |##################################################| 100.0%
Write Files: |##################################################| 100.0%
```


## Tests
To run the test suite:

```csh
# Clone the repository into your home directory
cd ~
git clone https://github.com/JeffersonLab/ced2gnn.git
# Specify a version of python3 in pubtools that has necessary modules
setenv PATH /usr/csite/pubtools/python/3.7/bin:$PATH
# Run the tests
python3 tests.py
```

Example output:

```
[53] theo@devl77 > python3 tests.py
============================= test session starts ==============================
platform linux -- Python 3.7.6, pytest-6.2.5, py-1.11.0, pluggy-1.0.0
rootdir: /a/csmuser/theo/ced2gnn/tests
collected 4 items

test_ced.py ...                                                          [ 75%]
test_mya.py .                                                            [100%]

============================== 4 passed in 0.53s ===============================
```


## Developer Notes
During development it is nice (and faster) to be able to work offline without constantly fetching data 
from the CED and archiver.  To do so, follow these steps.

While connected to a network with access to ced and mya web servers:
```
python3 main.py --save-json
```

Thereafter, to use the saved data, simply run
```
python3 main.py --read-json
```

Note that if the config changes after the --save-json execution, it's possible that it will become 
incompatible with the saved files and generate errors or unexpected results when --read-json is used.
