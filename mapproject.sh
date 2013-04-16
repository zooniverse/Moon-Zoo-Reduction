
# Convert to calibrated ISIS cubes if necessary

lronac2isis from=M101949648LE.IMG to=M101949648LE.cub
lronaccal from=M101949648LE.cub to=M101949648LE.cal.cub
spiceinit from=M101949648LE.cal.cub

lronac2isis from=M101949648RE.IMG to=M101949648RE.cub
lronaccal from=M101949648RE.cub to=M101949648RE.cal.cub
spiceinit from=M101949648RE.cal.cub

camrange from=M101949648LE.cal.cub to=M101949648LE.camrange
camrange from=M101949648RE.cal.cub to=M101949648RE.camrange

# select suitable projection, metres per pixel resolution, and any additional parameters by inspecting
# the PixelResolution and UniversalGroundRange groups in the outputs of camrange.
# Most projections require central longitude and latitudes (clon, clat)
# The Lambert Conformal appears to be the currently preferred projection for small regions.
# This requires two standard parallels to be specified, which span the latitude range of interest.

#maptemplate map=M101949648.map projection=mercator clon=30.5 clat=20.0 resopt=MPP resolution=1.4
maptemplate map=M101949648.map projection=lambertconformal clon=30.5 clat=20.0 par1=18.5 par2=21.5 resopt=mpp resolution=1.4

# This takes a while...
cam2map from=M101949648LE.cal.cub to=M101949648LE.map.cub map=M101949648.map pixres=map
cam2map from=M101949648RE.cal.cub to=M101949648RE.map.cub map=M101949648.map pixres=map

ls M101949648*map.cub > moslist.txt

automos fromlist=moslist.txt mosaic=M101949648.automos.cub

# Alterntaively blend the image overlap region before mosaicking
blend fromlist=moslist.txt
ls M101949648*blend.cub > blendmoslist.txt
automos fromlist=blendmoslist.txt mosaic=M101949648.blend.cub

# This is a possible alternative to blend and automos:
#noseam from=moslist.txt to=M101949648.noseam.cub
