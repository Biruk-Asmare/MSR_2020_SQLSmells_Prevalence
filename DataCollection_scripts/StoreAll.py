from pathlib import Path
import dbConnect as db #contains class DB for database connection
import Config
import re
import sys
import subprocess
import ParseJavaSmell as pjs
import ParseQuery as pc
import ParseSmell as ps
import argparse
import os
import csv
#arguments to pass
#projectName
#project path

def extract_xmlfile_name_from_path(path):
    tokens=path.split('/')
    return tokens[len(tokens)-1]
#Add a function that filters file names of xml files for queries and codeSmell
def get_Xml_file_names(path):
    out = subprocess.Popen(['find', path, '-name', '*.xml'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, stderr= out.communicate()
    lists= stdout.decode().split('\n')
    queries=""
    smells=""
    for f in lists:
        if 'queries' in f:
            queries= extract_xmlfile_name_from_path(f)
        elif 'sqlsmells' in f:
            smells= extract_xmlfile_name_from_path(f)
    return queries, smells
#validate input arguments

def separate_project_name_version(project):
    tokens= project.split("_")
    version= tokens[len(tokens)-1]
    #projectName= re.sub('\_-?\d','',project)
    return version


projectNames=[]
versions=[]

def read_csv_for_projects(fileName):
    with open(fileName) as csv_file:
        content = csv.reader(csv_file, delimiter=',')
        for r in content:
            projectNames.append(r[0])
    print("Done reading CSV file")
def collect_versions_of_project(project):
    command = "ls "+project
    out = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='UTF-8')
    stdout, stderr = out.communicate()
    versions=stdout.rstrip().split("\n")
    return versions
def select_projects_from_databasee(db_obj,cursor):
    query="SELECT projectName, version FROM ProjectInformation WHERE ProjectInformation.status ='ready' ORDER BY ProjectInformation.projectName ASC"
    res = db_obj.execute_read_query(cursor, query)
    if (cursor.rowcount == 0):
        return -1
    else:
        for row in res:
            projectNames.append(row[0])
            versions.append(row[1])

def set_status_analyzed(status,project,version, db_obj,cursor,conn):
    query="UPDATE ProjectInformation SET ProjectInformation.status='{}' WHERE ProjectInformation.projectName='{}' AND ProjectInformation.version='{}'".format(status,project,version)
    res = db_obj.execute_query(cursor, query, conn)
    return res
def main ():
    ############## Arg parse #########
    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--projectGroup", help="Project group jdbc, hibernate_spring, jpa or android")

    parser.add_argument("-f", "--failedCsv", help="Project lists in CSV format")
    parser.add_argument("-d", "--database", help="Database name")
    parser.add_argument("-p","--projectPath", help="The path of the project group")
    args = parser.parse_args()
    #read_csv_for_projects(args.projectCsv)
    db_obj = db.DB()
    db_obj.set_db_name(args.database)
    cursor, conn = db_obj.connect_mysql()
    projectGroup = args.projectGroup
    #load projects with no issues to dump to database
    select_projects_from_databasee(db_obj,cursor)
    missed_class=open(args.failedCsv,"a+")
    for index, proj in enumerate(projectNames):
        folderPath = args.projectPath + "/" + proj + "/" +proj+"_" + str(versions[index])
        if os.path.isdir(folderPath):
            print("Parsing {},{}".format(proj,versions[index]))
            #set_status_analyzed('analyzed',proj,versions[index],db_obj,cursor,conn)
            queryxml, smellxml = get_Xml_file_names(folderPath)
            try:
                ps.store_mysql_smell(smellxml, projectGroup, proj, cursor, conn, db_obj,versions[index], folderPath, missed_class)
                # print("Finished storing mysql smell")
                pc.parseQuery(queryxml, proj, cursor, conn, db_obj, projectGroup, str(versions[index]), folderPath,missed_class)
                # print("Finished storing mysql query")
                pjs.parseJavaSmell(cursor,conn, db_obj,proj, projectGroup, str(versions[index]), folderPath,missed_class)
                # print("Finished storing java smell")
                set_status_analyzed('parsed',proj,versions[index],db_obj,cursor,conn)
                print("{}/{} is parsed".format(proj,versions[index]))
            except:
                set_status_analyzed('notanalyzed', proj, versions[index], db_obj, cursor, conn)
        else:
            set_status_analyzed('notanalyzed',proj,versions[index],db_obj,cursor,conn)
            print(folderPath + "not analyzed")
    db_obj.close_connection(conn)
    missed_class.close()
    # except:
    # print("Error occured")
    # exit(1)


if __name__ == '__main__':
    main()
