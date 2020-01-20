import pandas as pd
df=pd.read_csv("survivial_combined_data.csv")
import argparse
from pandasql import sqldf

# now define a data structure to capture all needed information
# Note: Version number are assigned in decreasing order, oldest version has the highest version number and the latest
# version number will be 0
class Smell:
    def __init__(self, fileId, smell_type, category, pg, final_list):
        self.fileId = fileId
        self.exception_files = []
        self.category = category
        self.smell_type = smell_type  # FU:7,IC:8, LM=9, LPL=10
        self.tInit = None
        self.projectGroup = pg
        self.currentVersion = None
        self.versionCount = 0
        self.first=0 # boolean to track if smell is introduced in the first version
        self.last = 0  # boolean to indicate if a smell is persisted to the last version
        self.tFinal = None
        self.status = 0  # only 1 when a smell is fixed or not present anymore on a version
        self.finish_tracking = False
        self.version_break = False  # variable to be cheked at finialize if the file has smell or not
        self.final_list = final_list

    def update_data(self, row, total_versions, first):
        #f irst indicates the oldest version and last indicates the newst version
        if row[self.smell_type] > 0:

            if self.currentVersion is not None and (self.currentVersion - 1 != row['version']):
                # version break
                self.status = 0
                # store record
                self.store_record()
                return 1
            # smell occured or persisits
            if self.tInit is None:
                # smell occured
                self.tInit = self.tFinal = row['_date']
                self.versionCount = self.versionCount + 1
                self.currentVersion = row['version']
                if first:
                    self.first=1
                return 0  # continue
            else:  # smell persists
                self.tFinal = row['_date']
                self.versionCount = self.versionCount + 1
                self.currentVersion = row['version']
                # if it percisitis to final version then set the flag to censored
                if self.versionCount == total_versions:
                    self.status = 0  # censored data
                    self.last=1
                    # store record
                    self.store_record()
                    return 1
                return 0
        else:
            if self.currentVersion is not None and (self.currentVersion - 1 != row['version']):
                # version break
                self.status = 1
                # store record
                self.store_record()
                return 1
            # smell not occur yet or it is fixed
            self.versionCount = self.versionCount + 1
            self.currentVersion = row['version']
            if self.tInit is None:
                # smell not occured yet move on to next iteration if there is
                return 0  # continue
            else:  # smell is fixed
                self.tFinal = row['_date']
                self.status = 1
                if self.versionCount == total_versions and self.currentVersion != 0:  # for cases whose life ends before
                    # version 0
                    self.exception_files.append(self.fileId)
                # store record
                self.store_record()
                return 1

    def store_record(self):
        self.finish_tracking = True
        if self.tFinal == self.tInit:
            return

        row = self.format_output()
        self.final_list.append(row)

    def format_output(self):
        row = []
        row.append(self.fileId)
        row.append(self.projectGroup)
        row.append(self.category)
        row.append(self.smell_type)
        row.append(self.status)
        row.append(self.tInit)
        row.append(self.tFinal)
        row.append(self.first)
        row.append(self.last)
        print(row)
        return row


def main ():
    ############## Arg parse #########
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--smellName", help="Smell Name to run on")
    df = pd.read_csv("survivial_combined_data.csv")
    args = parser.parse_args()
    # lets create object lists to hold for each type of smell
    fear_un = []
    long_method = []
    long_pl = []
    # get file_ID, get data by fileId, create 4 smells, total length of files, 3818
    pysql = lambda q: sqldf(q, globals())
    fileIDs = df.file_id.unique()
    count = 0
    smell_fu=None
    for fileId in fileIDs:
        query = "select * from df where file_id='{}' order by version desc".format(fileId)
        dft = pysql(query)
        count = count + 1
        total_version= len(dft.index)
        if not dft.empty:  # fileId,smell_type, category
            cat = dft.iloc[0]['category']
            pg = dft.iloc[0]['projectGroup']
            smell_fu = Smell(fileId, args.smellName, cat, pg, fear_un)
            for index, row in dft.iterrows():
                first=False
                if index==0:
                    first=True
                res=smell_fu.update_data(row, len(dft.index),first)
                if res == 1:
                    break #remove redendunt files
            print("Done for {} {}/{}".format(fileId, count, fileIDs.size))
    if smell_fu is not None:
        df_out=pd.DataFrame(smell_fu.final_list, columns=['file_id','projectGroup','category','smellType','status','tInit','tFinal','first','last'])
        df_except=pd.DataFrame(smell_fu.exception_files, columns=['fileId'])
        df_except.to_csv(args.smellName + "_exceptions.csv", index=False)
        df_out.to_csv(args.smellName+ "_survivial.csv", index=False)


if __name__ == '__main__':
    main()