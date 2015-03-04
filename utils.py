from matplotlib.collections import LineCollection
import numpy as np
import pandas as pd
# Scraping
from bs4 import BeautifulSoup
from urllib2 import urlopen
# GIS
import shapely.geometry as geom
from osgeo import osr
import shapefile



def esriprj_to_proj4(shapeprj_path):
    '''
    Takes .prj file and determines in which projection the shapefile was
    generated. Proj4 string for this projection is returned.
    '''
    prj_file = open(shapeprj_path, 'r')
    prj_txt = prj_file.read()
    srs = osr.SpatialReference()
    srs.ImportFromESRI([prj_txt])
    return srs.ExportToProj4()


def mayor_results_df_ward(filepath='data/raw_files/overall_mayor_results.txt',
                          year2011=False, nwards=50):
    # This is the ordering of the columns in the Board of Elections data. The
    # columns unfotunately get spread out line-by-line in the text file.
    coldict = {0:'Ward',1:'Votes Cast',2:'RAHM EMANUEL',3:'pct',
               4:'WILLIE WILSON',5:'pct',6:'ROBERT W. FIORETTI',7:'pct',
               8:'JESUS "CHUY" GARCIA',9:'pct',10:'WILLIAM WALLS III',11:'pct'}
    columns = ['Ward','Votes Cast','RAHM EMANUEL', 'WILLIE WILSON',
               'ROBERT W. FIORETTI','JESUS "CHUY" GARCIA','WILLIAM WALLS III']

    # This is the ordering of the columns in the Board of Elections data for 
    # the 2011 election. The columns unfotunately get spread out line-by-line 
    # in the text file.
    coldict2011 = {0:'Ward',1:'Votes Cast',2:'RAHM EMANUEL',3:'pct',
                   4:'MIGUEL DEL VALLE',5:'pct',6:'CAROL MOSELEY BRAUN',
                   7:'pct',8:'GERY J. CHICO',9:'pct',
                   10:'PATRICIA VAN PELT WATKINS',11:'pct',
                   12:'WILLIAM WALLS III',13:'pct'}
    columns2011 = ['Ward','Votes Cast','RAHM EMANUEL','MIGUEL DEL VALLE',
                   'CAROL MOSELEY BRAUN','GERY J. CHICO',
                   'PATRICIA VAN PELT WATKINS','WILLIAM WALLS III']
    if year2011:
        columns = columns2011
        coldict = coldict2011

    # Create dataframe
    df = pd.DataFrame(columns=columns, index=np.arange(1,nwards + 1))
    nline = 0
    # Read file, fill dataframe
    with open(filepath) as f:
        rowdict = {}
        for line in f:
            if line.strip():
                # Exit when you get to the 'Total' row
                if line.strip() == 'Total': break
                # Filter on which BofE column this row corresponds to
                if coldict[nline%len(coldict)] != 'pct':
                    rowdict[coldict[nline%len(coldict)]] = int(line.strip())
                nline += 1
                # Once you get to the text row corresponding to the last 
                # column, write data into dataframe.
                if nline%len(coldict) == 0: 
                    df.loc[rowdict['Ward']] = pd.Series(rowdict)

    # Return dataframe
    return df


def scrape_mayor_results_precinct(nwards=50):
    '''
    Scrape Chicago Board of Elections pages for ward-by-ward, precinct-level
    mayoral election results. 
    '''
    # All pages take the simple form 'urlprefix' + ward number + 'urlsuffix'
    urlprefix = 'http://www.chicagoelections.com/en/pctlevel3.asp?Ward='
    urlsuffix= '&elec_code=10&race_number=10'

    columns = ['Ward','Precinct','RAHM EMANUEL', 'WILLIE WILSON',
               'ROBERT W. FIORETTI','JESUS "CHUY" GARCIA','WILLIAM WALLS III',
               'Votes Cast']
    # Create dataframe
    df = pd.DataFrame(columns=columns)

    # The precinct-level pages are nearly identical, so it's straightforward
    # to hardcode the scraping. Perhaps not the best method, but straighfoward.
    for ward in xrange(1,nwards+1):
        html = urlopen(urlprefix + str(ward) + urlsuffix)
        soup = BeautifulSoup(html)
        # Find all bold tags. 
        btags = soup.find_all('b')
        # There are always 38 "extra" tags per ward's page. There are otherwise
        # 12 tags per row, so we can find the number of precincts in the given
        # wards as follows:
        nprecincts = (len(btags) - 38)/12
        # Simple error check (make sure no remainder in above division):
        if nprecincts != ((len(btags) - 38)/12.):
            print 'Pattern for Number of precincts broken in ward %s' % ward


        # The first precinct number always starts at tag 13. There are 12 tags
        # per row, so precinct numbers are always at index 13 + n*12. Rahm
        # is always 2 past the precinct, Willie is 4 past, and so on.
        for i in xrange(nprecincts):
            # Fill a dictionary that will hold all of this row's data.
            rowdict = {}
            rowdict[columns[0]] = ward
            votescast = 0
            for j in xrange(6):
                rowdict[columns[j+1]] = int(btags[13 + 2*j + 12*i].string)
                if j != 0: 
                    votescast += int(btags[13 + 2*j + 12*i].string)
            rowdict[columns[7]] = votescast
            df = df.append(rowdict, ignore_index=True)

    return df


def ward_census_overlap(wardbase='chicago_2015_wards/chicago_2015_wards', 
                        censusbase='wgs84_ACSdata_tracts/ChTr0812', 
                        verbose=False, threshold=1e-4):
    '''
    Searches for overlap between wards and census blocks. Ignores overlaps
    which are smaller than threshold*(ward's area).
    '''
    wardfile = shapefile.Reader('shapefiles/' + wardbase)
    censfile = shapefile.Reader('shapefiles/' + censusbase)

    # Make dict of census field indices, where 'field' is key and corresponding
    # index for 'field' is value.
    censinds = {}
    i = 0
    for f in censfile.fields[1:]:
        censinds[f[0]] = i
        i += 1

    # TEST CODE
    # Make a shapely polygon of ward 48
    poly48 = geom.Polygon(wardfile.shapes()[0].points)

    tractlist = []
    totoverlap = 0
    for shape, rec in zip(censfile.shapes(), censfile.records()):
        tractnum = rec[censinds['TRACT']]
        tractpoly = geom.Polygon(shape.points)
        
        if poly48.intersects(tractpoly):
            interfrac = poly48.intersection(tractpoly).area/poly48.area
            if interfrac > 1e-4:
                if verbose: 
                    print 'Tract %s intersects with ward 48; area: %s' % \
                        (tractnum, interfrac)
                    totoverlap += interfrac
                tractlist.append(tractnum)
                
    if verbose: print 'Total overlap: %s' % totoverlap
    return tractlist


def shape_to_linecollection(shape, chimap, edgecolor='k', linewidth=0.1):
    '''
    Takes a shape from a shapefile and returns a LineCollection.
    '''
    lons=np.array(shape.points).T[0,:]
    lats=np.array(shape.points).T[1,:]

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

    lines = LineCollection(segs,antialiaseds=(1,))
    lines.set_edgecolors(edgecolor)
    lines.set_linewidth(linewidth)
    return lines

    
