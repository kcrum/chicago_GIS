Chicago Tribune 2000 and 2010 Ward Demographics map
---------------------------------------------------

In this zip file you will find a CSV file containing demographic data for Chicago's 50 wards
as well as Chicago itself. This file should be suitable for analysis in Excel or any other
spreadsheet application.

This data was generated from raw data downloads of US census redistricting data:

2000: http://www2.census.gov/census_2000/datasets/redistricting_file--pl_94-171/Illinois/
2010: http://www2.census.gov/census_2010/redistricting_file--pl_94-171/Illinois/

Columns
-------

The column names are abbreviated, but should otherwise be self-explanatory. The following is a
key to the abbreviations used, using the terminology of the census fields from which they are
sourced:

* amind: American Indian and Alaska Native alone (no other race)
* asian: Asian alone (no other race)
* black: Black or African American alone (no other race)
* chg: percent change from 2000 to 2010
* hisp: Hispanic (regardless of race)
* nh: Non-Hispanic
* other: Some Other Race alone (but not multiple races)
* pacific: Native Hawaiian and Other Pacific Islander alone (no other race)
* white: White alone (no other race)
* 00: population according to the 2000 census
* 10: population according to the 2010 census

Technical details
-----------------

The specific method employed to aggregate this data was to allocate census blocks to wards based
the location of each block's centroid. A few populated blocks failed to allocate due to inaccuracies
in the border of the Ward's shapefile. These were manually allocated to the correct wards.

Contact
-------

If you have questions about this data, please feel free to contact the News Applications team.

newsapps@tribune.com
@TribApps (twitter)
http://blog.apps.chicagotribune.com

