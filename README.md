# AIS_project

This project's goals are to:
- Gain experience building out data pipelines for large, geospatial datasets myself
- Learn more about PostGIS and QGIS
- Practice good software engineering practices in my data science projects
- Experiment with different ways of identifying and evaluating clusters in space and time
- Translating dense spatial-temporal data into networks
- Analyze network analysis, including machine learning for prediction

The project has three major phases.
  1. Data ingest, cleaning, and analysis.
  2. Cluster creation and evaluation.
  3. Network analysis and prediction.
  4. Timeseries analysis and prediction.

  Each phase has multiple individual projects.  This readme will try to document the project and track development.

  ## Data Sources
  Easy to scrape website
  https://coast.noaa.gov/htdata/CMSP/AISDataHandler/2017/index.html
  Pretty website:
  https://marinecadastre.gov/ais/
  World Port Index (loaded using QGIS into Post GIS)
  https://msi.nga.mil/Publications/WPI


  ## Required Software
  - PostGreSQL with post GIS
  - PG Admin 4
  - QGIS
  - Spyder

  Python Packages
  - update all packages here

  ## Background
  Fueled by near universal adoption of smartphone technology across the developed world, the last few years have seen a renaissance in the capabilities of large-scale geospatial data exploitation and analysis.  Locational metadata from users can provide insights on traffic density and congestion, the current popularity of restaurants, stores or other places of interest, and even support analysis of pandemics like in 2020 (See Israel's use at https://www.nytimes.com/2020/03/16/world/middleeast/israel-coronavirus-cellphone-tracking.html, or Unacast's social distancing scoreboard at https://www.unacast.com/covid19/social-distancing-scoreboard).

  The risk to personal privacy with this volume and precision of this data is significant, and therefore access to the data is extremely limited (See The New York Times excellent deep dive into this topic One Nation, Tracked at https://www.nytimes.com/interactive/2019/12/19/opinion/location-tracking-cell-phone.html).  I intend to use this AIS data as a proxy to develop expertise on building pipelines, conducting EDA, developing models, and extracting insights.  

  I argue that this dataset is a good proxy for the type of location metadata being used today for several reasons:
  - There is a unique identifier for each ship, which allows me to analyze one particular entity's pattern.  This is key for many approaches being used today on locational metadata as its a specific phone or devices movement from one area to another that is of interest (see Spring Breakers at a Florida beach returning across country during COVID-19 crisis https://twitter.com/TectonixGEO/status/1242628347034767361)
  - The data is high volume.  Much like the curse of dimensionality, there can be too much of a good thing in data analysis.  The high volume of this location metadata is a core part of its strength, but complicates analysis.  
  - Activity is varied.  In the AIS data, there are sailboats, container ships, tankers, fixed sites, and a number of other maritime entities going about their regular business.  This makes the data noisy, a reality likely common to most location datasets.

  The AIS data is different from other location datasets of interest though in several key ways.  
  - It is dramatically narrower in scope in that all activity is related to ships.  Despite the variety of ships involved, it is a much narrower slice of activity.
  - It is spatially constrained to the maritime domain, simplifying some of the spatial analysis required.
  - The data collection is limited to land-based coastal collection sites.  This leads to a non-continuous record of activity for many AIS devices, something less likely to occur in other location metadata.



  ## Data Ingest, Cleaning, and Analysis

  The AIS data is large.  January 2017 data fro the US is 25 gigabytes.  The entire year could be about 300 gigabytes.  There are two options here.  The first is to put it all in the cloud with all the raw data and cleaned tables.  The second is to  store all csvs as zipped files, process and clean he data in chunks to a database, and create a summary for every vessel in the data.  Then, we can sample the raw positions and conduct cluster analysis on those samples.  Armed with our summary analysis of the entire data, we can then ensure that our samples are repersentative of different patterns.

  We will first pursue the latter option, but may eventually use AWS to spin-up a PostGres instance.  

  Current implementation (16 January 2019) uses a source directory as an input and iterates through all the csv files in that directory.  Future improvements can allow filtering based on month and zone.  Additionally, can eventually add a webscraper component.

  Still to do on ingest script:
  - Set up scrape from remote website
  - set up automatic filters for zones and months to

  ### Ingest pipelines
  First we create a new database (in prod it is the "AIS_data" database) and then build a Post GIS extension.  Then we run the python script "ingest_script_prod".  This script:

  - Creates a connection to the db
  - Drops any existing tables using a custom 'drop_table' function.  (Note, in prod the actual calls are commented out for safety.)
  - Creates a "dedupe_table" function for the ship_info table.
  - Creates the tables 'imported_ais' to hold the original copied data, the ship_info table that includes mmsi, ship name and ship type, the ship_position table with location data for each position, and the wpi table that has info from the world port index for each major port.
  - The "parse_ais_SQL" function ingests the raw csv file to imported_ais and then selects the relevant data for the ship_info and ship_position table.
  - The "make_ship_trips" function creates a ship_trips table that reduces each ship's activity in the ship_position table to summary stats, including a line of the ship's voyage.
  - All activities are recorded to a processing log ("proc_log") with the date appended.  "function_tracker" function executes key functions, logs times, and prints updates to the console.

  ### Reducing Raw position data
  Unfortunately analysis against the entire corpus is difficult with limited compute.   However, we can reduce the raw positions of each ship into a line segment that connects each point together in the order of time.  Because there are sometimes gaps in coverage, a line will not follow the actual ships path and "jump".  The "make_ship_trips" function in the ingest pipeline uses geometry in PostGIS to connect all positions per ship, but this is not accurate as the coverage is not consistent.

  ### Analyze Summarized Ship trips
  Since we don't want to test all of our algorithm development against the entirety of the data, we need to select a sample of MMSI from the entire population to examine further.  The Jupyter Notebook "ships_trips_analysis" parses the ships_trips table and analyzes the fields.  We can use it to select a sample of MMSIs for further analysis.  The notebook builds several graphs and examines the summary of each MMSI's activity.  After filtering out MMSIs that don't travel far, have very few events, or travel around the globe in less than a month and are possible errors, the notebook exports a sample (250 now) to a csv file.  The notebook also writes the ship_trips sample to a new table, "ship_trips_sample" directly from the notebook using SQL Alchemy.

  ### Create Samples for Further analysis
  Python script "populate_sample" takes the csv output of the sample MMSIs from the Jupyter Notebook "ships_trips_analysis" and adds all positions from the "ship_position" table to a new "ship_position_sample" table.  It also makes a "ship_trips_sample" table from the full "ship_trips" table.

  ### Port Activity
  Creates a table that includes all of a ship's position when the ship's positions are within X meters of a known port.  This table has all of these positions labeled with that port. Then

  The WPI dataset has  duplicate port locations.  Specifically, the exact same geos are used twice by two different named and indexed ports 13 times.  I naively dropped duplicates on the lat and lon columns to resolve.

  Still to do:
  - rejoin this back to the main tables since we want to have a port for each position as well as the blanks.  Making a new table is fine for the sample data, but not for the full data.


  ### Status as of 18 January 2019:
  Using a sample of 200 mmsis, we went from 135 million positions in all of January to a total of 2,155,696 positions.  This reduces to 1003 nodes.

  ### Table Summary
  imported_ais --> ship_position --> ship_trips --> port_activity --> edges


  ### Lessons Learned
  #### Using PostGreSQL COPY rather than iterating through chunks using pandas
  Using Pandas and iterating through 100000 rows at a time on a sample csv of 150 mb took ~2 mins.  By using copy to create a temp table and then selecting the relevant info to populate the ship_info and ship_position table, the total time was reduced to 25 seconds.

  ### A note on Spatial Indices
  I first failed to create spatial indices at all.  This led to a 2 minute 45 second spatial join between a table with 9265 positions and the WPI table with 3630 ports.  By adding a spatial index with the below syntax to both tables, the query then took only 124 msec.  Running the same query against over 2 million rows in the sample data took 2.6 seconds.

  CREATE INDEX wpi_geog_idx
  ON wpi
  USING GIST (geog);
  CREATE INDEX ship_test_geog_idx
  ON ship_test
  USING GIST (geog);

  ## Notes on Visualizing in QGIS

  Large numbers of points within a vector layer can severely impact rendering performance within QGIS.  Recommend using the "Set Layer Scale Visibility" to only show the points at a certain scale.  Currently I found a minimum of 1:100000 appropriate with no maximum.  Ship trips can have no scale visibility because they render much faster.


  # Clustering

  Note, when we get there, we will have to look at how to represent time.  If we include it as a Z dimension, the scale will impact different clustering spaces.  Perhaps we can run the same clustering approaches with different time scales to show how it can impact the final clusters.  Or we could just ignore time entirely and cluster just based on spatial activity.

  Can I use labeled clusters of "ports" to identify the critical values for distance in time and space, and then apply those parameters against the rest of the data.
  -Likely DBSCAN is the best implementation
  -Would Gaussian mixture models successfully identify anamalous ship traffic?

  So use DBSCAN to cluster individual ships, but it crashes local machine in sklearn.  Rebuilt code to work in PostGres and can now run locally or in the cloud.  We can run the clustering for each ship, and then cluster all the ports from all the ships to find final ports.  This may be less subject to drift over time.  Our hyperparametrs are only good for the volume of ships in the timeframe.  Say we had well-tuned parameters for a month of AIS data.  They would be far too low for a years worth of data, because 12 times the shipping activity is in the same area.  If we cluster the activity first and then cluster to find ports, its could be more resistent to walking.


  Need to do:
  - on the purity analysis, need to compare when closest port == most strongly repersented port.
  - what is the proporiton of None as port?
  - filter out points that are far from known ports (activity on mississippi river)
  - add column for composition, ie how many unique mmsis are in each cluster.  penalize singletons.

  # Network Analysis

  First step is to create the input for a network multigraph.  For each unique identifier, lets evaluate if each point is "in" a port, as defined as a certain distance from a known port.  Then we can reduce all of the points down to when each unique identifier arrives and departs a known port.  In this network, each node is a port, and the edges are the travels of one identifier from a port to another.

  The python script "port_activity" identifies all positions within a certain distance of a port (now set for 2000m).  It then finds the closest port if more than one is returned, and joins the closes port back to the position data as a new table.  Right now this is one large query and needs to be modified to insert the new columns for port_id and port_name back into the original data rather than make a new table.

  The Python script "network_building" iterates through a table with ship position and determines an origin and destination for each connection between two ports.  These can be imported into networkx as edges.  The script also captures departure time,  arrival time, and total positions between the two ports as edge attributes.  These can be used to narrow down true port-to-port trips and minimize times when a ship repeatedly jumps back and forth between ports in a short number of positions or narrow time window.  All of this data is written to a table in the database.


  - I also need to add a conditional that looks for a minimum of X time at each port to prevent a ship from traveling by numerous ports to be listed as in port.
  - Refactor not to use pandas if proved to be non-preformant
  - Break code block into functions
