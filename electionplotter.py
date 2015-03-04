# So apparently you have two mpl_toolkits installations, but only one has 
# Basemaps. Python didn't search this mpl_toolkits first, and so failed to find
# Basemaps. Your crappy solution was to cp the 'basemap' directory directly 
# into the mpl_toolkits without basemap. This works, but it means software 
# updates for basemaps won't be automatically propagated. 
from matplotlib.collections import LineCollection
from matplotlib.patches import Polygon
import matplotlib.pyplot as plt  
from matplotlib import cm
import matplotlib as mpl
import pandas as pd
import numpy as np
import utils
import sys
# GIS modules
from mpl_toolkits.basemap import Basemap
from shapely.topology import TopologicalError
import shapely.geometry as geom
import shapefile  
import pyproj


def create_line_segments(chimap, sfile, proj4string, color=True, 
                         precincts=False, ax=plt.gca()):
    '''
    DEPRECATED (FINALLY!!!)

    Takes a shapefile and Proj4 projection string and adds line segments 
    demarcating ward and/or precinct boundaries to the plot axis. Roughly 
    follows example of:
    http://nbviewer.ipython.org/github/rjtavares/numbers_arent_people/blob/master/experiments/Plotting%20with%20Basemap%20and%20Shapefiles.ipynb
    '''

    ##### Coordinate transformations #####
    # The shapefiles you got from the City of Chicago Open Data site do not 
    # contain latitude and longitude points. Rather they contain relative 
    # measurements (in feet) using a predeterminted projection. Projections are
    # numerous and complicated, but the distinguishing details can be found in 
    # the .prj files.
    #
    # In order to get lat/lon coorindates (the preferred values for Basemap), 
    # you must transform coordinates from the city's projection. You 
    # successfully managed to transform a coodinate using information from the 
    # following StackExchange posts:
    #
    #http://gis.stackexchange.com/questions/10209/converting-x-y-coordinates-to-lat-long-using-pyproj-and-proj-4-returns-the-wrong
    #http://gis.stackexchange.com/questions/118215/proj4-string-for-nad832011-louisiana-south-ftus
    #
    # One key thing to remember is that the Chicago values are in feet, and 
    # PyProj always defaults to using meters, even if you pass it an EPSG code 
    # or Proj4 string that indicates that your projection is in feet. You must 
    # pass the "preserve_units=True" argument to PyProj in order for it to 
    # interpret your input coordinates from the city as being in feet.
    ######################################


    colors = ['#E24A33', '#348ABD', '#988ED5', '#777777', '#FBC15E', '#8EBA42',
              '#FFB5B8']

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


def draw_chicago(projection='merc', resolution='c',ax=plt.gca()):
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


def candidate_shorthands(candidate):
    '''
    This allows you to refer to a candidate by several names without raising 
    an exception.
    '''
    if 'rahm' in candidate.strip().lower() or \
       'emanuel' in candidate.strip().lower(): 
        return 'RAHM EMANUEL'
    elif 'fioretti' in candidate.strip().lower(): 
        return 'ROBERT W. FIORETTI'
    elif 'chuy' in candidate.strip().lower() or \
       'garcia' in candidate.strip().lower(): 
        return 'JESUS "CHUY" GARCIA'
    elif 'walls' in candidate.strip().lower(): 
        return 'WILLIAM WALLS III'
    elif 'wilson' in candidate.strip().lower(): 
        return 'WILLIE WILSON'  
    else:
        print 'No valid candidate name passed. Defaulting to Rahm.'
        return 'RAHM EMANUEL'


def precinct_color_frac(chimap, ax=plt.gca(), candidate='RAHM EMANUEL'):
    '''
    Given a map of Chicago, add shapes colored by fraction of votes candidate 
    received in a precinct in 2015.
    '''
    chimap.readshapefile('shapefiles/chicago_2015_precincts/chicago_2015_precincts','precincts', drawbounds=False)
    chimap.readshapefile('shapefiles/chicago_2015_wards/chicago_2015_wards',
                         'wards', linewidth=0.5, color='k')
    resultdf = pd.read_csv('data/precinct_level_mayoral_results2015.csv')
    
    for shape, precinct in zip(chimap.precincts, chimap.precincts_info):
        nward = int(precinct['ward'])
        nprecinct = int(precinct['precinct'])
        row = resultdf[(resultdf.Ward == nward) & \
                       (resultdf.Precinct == nprecinct)]
        if row.empty:
            print 'Ward %s, precinct %s has no vote data.'% (nward, nprecinct)
        else:
            votefrac = float(row[candidate])/row['Votes Cast']
            poly = Polygon(shape, facecolor=cm.Reds(votefrac)[0], 
                           edgecolor='none')
            ax.add_patch(poly)        

    lenleg = 25
    cmleg = np.zeros((1,lenleg))
    for i in range(lenleg):
        cmleg[0,i] = float(i)/lenleg
    plt.imshow(cmleg, cmap=plt.get_cmap('Reds'))
    

