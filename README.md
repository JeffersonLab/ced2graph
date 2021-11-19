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
# Run the script
python3 main.py
```
It's a work in progress, so the output is probably just some scratch data at the moment:

```
[52] theo@devl77 > python3 main.py
[{'MQW1I03.BDL': '3'}, {'MQW1I03.S': '0.221386'}]
[{'MQW1I04.BDL': '0'}, {'MQW1I04.S': '-0'}]
[{'MQW1I05.BDL': '-8'}, {'MQW1I05.S': '-0.590362'}]
[{'MQW1I06.BDL': '-3'}, {'MQW1I06.S': '-0.221386'}]
[{'MQS0I07.BDL': '0'}, {'MQS0I07.S': '3.85376e-09'}]
[{'R027PMES': '3.6'}, {'R027GMES': '5.256'}]
[{'R028PMES': '60.2'}, {'R028GMES': '5.279'}]
[{'MQS0L01.BDL': '-4'}, {'MQS0L01.S': '-0.296516'}]
[{'MQJ0L01.BDL': '1.19332e-06'}, {'MQJ0L01.S': '-0.0498252'}]
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

