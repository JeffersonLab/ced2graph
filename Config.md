# The ced2gnn Configuration File

The default name for the configuration file is config.yaml.  Its contents are discussed below on a section-by-section basis.

## CED Parameters

The ced block of the config specifies paramters that will be used to query the [CEBAF Element Database](https://ced.acc.jlab.org/)
to build a list of beamline elements.  For brevity the query may specifiy a superset of the element types which will actually be 
used to represent readbacks and setpoints (For example, fetching all BeamElem elements even though perhaps only Magnet and 
BPM will actually be used). 

```yaml
##################################################################################################################
# CED
#
# Here you specify the parameters for gathering data from the CEBAF Element Database (CED)
#
#  history: Set true in order to query CED history instance, otherwis OPS instance is used
#  workspace: Workspace/Date to query.  Default is OPS/now
#  zone: The name of a CED zone
#
#  types: A list of types to retrieve. Can simply use BeamElem or LineElem and rely on CED inheritance.  Must 
#         choose types that all have S and EPICSName property as well as any specified extra properties.
#         Not every retrieved type of element will necessarily be used.  
#         Which elements will be used as graph nodes is determined in the nodes block of the config file.  
#
#  properties: A list of properties to fetch in addition to default EPICSName and S which are hard-coded.
#              Any extra properties specified must be applicable to all retrieved types.
#
#  expressions: A list of CED property expressions. See CED command line help for details about available options.
#       Example: S >= 6.65657  # skip over elements in the front of the MFA0I03 S Value
#       Example: '!isSRF'      # Only retrieve elements whose is isSRF property is false or null
#
ced:
  history: true           # Optional.  Default is false meaning use OPS ced.
  workspace: '2021-12-15' # Optional.  Default is OPS workspace/current timestamp
  zone: "Injector"        # Required.  See https://ced.acc.jlab.org/zones/
  types: ["LineElem"]     # Required.  See https://ced.acc.jlab.org/catalog/
  properties: []          # Optional.  Specify properties in addition to default EPICSName and S
  expressions:
    - S >= 6.65657  # skip over elements in the front of the MFA0I03 S Value
    - S <= 101.58   # So that ILM0R08 is final element
```

## Node Parameters

The node block settings largely govern how the inventory of CED elements will be represented as graph nodes.

A master node may also optionally be specified.  When specified, it does not come from CED, but consists of a subset
list of signals from the global attribute in the mya section of settings.

```yaml
##################################################################################################################
# Nodes
#
# Here you specify information about the nodes that will be generated from the CED data.
#
# master:     List signals from the mya.global list to define attributes of a master node
# setpoints:  List CED types whose elements are to be considered setpoints and their desired EPICS fields
# readgacks:  List CED types whose elements are to be considered readbacks and their desired EPICS fields
#
# default_attributes:  Specify a label for node properties derived from the empty ("") EPICS field name
#
# modifiers:  Provide calculation expressions that will be used to manipulate data retrieved from the archiver.
#             This might be useful to normalize data taken from elements that record data at differeing scales.
#             To the left of the colon is the PV to be modified.  To the right is the expression with the PV
#             name included in EDM macro syntax $(PV)
#
# filter:    A filter expression to govern whether data for a given time interval is valid (i.e. was the beam on?).
#            Only time intervals for which the filter returns True will be written to output files.
#

nodes:

  master:
    - IBC0L02Current     # must also be present in mya.global

  setpoints:
    Corrector: [".BDL", ".S"]
    Dipole: [".BDL", ".S"]
    Quad: [".BDL", ".S"]
    Solenoid: [".BDL", ".S"]

    # Note XPSET8 below actually belongs to a zone and not the cavity.
    # Special handling for this case has been hard-coded into the node module.
    CryoCavity: ['PSET','GSET','XPSET8']

    # Because the types below will be matched in the order listed, we can provide
    # special PV list for the Capture and then let the catch-all WarmCavity
    # handle PreBuncher, Buncher, Chopper, etc.
    Capture: ['PSET','GSET']
    WarmCavity: ['PSET','GSET','Psum']

  readbacks:
    BeamLossMonitor: ["Lc"]
    BPM: [".XPOS", ".YPOS", ""] # The "" is to give us a bare EPICSName which means the wire sum
    IonPump: [""]               # The "" is the vacuum readback
    BCM: [""]                   # node module must handle special cases

  default_attributes:
    BCM: "Current"      # The bare EPICSName of a BCM gives us its Current
    BPM: "WireSum"      # The bare EPICSName of a BPM is its WireSum
    IonPump: "Vacuum"   #

  modifiers:
    # Certain Ion Pumps in the injector need to be scaled differently based on their hardware type
    # and how many pumps are ganged together to provide the voltage being read.  The calculations below
    # are from a spreadsheet compiled by Dan Moser.
    VINJDIG07: "0.066 * $(VINJDIG07) * 0.000001 *((5600/5600)/80)"
    VINJDIG02: "0.066 * $(VINJDIG02) * 0.000001 *((5600/5600)/120)"
    VINJDIG03: "0.066 * $(VINJDIG03) * 0.000001 *((5600/5600)/102)"
    VINJDIG04: "0.066 * $(VINJDIG04) * 0.000001 *((5600/5600)/160)"
    VINJDIG12: "0.066 * $(VINJDIG12) * 0.000001 *((5600/5600)/45)"
    VINJDIG08: "0.066 * $(VINJDIG08) * 0.000001 *((5600/5600)/30)"
    VINJDIG05: "0.066 * $(VINJDIG05) * 0.000001 *((5600/5600)/120)"
    VINJDIG06: "0.066 * $(VINJDIG06) * 0.000001 *((5600/5600)/120)"
    VIP0L08:   "0.066 * $(VIP0L08) * 0.000001 *((5600/5000)/11)"
    VIP0L10:   "0.066 * $(VIP0L10) * 0.000001 *((5600/5000)/11)"
    VIP0R02:   "0.066 * $(VIP0R02) * 0.000001 *((5600/5000)/22)"
    VIP0R04:   "0.066 * $(VIP0R04) * 0.000001 *((5600/5000)/11)"
    VIP0R06:   "0.066 * $(VIP0R06) * 0.000001 *((5600/5000)/11)"
    VIP0R08:   "0.066 * $(VIP0R08) * 0.000001 *((5600/5000)/11)"
    VIP0R09:   "0.066 * $(VIP0R09) * 0.000001 *((5600/5000)/11)"

   # The filter expression below may use EPICS Macro variable syntax to reference PVs from the mya.global
   # secion of this config file
  filter: "$(IBC0L02Current) > 0.1"

```

## Mya Parameters

The mya block settings specifies the dates and times for which data will be fetched from the mya archiver.  It also 
permits the specification of global (i.e. not node-specific) PVs to fetch for each time sample.  These global PVs may be
used for filtering purposes.  For example fetching a BCM readback whose value can be used to determine if there was
beam in a particular segment of the machine at the time in question.

```yaml
##################################################################################################################
# Mya
#
# Here you specify information that will govern fetching of data from the mya archiver.
#
# deployment:
#   Which mya deployment to use (history or ops).  Deployment "history" should suffice in most situations. It contains
#   data going back much further (~10 years) than the ops deployment (~2 years).  However the history
#   deployment only gets refreshed at the first of each month, so any more recent data must come from ops.
#
# throttle:
#   Sets the max number of data points to be fetched from the archiver web api in a single HTTP request.
#   The web server will timeout if a request takes too long to complete.
#
# dates:
#   begin: The start of the date range to fetch (YYYY-MM-DD [HH:MM:SS])
#   end: The end of the date range to fetch (YYYY-MM-DD [HH:MM:SS])
#   interval: An interval specifier ('1h' = 1 hour, '1d' = 1 day, etc.)
#   Example -
#     begin: "2021-01-01"
#     end: "2021-12-15"
#     interval: "1h"
#
#   -- OR --
#
# dates: "filename"
#   where filename contains either singe timestamp per line or a comma-separated begin,end,interval triplet per line
#   Example -
#     2021-01-01, 2021-02-01, 1h
#     2022-01-01, 2022-01-15, 1h
#     ...
#
# global:
#   A list of global signal names to be fetched at each time interval.  These values may be referenced as
#   variables in node.filter.

mya:
  deployment: "history"
  throttle: 2500
  dates:
    begin: "2021-09-01"
    end: "2021-09-30"
    interval: "1d"
  global:
    - ISD0I011G
    - BOOMHLAMODE
    - BOOMHLBMODE
    - BOOMHLCMODE
    - BOOMHLDMODE
    - IBC0L02Current
    - IBC0R08CRCUR1
    - IBC1H04CRCUR2
    - IBC2C24CRCUR3
```

## Edge parameters

The edge paramters govern how the contents of the link.dat files will be produced.

```yaml
##################################################################################################################
# Edges
#
# Here you specify information that will govern construction of edge features
#
#  connectivity: each readback node will be connected to to the intervening setpoint and readback nodes up until the nth
#                readback node, where n = edges.connectivity.
#  directed:  true if edges are considered unidirectional
#  weighted : if true, edges will be weighted using 1/(S[2]-S[1])

edges:
  connectivity: 2
  directed: true      # Probably stays true since the beam is directional
  weighted: false     # If false, all weights will be 1

```