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


def census_ethnicity_frac(chimap, ax=plt.gca(), ethnicity='PtL', shapefileroot='shapefiles/wgs84_ACSdata_tracts/ChTr0812'):
    '''
    Given a map of Chicago, add census tracts colored by percentage of 
    inhabitants of a certain ethnic group (default: Latino). For non-Latino 
    African-American, use the string 'PtNLB'. For non-Latino whites, use the 
    string 'PtNLWh'.
    '''
    chimap.readshapefile(shapefileroot,'tracts')
    
    for shape, tractinfo in zip(chimap.tracts, chimap.tracts_info):        
        ethnicfrac = tractinfo[ethnicity]/100.
        poly = Polygon(shape, facecolor=cm.Reds(ethnicfrac))
        ax.add_patch(poly)        

    lenleg = 25
    cmleg = np.zeros((1,lenleg))
    for i in range(lenleg):
        cmleg[0,i] = float(i)/lenleg
    plt.imshow(cmleg, cmap=plt.get_cmap('Reds'))


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


def candidate_vs_candidate(cand1='rahm', cand2='chuy'):
    '''
    Plot fraction of votes by precinct for two candidates.
    '''
    fig, (ax1,ax2) = plt.subplots(1,2)

    chimap = draw_chicago(resolution='c',ax=ax1)
    candidate = candidate_shorthands(cand1)
    precinct_color_frac(chimap, candidate=candidate,ax=ax1)
    ax1.set_title("Fraction of ward voting for %s" % candidate)

    plt.colorbar()

    chimap2 = draw_chicago(resolution='c',ax=ax2)
    candidate = candidate_shorthands(cand2)
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


def bad_census_tracts(chimap, ax=plt.gca(), edgecolor='k', verbose=False,
                      filepath='shapefiles/wgs84_ACSdata_tracts/ChTr0812'):
    '''
    Adds census tracts that fail shapely's "is_valid" check to axis object. If
    verbose, also outputs index number and tract number for these bad tracts.
    TO DO: Consider buffering these shapes to get rid of small artifacts? Still
    not sure how to handle large disjoing polygons, however...
    '''
    sfile = shapefile.Reader(filepath)

    colors = ['#E24A33', '#348ABD', '#988ED5', '#777777', '#FBC15E', '#8EBA42',
              '#FFB5B8']

    for shape, rec in zip(sfile.shapes(), sfile.records()):
        tractpoly = geom.Polygon(shape.points)
        if not tractpoly.is_valid:
            if verbose:
                print 'Shape index: %s tract number: %s' % (rec[0] - 1, rec[3])

            lines = utils.shape_to_linecollection(shape, chimap)
            lines.set_facecolor(np.random.choice(colors))
            ax.add_collection(lines)


if __name__=='__main__':
    if len(sys.argv) == 1:
        candidate_vs_candidate()
    else:
        precinct_results(sys.argv[1])
