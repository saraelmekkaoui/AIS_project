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
from sqlalchemy import create_engine

#%%
def postgres_dbscan(source_table, eps_km, min_samples, conn, lat='lat', lon='lon',
                    posit_id='id'):

    #this formulation will yield epsilon based on km desired
    kms_per_radian = 6371.0088
    eps = eps_km / kms_per_radian

    new_table_name = ('dbscan_results_' + str(eps_km).replace('.','_') +
                      '_' + str(min_samples))

    print("""Starting processing on clustering_analysis with eps_km={} and
          min_samples={} """.format(str(eps_km), str(min_samples)))

    dbscan_sql = """CREATE TABLE IF NOT EXISTS {0} AS
    SELECT {1}, {2}, {3},
    ST_ClusterDBSCAN(Geometry(geog), eps := {}, minpoints := {4})
    over () as clust_id
    FROM {5};""".format(new_table_name, posit_id, lat, lon, str(eps), 
    str(min_samples), source_table)
    # execute dbscan script
    c = conn.cursor()
    c.execute(dbscan_sql)
    conn.commit()
    c.close()

    print('clustering_analysis complete, {} created'.format(new_table_name))


def make_tables_geom(table, conn):
    # add a geom column to the new table and populate it from the lat and lon columns
    c = conn.cursor()
    c.execute("""ALTER TABLE {} ADD COLUMN
                geom geometry(Point, 4326);""".format(table))
    conn.commit()
    c.execute("""UPDATE {} SET
                geom = ST_SetSRID(ST_MakePoint(lon, lat), 4326);""".format(table))
    conn.commit()
    c.close()

#%%
import aws_credentials as a_c
user = a_c.user
host = a_c.host
port = '5432'
database = 'aws_ais_clustering'
password = a_c.password

aws_conn = psycopg2.connect(host=host,database=database, user=user,password=password)
aws_c = aws_conn.cursor()
if aws_c:
    print('Connection to AWS is good.'.format(database))
else: print('Connection failed.')
aws_c.close()


# def create_aws_engine(database):
#     import aws_credentials as a_c
#     user = a_c.user
#     host = a_c.host
#     port = '5432'
#     password = a_c.password
#     try:
#         aws_engine = create_engine('postgresql://{}:{}@{}:{}/{}'.format(user, password, host, port, database))
#         print('AWS Engine created and connected.')
#         return aws_engine
#     except:
#         print('AWS Engine creation failed.')
#         return None

# aws_engine = create_aws_engine('aws_ais_clustering')

#%%
#database='ais_test'
#loc_conn = psycopg2.connect(host="localhost",database=database)
#c = loc_conn.cursor()
#if c:
#    print('Connection to {} is good.'.format(database))
#else:
#    print('Error connecting.')
#c.close()



    # # drop table if an old one exists
    # c = conn.cursor()
    # c.execute("""DROP TABLE IF EXISTS {}""".format(new_table_name))
    # conn.commit()
    # c.close()
#%%

print('Function run at:', datetime.datetime.now())
epsilons = [2, 5, 7, 10, 15, 20, 30]
samples = [50, 100, 250, 500, 1000, 1500, 2000, 3000, 5000]

for e in epsilons:
    for s in samples:

        aws_conn = psycopg2.connect(host=host,database=database, user=user,password=password)

        tick = datetime.datetime.now()
        # pass the epsilon in km.  the function will convert it to radians
        postgres_dbscan('ship_position_sample', e, s, aws_conn)

        #timekeeping
        tock = datetime.datetime.now()
        lapse = tock - tick
        print ('Time elapsed: {}'.format(lapse))
