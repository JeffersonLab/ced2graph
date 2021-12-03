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
It's a work in progress, so the output is probably just some scratch data at the moment:
Which may or may not look anything like the example below.
```
2021-11-01T11:00:00      0      MFA0I03 Solenoid         6.6565725      243.994 1394.25
2021-11-01T11:00:00      1      MBH0I03H        Corrector        6.8629475      -16.5   -92.4888
2021-11-01T11:00:00      2      MBH0I03V        Corrector        6.8629475      10      70.2247
2021-11-01T11:00:00      3      MFD0I04 Solenoid         7.3768604      60.619  0.747
2021-11-01T11:00:00      4      MFD0I04A        Solenoid         7.5483104      60.619  0.747
2021-11-01T11:00:00      5      MBH0I04H        Corrector        7.9520233      -19     -106.502
2021-11-01T11:00:00      6      MBH0I04V        Corrector        7.9520233      2.2     15.4494
2021-11-01T11:00:00      7      MFA0I05 Solenoid         8.2250733      271.998 1554.27
2021-11-01T11:00:00      8      IPM0I05 BPM      8.453410847612 62.144  -2.66561        -1.81257
2021-11-01T11:00:00      9      MBH0I05H        Corrector        8.454089347612 3.6     20.1794
2021-11-01T11:00:00      10     MBH0I05V        Corrector        8.454099347612 15.8    110.955
...
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
