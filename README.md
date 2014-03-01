# Moon Zoo Reduction

This is a set of scripts used in reducing the Moon Zoo dataset.

Note that Moon Zoo is based on the old Juggernaut MySQL database
structure.  Obviously many of the scripts have aspects that are
specific to the Moon Zoo dataset and LROC imaging.  However, the
overall approach and more general pieces of the code should be useful
for other projects.

Note that a lot of effort has been put into making clustering with a
custom metric fast in Python.  To do this I have used Cython to
optimise key parts of the code, resulting in a speedup factor of
over 100.  This may be very useful for projects with similar custom
clustering requirements.

## Usage

This reduction is usually performed on an AWS EC2 instance, although
it should work on any suitably configured Linux machine.  The scripts
assume a freshly created instance of a vanilla Ubuntu AMI and
reduce\_mz\_db.sh installs all the software required.  A large
instance is recommended, but not essential, however note that in
reduce\_mz\_db.sh a msql conguration file is installed, and this must
correspond to the available memory.

## What it does

See reduce\_mz\_db.sh for more details.  This script first configures
the machine, then downloads the required database dumps, imports them
into mysql, runs some mysql reduction steps and outputs the results to
csv.  A python script then continues the reduction, parsing the
feature marking information and producing another set of csv files,
which are then re-imported into the mysql database.  Next, ISIS is
used to convert the image coordinates to lunar latitude and longitude.
Finally, a fast friends-of-friends clustering algorithm can be run on
specified regions, to produce aggregated crater catalogues, along with
a some useful plots.  If a 'truth' set of craters is supplied, then
the resulting craters are compared to the 'truth' and more plots and
statistics produced.

## Issues

There are a variety of customisable parameters (some hardcoded), and a
final setup for the Moon Zoo data has not yet been decided upon.  Note
that an alternative approach to aggregating the markings to produce a
final crater catalogue has been developed by the Manchester machine
vision group, which may well supercede the fairly simple approach
taken here.

The whole process could be refactored to make it more efficient,
without jumping between langauages and file formats.

The conversion of the coordinates is slow as the ISIS routine campt
only operates on one point at a time.  A bit of C coding to address
this, or perhap use of IDL ISIS routines, would speed this up.

