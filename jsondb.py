#!/usr/bin/env python

'''
'''
#----------------------------------------------------------------------------------
import os, sys, datetime, re, json, shutil, glob, traceback
import pandas as pd
import numpy as np
sys.path.append("/opt/utils")
from colabexts import utils as colabexts_utils
from collections import defaultdict 
from mangorest import mango
from inspect import isfunction

import logging

# Remove all handlers associated with the root logger object.
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.basicConfig( level=logging.INFO,
        format='%(levelname)s:%(name)s %(asctime)s %(filename)s:%(lineno)s:%(funcName)s: %(message)s',
        #format='%(asctime)s %(name)s %(levelname)s: %(message)s',
        handlers=[ logging.FileHandler("/tmp/app.log"), logging.StreamHandler()],
)
logger = logging.getLogger( "genai_utils" )


class myjson:
    def __init__(self, db="default", base=os.path.expanduser("~/myjson")):
        self.base = os.path.expanduser(base)
        self.db = db
        self.createdb( db )

    def createdb(self, db):
        db = self.base + "/" + db
        os.makedirs(db, exist_ok=True)
        self.db = db
        logger.debug(f"Current DB {self.db}")
        #traceback.print_stack()
        return self.db

    def changedb(self, db):
        createdb(db)

    def deletedb(self, db):
        if (db == "default"):
            logger.warning(f"Cannot Delete default DB")
            return

        db = self.base + "/" + db
        logger.info(f"Deleting DB {db}: {db}")
        shutil.rmtree(db)
        if self.db == db:
            createdb("default")

        return self.db
        

    def listDbs(self):
        dbs = [os.path.basename(c[0:-1]) for c in glob.glob(f"{self.base}/*/", recursive=True)]
        return dbs

    def listTables(self):
        dbs = [os.path.basename(c[0:-1]) for c in glob.glob(f"{self.db}/*/", recursive=True)]
        return dbs

    def create_table(self, table):
        tab = self.db + "/" + table 
        os.makedirs(tab, exist_ok=True)
        return tab

    def delete_table(self, table):
        tab = self.db + "/" + table 
        if ( os.path.exists(tab)):
            shutil.rmtree(tab)
        return tab

    def _update_info(self, df, table, max_id):
        if ( len(df) <= 0):
            return
            
        info_file = f"{self.db}/{table}/info.js"
        infoj = dict(columns=[c for c in df.columns], maxid=max_id, nrows=len(df))
        open(info_file, "w").write(json.dumps(infoj, indent=2))

        #infoj = colabexts_utils.parsej(open(info_file).read())
        return infoj
        
    def fromDataFrame(self, df, table, delete=True):
        if (delete):
           self.delete_table(table) 
        tab = self.create_table(table)
        for rowid, r in df.iterrows():
            d = r.to_dict()
            d['rowid'] = rowid
            open(f"{tab}/{rowid}.json", "w").write( json.dumps(d, indent=2))
        
    def get(self, table, rowid=None ):
        if ( not rowid):
            return self.read(table)

        f = f"{self.db}/{table}/{rowid}.json"
        if ( not os.path.isfile(f)):
            return None
        r = open(f).read()
        a = colabexts_utils.parsej(r)
        return a;

    def read(self, table, nrows=1024*1024, filter=None , **kwargs):
        rows, cols, max_id =[], {}, 0

        dir = f"{self.db}/{table}/*.json"

        #logger.debug(f"Reading from {dir}")

        sortk =  lambda x: int(os.path.basename(x).split('.')[0])
        if ( nrows and nrows < 0):
            nrows = -nrows
            files = sorted(glob.glob(dir), key=sortk , reverse=True)
        else:
            files = sorted(glob.glob(dir), key=sortk )

        for f in files:
            try:
                r = open(f).read()
                a = colabexts_utils.parsej(r)
                #a = json.loads(r)
                if ("rowid" not in a):
                    logger.error(f"ROWID IS MISSING in {f}")
                    #a['rowid'] = os.path.basename(f)[:-5]
                    continue; 
                    
                max_id = a['rowid']

                if ( filter and type(filter) == dict):
                    c = all(a.get(k, None) == v for k, v in filter.items())
                    if (not c):
                        continue
                elif ( filter and isfunction(filter) ):
                    c= filter(a)
                    if (not c):
                        continue

                cols.update(a)
                rows.append(a)
            except Exception as e:
                logger.error(e)
                out = ""
                for i, l in enumerate(r.split("\n")[:100]):
                    out += f'{i+1:3d}: {l}\n'
                logger.error(f"Error while parsing {f} \n\n{out}")
            if ( len(rows) >= nrows):
                break;
                
        df = pd.DataFrame(rows) 
        if ( not filter):
            self._update_info (df, table, max_id,)
        return df

    def delete(self, table, rowid, **kwargs):
        print(f'''
        **** DELETING {table} {rowid}
        **** 
        ****
        ''')
        f = f"{self.db}/{table}/{rowid}.json"
        if ( not os.path.isfile(f)):
            return 0
        os.rename(f, f+".deleted")
        pass;


    def update(self, table, data):
        ret = data
        if type(data) == str:
            ret = colabexts_utils.parsej(data)
        elif type(data) == pd.Series:
            ret = data.to_dict()
            
        tab = self.db + "/" + table 

        rowid = ret.get("rowid", None)
        if ( rowid is None or not str(rowid) or int(rowid) < 0 ):
            rowid = max([-1] +[int(os.path.basename(c[:-5])) for c in glob.glob(f"{tab}/*.json")])
            rowid = rowid + 1
            logger.info(f"Update called with no rowid: Assuming insert => newId= {rowid}")
            ret['rowid'] = rowid
            
        rowid = ret["rowid"]
        row = f"{tab}/{rowid}.json"
        
        if ( os.path.exists(row)):
            old = colabexts_utils.parsej((open( row, "r")).read())
            old.update(ret)
            ret = old
            
        open(f"{tab}/{rowid}.json", "w").write( json.dumps(ret, cls=mango.myEncoder, indent=2))

        return ret
        
#db = myjson()
