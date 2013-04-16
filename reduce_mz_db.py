from tables import *
import os, time
from string import strip
import numpy
import csv

datapath = '/mnt/moonzoo/'

rnames = ['annotation_id', 'classification_id', 'task_id', 'answer_id', 'nac_name', 'asset_id', 'name',
          'asset_created_at', 'value', 'x_min', 'x_max', 'y_min', 'y_max', 'parent_trim_left', 'parent_trim_right',
          'zoom', 'resolution', 'longitude', 'latitude', 'transfo', 'parent_image_width', 'parent_image_height',
          'zooniverse_user_id', 'classification_created_at', 'time_spent']

def make_hdf5():
    filters = Filters(complevel=1, complib='blosc')
    with openFile(os.path.join(datapath, 'mz_results.h5'), mode = "w",
                         title = "MZResults", filters=filters) as h5file:
        crater_results = file(os.path.join(datapath, 'mz_results_craters.csv'))
        crater_table = h5file.createTable('/', 'craters', MZCrater, "Moon Zoo raw craters")
        crater = crater_table.row
        for i, r in enumerate(crater_results):
            for j, v in enumerate(r.split(',')):
                try:
                    if rnames[j]=='value':
                        if 'No craters' in v:
                            continue
                        for i in range(1,8):
                            vname, value = (strip(x) for x in v.split('|')[i].split(':'))
                            crater[vname] = value.replace('\\', '').replace('"', '')
                    elif 'created_at' in rnames[j]:
                        crater[rnames[j]] = time.mktime(time.strptime("2010-05-11 13:06:03", "%Y-%m-%d %H:%M:%S"))
                    else:
                        crater[rnames[j]] = v.replace('"', '')
                except TypeError:
                    pass
                except ValueError:
                    print 'ValueError:', j, rnames[j], v
            crater.append()
        crater_table.flush()
        h5file.flush()
        region_results = file(os.path.join(datapath, 'mz_results_regions.csv'))
        region_table = h5file.createTable('/', 'regions', MZRegion, "Moon Zoo raw regions")
        region = region_table.row
        for i, r in enumerate(region_results):
            for j, v in enumerate(r.split(',')):
                try:
                    if rnames[j]=='value':
                        if 'No regions' in v:
                            continue
                        for i in range(1,7):
                            vname, value = (strip(x) for x in v.split('|')[i].split(':'))
                            region[vname] = value.replace('\\', '').replace('"', '')
                    elif 'created_at' in rnames[j]:
                        region[rnames[j]] = time.mktime(time.strptime("2010-05-11 13:06:03", "%Y-%m-%d %H:%M:%S"))
                    else:
                        region[rnames[j]] = v.replace('"', '')
                except TypeError:
                    pass
                except ValueError:
                    print 'ValueError:', j, rnames[j], v
            region.append()
        region_table.flush()
        h5file.flush()



def untransform_craters():
    h5file = openFile(os.path.join(datapath, 'mz_results.h5'), mode = "a")
    t = h5file.root.craters

    x_min = t.cols.x_min
    y_min = t.cols.y_min
    zoom = t.cols.zoom
    x = t.cols.x
    y = t.cols.y
    xtranac = t.cols.xtranac
    ytranac = t.cols.ytranac
    
    expr = Expr('x_min + x * zoom + (zoom-1)/2.0')
    expr.setOutput(xtranac)
    expr.eval()

    expr = Expr('y_min + y * zoom + (zoom-1)/2.0')
    expr.setOutput(ytranac)
    expr.eval()

    xd = t.cols.x_diameter
    yd = t.cols.y_diameter
    xdnac = t.cols.x_diameter_nac
    ydnac = t.cols.y_diameter_nac

    expr = Expr('xd * zoom')
    expr.setOutput(xdnac)
    expr.eval()

    expr = Expr('yd * zoom')
    expr.setOutput(ydnac)
    expr.eval()

    ltrim = t.cols.parent_trim_left
    rtrim = t.cols.parent_trim_right
    width = t.cols.parent_image_width
    height = t.cols.parent_image_height
    transfo = t.cols.transfo
    xnac = t.cols.xnac
    ynac = t.cols.ynac

    expr = Expr('where(transfo % 2 == 0, xtranac + ltrim, xtranac + rtrim)')
    expr.setOutput(xnac)
    expr.eval()

    expr = Expr('where(transfo < 2, ytranac, height - ytranac)')
    expr.setOutput(ynac)
    expr.eval()

    # the angle should be transformed too, but I'm not sure how it is defined.

    h5file.close()


def untransform_regions():
    h5file = openFile(os.path.join(datapath, 'mz_results.h5'), mode = "a")
    t = h5file.root.regions

    x_min = t.cols.x_min
    y_min = t.cols.y_min
    zoom = t.cols.zoom
    x = t.cols.x
    y = t.cols.y
    xtranac = t.cols.xtranac
    ytranac = t.cols.ytranac
    
    expr = Expr('x_min + x * zoom + (zoom-1)/2.0')
    expr.setOutput(xtranac)
    expr.eval()

    expr = Expr('y_min + y * zoom + (zoom-1)/2.0')
    expr.setOutput(ytranac)
    expr.eval()

    xd = t.cols.width
    yd = t.cols.height
    xdnac = t.cols.width_nac
    ydnac = t.cols.height_nac

    expr = Expr('xd * zoom')
    expr.setOutput(xdnac)
    expr.eval()

    expr = Expr('yd * zoom')
    expr.setOutput(ydnac)
    expr.eval()

    ltrim = t.cols.parent_trim_left
    rtrim = t.cols.parent_trim_right
    width = t.cols.parent_image_width
    height = t.cols.parent_image_height
    transfo = t.cols.transfo
    xnac = t.cols.xnac
    ynac = t.cols.ynac

    expr = Expr('where(transfo % 2 == 0, xtranac + ltrim, xtranac + rtrim)')
    expr.setOutput(xnac)
    expr.eval()

    expr = Expr('where(transfo < 2, ytranac, height - ytranac)')
    expr.setOutput(ynac)
    expr.eval()

    # the angle should be transformed too, but I'm not sure how it is defined.

    h5file.close()


