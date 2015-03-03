# So apparently you have two mpl_toolkits installations, but only one has 
# Basemaps. Python didn't search this mpl_toolkits first, and so failed to find
# Basemaps. Your crappy solution was to cp the 'basemap' directory directly 
# into the mpl_toolkits without basemap. This works, but it means software 
# updates for basemaps won't be automatically propagated. 
from mpl_toolkits.basemap import Basemap
from matplotlib.collections import LineCollection
import matplotlib.pyplot as plt  
from matplotlib import cm
import matplotlib as mpl
import pandas as pd
import numpy as np
import utils
# Non-mpl GIS software
import shapefile  
import pyproj

colors = ['#E24A33', '#348ABD', '#988ED5', '#777777', '#FBC15E', '#8EBA42', 
          '#FFB5B8']

##### Coordinate transformations #####
# The shapefiles you got from the City of Chicago Open Data site do not contain
# latitude and longitude points. Rather they contain relative measurements (in
# feet) using a predeterminted projection. Projections are very numerous and
# complicated, but the distinguishing details can be found in the .prj files.
#
# In order to get lat/lon coorindates (the preferred values for Basemap), we 
# must transform coordinates from the city's projection. You successfully
# managed to transform a coodinate using information from the following
# StackExchange posts:
#
#http://gis.stackexchange.com/questions/10209/converting-x-y-coordinates-to-lat-long-using-pyproj-and-proj-4-returns-the-wrong
#http://gis.stackexchange.com/questions/118215/proj4-string-for-nad832011-louisiana-south-ftus
#
# One key thing to remember is that the Chicago values are in feet, and PyProj
# always defaults to using meters, even if you pass it an EPSG code or Proj4
# string that indicates that your projection is in feet. You must pass the 
# "preserve_units=True" argument to PyProj in order for it to interpret your
# input coordinates from the city as being in feet.
######################################


def alderman_dict(sfile):
    '''
    Given the ward shapefile, return a dictionary with key = ward #, 
    value = alderman's name.
    '''
    aldermandict = {}
    for rec in sfile.records():
        if rec[2] != 'OUT':
            aldermandict[int(rec[2])] = rec[3]
        
    return aldermandict


def draw_chicago(projection='merc', resolution='i',ax=plt.gca()):
    '''
    Create and return Chicago Basemap upon which wards will be plotted.
    '''
    # Chicago corners
    urcornerlat = 42.03 
    urcornerlong = -87.51 
    llcornerlat = 41.64
    llcornerlong = -87.95
  
    m = Basemap(projection=projection, resolution=resolution,
                llcrnrlat=llcornerlat, urcrnrlat=urcornerlat, 
                llcrnrlon=llcornerlong, urcrnrlon=urcornerlong, ax=ax)
    m.drawmapboundary()

    return m


def precinct_frac(resultdf, record, candidate='RAHM EMANUEL', verbose=False):
    '''
    Color code a precinct by Rahm's fraction of the vote. 
    Make this more general by making a coloring class, perhaps?
    '''
    ward, precinct = record[0], record[1]
    row = resultdf[(resultdf['Ward']==ward) & (resultdf['Precinct']==precinct)]
    if row.empty:
        if verbose: 
            print 'Empty row for ward: %s  precinct: %s' % (ward, precinct)
        return -1        
    else:
        return float(row[candidate])/row['Votes Cast']


def create_line_segments(chimap, sfile, proj4string, color=True, 
                         precincts=False, ax=plt.gca()):
    '''
    Takes a shapefile and Proj4 projection string and adds line segments 
    demarcating ward and/or precinct boundaries to the plot axis. Roughly 
    follows example of:
    http://nbviewer.ipython.org/github/rjtavares/numbers_arent_people/blob/master/experiments/Plotting%20with%20Basemap%20and%20Shapefiles.ipynb
    '''
    # Initialize input projection, as specified by Proj4 string.
    inproj = pyproj.Proj(proj4string, preserve_units=True)
    # From gis.StackExchange: "WGS84 comprises a standard coordinate frame for
    # the Earth, a datum/reference ellipsoid for raw altitude data, and a 
    # gravitational equipotential surface (the geoid) that defines the nominal 
    # sea level. '4326' is just the EPSG identifier of WGS84." 
    # This 'outproj' just specifies a point by its longitude and latitude.
    outproj = pyproj.Proj(init='epsg:4326')

    # If we're looking at precincts, open precinct-level results.
    if precincts:
        precinct_results = pd.read_csv('data/precinct_level_mayoral_results.csv')
        
    for record, shape in zip(sfile.records(),sfile.shapes()):
        # Get points (in input projection) from shapefile
        xarr,yarr = zip(*shape.points)
        # Transform points from input projection to longitudes and latitudes
        lons, lats = pyproj.transform(inproj, outproj, xarr, yarr)
        data = np.array(chimap(lons, lats)).T

        # Each shape may have different segments
        if len(shape.parts) == 1:
            segs = [data,]
        else:
            segs = []
            for i in range(1,len(shape.parts)):
                index = shape.parts[i-1]
                index2 = shape.parts[i]
                segs.append(data[index:index2])
            segs.append(data[index2:])

        # Draws the segments, set their properties. 
        lines = LineCollection(segs,antialiaseds=(1,))
        # Use a colormap to color the wards or precincts
        if color and record[2] != 'OUT' and not precincts:                    
            lines.set_facecolors(colors[int(record[2])%len(colors)])
        if color and precincts:            
            lines.set_array(precinct_frac(precinct_results,record))
            lines.set_cmap(cm.hot)
            
        lines.set_edgecolors('k')
        lines.set_linewidth(0.1)
        ax.add_collection(lines)

    

def main(shapefileroot = 'shapefiles/Wards'):

    #fig = plt.figure(figsize=(14,10))
    #ax1 = fig.add_axes([0.05,0.05,0.8,0.9])
    #ax2 = fig.add_axes([0.85,0.05,0.1,0.9])

    chimap = draw_chicago(resolution='c')
    sfile = shapefile.Reader(shapefileroot)  
    proj4string = utils.esriprj_to_proj4(shapefileroot + '.prj')

    create_line_segments(chimap, sfile, proj4string,color=False)

    precinctshapes = shapefile.Reader('shapefiles/WardPrecincts')  
    precinctproj4string = utils.esriprj_to_proj4('shapefiles/WardPrecincts.prj')  

    create_line_segments(chimap, precinctshapes, precinctproj4string, 
                         color=True, precincts=True)

    #norm = mpl.colors.Normalize(vmin=0., vmax=1.)
    #olbar = mpl.colorbar.ColorbarBase(ax2, cmap=cm.hot, norm=norm,
    #                                   orientation='vertical')
    #chimap.colorbar(location='right')
    print 'before show'
    plt.show()

if __name__=='__main__':
    main()