def ward_color_frac(chimap, ax=plt.gca(), candidate='RAHM EMANUEL', shapefileroot='shapefiles/chicago_2015_wards/chicago_2015_wards'):
    '''
    Given a map of Chicago, add shapes colored by fraction of votes candidate 
    received.
    '''
    chimap.readshapefile(shapefileroot,'Wards')
    wardresultdf = pd.read_csv('data/mayoral_ward_results2015.csv')
    
    for shape, ward in zip(chimap.Wards, chimap.Wards_info):        
        nward = int(ward['ward'])
        row = wardresultdf[wardresultdf.Ward == nward]
        votefrac = float(row[candidate])/row['Votes Cast']
        poly = Polygon(shape, facecolor=cm.CMRmap(votefrac)[0])
        ax.add_patch(poly)        

    lenleg = 25
    cmleg = np.zeros((1,lenleg))
    for i in range(lenleg):
        cmleg[0,i] = float(i)/lenleg
    plt.imshow(cmleg, cmap=plt.get_cmap('CMRmap'))


def ward_color_frac_2011(chimap, ax=plt.gca(), candidate='RAHM EMANUEL', 
                         shapefileroot='shapefiles/pre2015_wards/wgs84_wards/Wards'):
    '''
    Given a map of Chicago, add shapes colored by fraction of votes candidate 
    received in 2011 mayoral election.
    '''
    chimap.readshapefile(shapefileroot,'Wards')
    wardresultdf = pd.read_csv('data/mayoral_ward_results2011.csv')

    for shape, ward in zip(chimap.Wards, chimap.Wards_info):
        if ward['WARD'] != 'OUT':
            nward = int(ward['WARD'])
            row = wardresultdf[wardresultdf.Ward == nward]
            votefrac = float(row[candidate])/row['Votes Cast']
            poly = Polygon(shape, facecolor=cm.CMRmap(votefrac)[0])
            ax.add_patch(poly)        

    lenleg = 25
    cmleg = np.zeros((1,lenleg))
    for i in range(lenleg):
        cmleg[0,i] = float(i)/lenleg
    plt.imshow(cmleg, cmap=plt.get_cmap('CMRmap'))


def rahm_vs_chuy():
    '''
    Plot fraction of votes for Rahm and Chuy, by precinct.
    '''
    fig, (ax1,ax2) = plt.subplots(1,2)

    chimap = draw_chicago(resolution='c',ax=ax1)
    precinct_color_frac(chimap, candidate='RAHM EMANUEL',ax=ax1)
    ax1.set_title("Fraction of ward voting for RAHM EMANUEL")

    plt.colorbar()

    chimap2 = draw_chicago(resolution='c',ax=ax2)
    candidate = candidate_shorthands('chuy')
    precinct_color_frac(chimap2, candidate=candidate,ax=ax2)
    ax2.set_title("Fraction of ward voting for %s" % candidate)
    
    plt.show()


def precinct_results(candidate):
    '''
    Plot fraction of votes for 'candidate,' by precinct.
    '''
    fig, ax = plt.subplots()

    chimap = draw_chicago(resolution='c',ax=ax)
    candidate = candidate_shorthands(candidate)
    precinct_color_frac(chimap, candidate=candidate,ax=ax)
    ax.set_title("Fraction of ward voting for %s" % candidate)
    
    plt.colorbar()
    plt.show()


def draw_ward_tracts(wardshape, chimap, ax=plt.gca()):
    '''
    Given a ward's shapefile.shape, draw ward and its census tracts.
    '''
    wardpoly = geom.Polygon(wardshape.points)
    lines = utils.shape_to_linecollection(wardshape, chimap, 'b', 1.0)
    ax.add_collection(lines)

    censfile = shapefile.Reader('shapefiles/wgs84_ACSdata_tracts/ChTr0812')

    for shape, rec in zip(censfile.shapes(), censfile.records()):
        tractpoly = geom.Polygon(shape.points)

        if wardpoly.intersects(tractpoly):
            try:
                interfrac = wardpoly.intersection(tractpoly).area/wardpoly.area
                if interfrac > 1e-4:
                    lines = utils.shape_to_linecollection(shape, chimap, 'r')
                    ax.add_collection(lines)
            except TopologicalError:
                print rec
    plt.show()


if __name__=='__main__':
    if len(sys.argv) == 1:
        rahm_vs_chuy()
    else:
        precinct_results(sys.argv[1])
