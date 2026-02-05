import sqlite3
import os
import pandas as pd
import sys

#script_dir = os.path.dirname(os.path.abspath(__file__))  # Directory containing this script
#distribution_csv_path = os.path.join(script_dir, "distributions.csv")
DATABASESFOLDER = os.path.join(os.path.expanduser('~'),'AppData','Local','Segmentation App','Databases')
DATABASE = 'settings.db'

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller .exe """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class DatabaseHandler:
    def __init__(self):
        """Here is where I would make database connections"""
        self.connection = None
        self.cursor = None
        self._create_database() # create the database




    """Here would be my layout for this
        1. Create Database if not created
        2. Parse through distributions.csv
        3. insert data into database (id, formula name, active (0,1), formula string)
        4. update database, based on distribution selection
        5. run analysis based on database distributions"""
    
    def _create_database(self):

        if not os.path.exists(DATABASESFOLDER):
            os.makedirs(DATABASESFOLDER)

        db_path = os.path.join(DATABASESFOLDER, 'settings.db')

        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor() # this will be for navigation in the future

        # this is what creates the table for us
        sql = '''create table if not exists distributions(
            ID integer primary key autoincrement,
            distribution_name text UNIQUE,
            active int,
            formula text
        )'''

        self.cursor.execute(sql)

        sql = '''create table if not exists segmentation_settings(
            ID integer primary key autoincrement
        
        )'''

        self.cursor.execute(sql)
        self.connection.commit()

    def _parse_distributions(self):

        self.cursor.execute("SELECT * from distributions")

        # function to get the distribution and active selection
        # creates a dict of distribution and active status
        data = self.cursor.fetchall()
        existing_distributions = {row[1]: row[2] for row in data}

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        #distribution_csv_path = os.path.join(base_dir, "analysis_scripts", "distributions.csv") #FOR VSCODE

        #distribution_csv_path = resource_path("analysis_scripts/distributions.csv") #FOR PYINSTALLER

        if getattr(sys, 'frozen', False):
            # If we're running in a PyInstaller bundle
            distribution_csv_path = resource_path("analysis_scripts/distributions.csv")
        else:
            distribution_csv_path = os.path.join(base_dir, "analysis_scripts", "distributions.csv") 
        

        df = pd.read_csv(distribution_csv_path)


        for index, row in df.iterrows():
            distribution = row['Distribution'] # same here this is our dist formula
            formula = row['Formula'] # this is our pandas df formula
            
            
            # checking to see if we alreadt have an active distribution, if not set it to the default zero value
            if distribution in existing_distributions:
                active = existing_distributions[distribution]
            else:
                active = 0

            distribution_values = (distribution, active, formula)

            """What this loop is doing, is checking to see if our formulas align with what is seen in the csv file
               if a formula was updated then the data base will update accordingly"""
            
            for formulas in data:
                if formulas[3] != formula:
                    sql = "UPDATE distributions SET formula = ? WHERE distribution_name = ?"
                    self.cursor.execute(sql, (formula, distribution))
                    

            # Doing this instead ensures it wont break by a ' or something like that
            sql = f"INSERT OR IGNORE INTO distributions(distribution_name, active, formula) VALUES(?, ?, ?)"

            self.cursor.execute(sql, distribution_values)


        self.connection.commit()

        #self.connection.close()

    def _reset_database(self):
        """Clear the distributions table to allow full repopulation from CSV."""
        if self.cursor is None:
            raise Exception("Database not initialized. Run _create_database() first.")

        # Delete all rows in the distributions table
        self.cursor.execute("DELETE FROM distributions")

        self.connection.commit()

    def _get_selected_distributions(self):
        # gets all active distributions where active = 1
        self.cursor.execute("SELECT distribution_name FROM distributions WHERE active = 1")
        results = self.cursor.fetchall() 
        selected_list = []
        for result in results:
            selected_list.append(result[0])

        return selected_list # return as a list since within the pdf generator we need a list not tuples

    def _run_selected_distributions(self):
        pass

    def _get_all_distributions(self):
        """Get all distributions with their active status and formulas"""
        self.cursor.execute("SELECT distribution_name, active, formula FROM distributions")
        return self.cursor.fetchall()
    
    # will need this to update each distribution according to what the user selects
    def _update_distribution_status(self, distribution_name, active_status):
        """Update the active status of a distribution in the database"""
        self.cursor.execute(
            "UPDATE distributions SET active = ? WHERE distribution_name = ?",
            (active_status, distribution_name)
        )
        self.connection.commit()

    # Ensures the connection will be closed 
    def _close_connection(self):
        """Close the database connection"""
        if self.connection:
            self.connection.commit()
            self.cursor.close()
            self.connection.close()

    # Ensures it will get deleted 
    def __del__(self):
        """Ensure connection gets closed when object is destroyed"""
        self._close_connection()

# df = pd.read_csv(distribution_csv_path)

# for index, row in df.iterrows():
#     dist = row['Distribution']
#     print(dist)

db = DatabaseHandler()
#db._reset_database() # Call this if you need to 'reset' the database to remove all old 'distributions.csv' rows that no longer exist (test cases and aesthetic purposes)
db._parse_distributions()
print(db._get_selected_distributions())
