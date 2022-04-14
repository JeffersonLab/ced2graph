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
  --read-json     Read data from tree.json, nodes.json, and global.json instead of CED and Mya
  --save-json     Save fetched data in tree.json, nodes.json, and global.json

```
Example:

```
% PATH /usr/csite/pubtools/python/3.7/bin:$PATH
% python3 main.py
Fetch Data: |##################################################| 100.0%
Write Files: |##################################################| 100.0%
```
### Config File
Execution of the program is governed by parameters supplied via YAML format configuration file. 
The default name for the file is config.yaml, however this may be over-ridden on the command line using the -c flag.
For details about what may be specified in the config file see [Config.md](Config.md) and the comments in the 
included [config.yaml](config.yaml).   

## File Output

### Error Messages
Non-fatal warnings generated during program get written to the log file *warnings.log*.

### Data Directory Structure
Data is written to a date and time-based hiearchy of files anchored as illustrated below:

```
2021 # Year
|-- 01 # Day
|   |-- 03 # Hour  - Note Missing 01 and 03 hours were excluded by filter (IBC0R08CRCUR1 > 0)
|   |   |-- 02
|   |   |   |-- info.dat
|   |   |   |-- link.dat
|   |   |   |-- meta.dat
|   |   |   `-- node.dat
|   |   |-- 04
|   |   |   |-- info.dat
|   |   |   |-- link.dat
|   |   |   |-- meta.dat
|   |   |   `-- node.dat

```
Note that the config file allows you to specify if the hierarchy should be exntended down to minutes and seconds.
If minutes or seconds are not set, then only one set of data files will be generated for the hour or minute and the 
remainder will be discarded.

```yaml
##################################################################################################################
# Output
#
# Here you specify options that will govern output and its directory structure
#
# minutes:  if true then two digit minutes subdirectories will be created beneath hour
# seconds:  if true, then two digit seconds subdirectories will be created beneath minutes
#           Note: if seconds is true, then minutes will automatically also be regarded as true
#
output:
  minutes: true
  seconds: true
```
### Output Files
Within each output directory is a data set consisting of four files.

#### node.dat
The ordered list of nodes with comma-separate list of attribute values.
The label for the value in the TYPE column is defined info.dat as are
the labels for data in the VALUES column.
```
NODE    NAME            TYPE    VALUES
0       MFA0I03          0       6.6565725,243.994,1394.25
1       CHOP1Y           1       6.75976,<undefined>,86.9,61.9
2       CHOP1X           1       6.8629475,<undefined>,90,65
3       MBH0I03H         2       6.8629475,-16.5,-92.4888
4       MBH0I03V         2       6.8629475,10,70.2247
5       VIP0I03          3       7.2314509996126,0.0
6       MFD0I04          0       7.3768604,60.619,0.747
7       MFD0I04A         0       7.5483104,60.619,0.747
...
```

#### info.dat
The labels for types and attributes.
```
TYPE     NAME           LABELS
0        Solenoid       S,.BDL,.S
1        WarmCavity     S,GSET,PSET,Psum
2        Corrector      S,.BDL,.S
3        IonPump        S,Vacuum
4        BPM            S,WireSum,.XPOS,.YPOS
...
```

#### link.dat
The edges that connect the nodes.
```
START   END     LINK_TYPE     LINK_WEIGHT
0        1       0            1
0        2       0            1
0        3       0            1
0        4       0            1
0        5       0            1
0        6       0            1
1        2       0            1
1        3       0            1
1        4       0            1
1        5       0            1
1        6       0            1
1        7       0            1
2        3       0            1
...
```


#### meta.dat
The counts for each type of node in the data set.
```
Total Nodes:     206
Node_Type_0:     6
Node_Type_1:     5
Node_Type_2:     56
Node_Type_3:     49
Node_Type_4:     21
Node_Type_5:     2
Node_Type_6:     6
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



## TODO
 * Evaluate filter expression(s) from config file rather than hard-code IBC0R08 > 0
 * Add extra 01X hour if necessary during DST/EST transition
 * ~~Write out meta.dat files~~
 * ~~Convert type to type_id in node.dat, info.dat~~
 * ~~Make Edge links to nth readback node for n > 1~~
 * Progress bar during global data fetch (a long pause for large data sets)  
 * Test against longer date ranges
   * ~~2021-01-01 thru 2021-12-06 took about 15 minutes for element data but bombed on global~~
   * ~~Probably need to break large archiver requests into (month-sized?) chunks~~  
 * Use a timestamp directory name instead of . by default
 


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