def h5tocsv():
    h5file = openFile(os.path.join(datapath, 'mz_results.h5'))
    writer = csv.writer(open(os.path.join(datapath, 'mz_craters.csv'), 'wb'))
    writer.writerow(h5file.root.craters.colnames)
    for row in h5file.root.craters:
        writer.writerow(row[:])
    writer = csv.writer(open(os.path.join(datapath, 'mz_regions.csv'), 'wb'))
    writer.writerow(h5file.root.regions.colnames)
    for row in h5file.root.regions:
        writer.writerow(row[:])
    h5file.close()


class MZCrater(IsDescription):
    annotation_id = UInt64Col(pos=1)
    classification_id = UInt64Col(pos=2)
    task_id = UInt64Col(pos=3)
    answer_id = UInt64Col(pos=4)
    nac_name = StringCol(16, pos=5)
    asset_id = UInt64Col(pos=6)
    name = StringCol(64, pos=7)
    asset_created_at = Float64Col(pos=8)
    x_min = UInt32Col(pos=9)
    x_max = UInt32Col(pos=10)
    y_min = UInt32Col(pos=11)
    y_max = UInt32Col(pos=12)
    parent_trim_left = UInt32Col(pos=13)
    parent_trim_right = UInt32Col(pos=14)
    zoom = Float64Col(pos=15)
    resolution = Float64Col(pos=16)
    longitude = Float64Col(pos=17)
    latitude = Float64Col(pos=18)
    transfo = UInt8Col(pos=19)
    parent_image_width = UInt32Col(pos=20)
    parent_image_height = UInt32Col(pos=21)
    zooniverse_user_id = UInt64Col(pos=22)
    classification_created_at = Float64Col(pos=23)
    time_spent = Int32Col(pos=24)
    id = UInt32Col(pos=25)
    x = Float64Col(pos=26)
    y = Float64Col(pos=27)
    x_diameter = Float64Col(pos=28)
    y_diameter = Float64Col(pos=29)
    angle = Float64Col(pos=30)
    boulderyness = Float64Col(pos=31)
    xtranac = Float64Col(pos=32)
    ytranac = Float64Col(pos=33)
    xnac = Float64Col(pos=34)
    ynac = Float64Col(pos=35)
    x_diameter_nac = Float64Col(pos=36)
    y_diameter_nac = Float64Col(pos=37)
    angle_nac = Float64Col(pos=38)


class MZRegion(IsDescription):
    annotation_id = UInt64Col(pos=1)
    classification_id = UInt64Col(pos=2)
    task_id = UInt64Col(pos=3)
    answer_id = UInt64Col(pos=4)
    nac_name = StringCol(16, dflt="", pos=5)
    asset_id = UInt64Col(pos=6)
    name = StringCol(64, dflt="", pos=7)
    asset_created_at = Float64Col(pos=8)
    x_min = UInt32Col(pos=9)
    x_max = UInt32Col(pos=10)
    y_min = UInt32Col(pos=11)
    y_max = UInt32Col(pos=12)
    parent_trim_left = UInt32Col(pos=13)
    parent_trim_right = UInt32Col(pos=14)
    zoom = Float64Col(pos=15)
    resolution = Float64Col(pos=16)
    longitude = Float64Col(pos=17)
    latitude = Float64Col(pos=18)
    transfo = UInt8Col(pos=19)
    parent_image_width = UInt32Col(pos=20)
    parent_image_height = UInt32Col(pos=21)
    zooniverse_user_id = UInt64Col(pos=22)
    classification_created_at = Float64Col(pos=23)
    time_spent = Int32Col(pos=24)
    id = UInt32Col(pos=25)
    x = Float64Col(pos=26)
    y = Float64Col(pos=27)
    width = Float64Col(pos=28)
    height = Float64Col(pos=29)
    selection_type = StringCol(8, dflt="", pos=30)
    xtranac = Float64Col(pos=31)
    ytranac = Float64Col(pos=32)
    xnac = Float64Col(pos=33)
    ynac = Float64Col(pos=34)
    width_nac = Float64Col(pos=35)
    height_nac = Float64Col(pos=36)
    angle_nac = Float64Col(pos=37)


class MZBoulder(IsDescription):
    annotation_id = UInt64Col()
    classification_id = UInt64Col()
    task_id = UInt64Col()
    answer_id = UInt64Col()
    nac_name = StringCol(16, dflt="")
    asset_id = UInt64Col()
    name = StringCol(64, dflt="")
    asset_created_at = Float64Col()
    x_min = UInt32Col()
    x_max = UInt32Col()
    y_min = UInt32Col()
    y_max = UInt32Col()
    parent_trim_left = UInt32Col()
    parent_trim_right = UInt32Col()
    zoom = Float64Col()
    resolution = Float64Col()
    longitude = Float64Col()
    latitude = Float64Col()
    transfo = UInt8Col()
    parent_image_width = UInt32Col()
    parent_image_height = UInt32Col()
    zooniverse_user_id = UInt64Col()
    classification_created_at = Float64Col()
    time_spent = Int32Col()
    asset_id1 = UInt64Col()
    asset_id2 = UInt64Col()
    winner = UInt8Col()

if __name__ == "__main__":
    make_hdf5()
    untransform_craters()
    untransform_regions()
    h5tocsv()
