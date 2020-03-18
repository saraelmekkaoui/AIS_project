#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 17 23:03:35 2020

@author: patrickmaus
"""

#time tracking
import datetime

# db admin
import psycopg2

#%%
def postgres_dbscan(source_table, eps_km, min_samples, conn):
    
    #this formulation will yield epsilon based on km desired
    kms_per_radian = 6371.0088
    eps = eps_km / kms_per_radian
    
    new_table_name = ('dbscan_results_' + str(eps_km).replace('.','_') + 
                      '_' + str(min_samples))
    
    # drop table if an old one exists
    c = conn.cursor()
    c.execute("""DROP TABLE IF EXISTS {}""".format(new_table_name))
    conn.commit()
    c.close()
    
    print("""Starting processing on DBSCAN with eps_km={} and min_samples={} """.format(str(eps_km), str(min_samples)))
    
    dbscan_sql = """CREATE TABLE {} AS
    SELECT id, lat, lon, 
    ST_ClusterDBSCAN(Geometry(geog), eps := {}, 
    minpoints := {}) over () as clust_id
    FROM {};""".format(new_table_name, eps, min_samples, source_table)
    
    # execute dbscan script
    c = conn.cursor()
    c.execute(dbscan_sql)
    conn.commit()

    # add a geom column to the new table and populate it from the lat and lon columns
    c.execute("""ALTER TABLE {} ADD COLUMN 
                geom geometry(Point, 4326);""".format(new_table_name))
    conn.commit()
    c.execute("""UPDATE {} SET 
                geom = ST_SetSRID(ST_MakePoint(lon, lat), 4326);""".format(new_table_name))
    conn.commit()
    c.close()    
    
    print('DBSCAN complete, {} created'.format(new_table_name))    
    
#%% Run this code when we generate our own df_results from dbscan

database='ais_test'
loc_conn = psycopg2.connect(host="localhost",database=database)
c = loc_conn.cursor()
if c:
    print('Connection to {} is good.'.format(database))
else:
    print('Error connecting.')
c.close()
#%%
epsilons = [2, 5, 7, 10, 15]
samples = [50, 100, 250, 500, 1000, 2000]
for e in epsilons:
    for s in samples:      
            
        tick = datetime.datetime.now()
        
        postgres_dbscan('ship_position_sample', e, s, loc_conn)
        
        #timekeeping
        tock = datetime.datetime.now()
        lapse = tock - tick
        print ('Time elapsed: {}'.format(lapse))