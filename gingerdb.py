#!/usr/bin/env python
import os, glob, re, datetime, sys
import psycopg2

from ConfigParser import ConfigParser

class Config(object):
    """configuration and settings"""
    def __init__(self,configfile='ginger.conf'):
        # try to read default config file
        # TODO: build in try / except for reading config file
        config = ConfigParser()
        config.read(configfile)

        self.database = config.defaults()['database']
        self.host =  config.defaults()['host']
        self.port = config.defaults()['port']
        self.user = config.defaults()['user']
        self.password = config.defaults()['password']

    def set(self):
        """set configuration"""
        pass
       
    def save(self):
        """save current configuration to file"""
        pass

    def show(self):
        """show current configuration settings"""
        pass

# db class to connect to postgis db
class GingerDB(object):
    """connect to postgis DB and provide handlers to execute queries"""
    def __init__(self, config):
        self.database = config.database
        self.host     = config.host 
        self.user     = config.user
        self.password = config.password
         
        try:
            self.connection = psycopg2.connect("dbname='%s' user='%s' host='%s' password='%s'" %(self.database,
            self.user,
            self.host,
            self.password));
            self.cursor = self.connection.cursor()
            print("Verbinding met database %s geslaagd." %(self.database))
        except:
            print("*** FOUT *** Verbinding met database %s niet geslaagd." %(self.database))
            print("")
            raw_input("Druk <enter> om af te sluiten")
            sys.exit()

        # setup search path
        self.execute("SET search_path TO public, werk, resultaat, instellingen, initialisatie")

    def listtables(self):
        '''list all tables in database'''
        try:
            sql = "SELECT * FROM information_schema.tables"
            self.execute(sql)
            result = self.cursor.fetchall()
            self.connection.commit()
            return result
        except (psycopg2.Error,), error:
            # TODO: build logging
            # log("*** Error ***" cannot execute SQL statement '%s':\n %s) % (sql, error)
            raise error
    
    def execute(self, sql):
        """execute sql"""
        try:
            self.cursor.execute(sql)
            self.connection.commit()
            return self.cursor.rowcount
        except (psycopg2.Error,), error:
            # TODO: build logging
            # log("*** Error ***" cannot execute SQL statement '%s':\n %s) % (sql, error)
            raise error

# class containing dmc logic and data
class MaatregelAfweging(object):
    """bepaal maatregelen aan de hand van ontvangerpunten en trajecten"""
    def __init__(self, db):

        self.db = db
        #self.ontvangerpunten = db.
        #self.trajecten =
        print "Niewe MaatregelAfweging geinitialiseerd"

    def maatgevendtraject(self, zoekstraal=1500):
        """* selecteer alle trajecten die binnen een straal van 1500 m van de POI liggen
        * bereken de emissie naar afstand: eNaarAfstand = eday_tot - (10 * (Log(afstand)))
        * selecteer maatgevend traject door MAX(eNaarAfstand) voor ieder POI
        """
        print "Selecteer maatgevende trajecten"
        sql = """DROP TABLE IF EXISTS maatgevend_traject;
        CREATE TABLE resultaat.maatgevend_traject AS
        WITH traject_binnen_buffer AS (
        SELECT POI.*, traject.eday_tot AS eday_tot, traject.trajectid AS trajectid, ST_Distance(POI.the_geom, traject.the_geom) AS afstand, (eday_tot - ( 10 * (Log(ST_Distance(POI.the_geom, traject.the_geom))) )) AS eNaarAfstand
        FROM ontvangerpunten AS POI
        RIGHT JOIN trajecten AS traject
        
        ON ST_DWithin(POI.the_geom, traject.the_geom, %i)
        WHERE ST_Distance(POI.the_geom, traject.the_geom) > 0
        )
        SELECT DISTINCT ON (ontvangerid) ontvangerid, trajectid, afstand, eNaarAfstand, the_geom
        FROM (
        SELECT ontvangerid, trajectid, afstand, eNaarAfstand, the_geom, MAX(eNaarAfstand) OVER (PARTITION BY ontvangerid) AS max_e
        FROM traject_binnen_buffer
        ) AS tbb
        WHERE eNaarAfstand = max_e
        ORDER BY ontvangerid;
        DROP INDEX IF EXISTS maatgevend_traject_the_geom;
        CREATE INDEX maatgevend_traject_the_geom ON maatgevend_traject USING GIST( the_geom );
        ALTER TABLE maatgevend_traject ADD COLUMN maatgevend_trajectid INTEGER;
        DROP SEQUENCE IF EXISTS maatgevend_traject_id_seq;
        CREATE SEQUENCE maatgevend_traject_id_seq;
        UPDATE maatgevend_traject SET maatgevend_trajectid = nextval('maatgevend_traject_id_seq');
        ALTER TABLE maatgevend_traject ALTER COLUMN maatgevend_trajectid SET DEFAULT nextval('maatgevend_traject_id_seq');
        ALTER TABLE maatgevend_traject ALTER COLUMN maatgevend_trajectid SET NOT NULL;
        ALTER TABLE maatgevend_traject ADD PRIMARY KEY (maatgevend_trajectid);
        """ % (zoekstraal)

        self.db.execute(sql)
        
        def segmentise(self):
            """segementeer trajecten in stukjes van X meter"""
            pass
        

# main to run cli
def main():
    """run command line stand alone"""
    config = Config()
    db = GingerDB(config) 
    #print db.listtables()
    ma = MaatregelAfweging(db)
    ma.maatgevendtraject(1500)

if __name__ == '__main__':
    main()
