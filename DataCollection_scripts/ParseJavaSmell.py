import dbConnect as db #contains class DB for database connection
import Config
import os
import re
from pathlib import Path

def getId(className, projectName,db_obj, cursor):
    #correct the format of the className
    className=className.rstrip('.java')
    className=className.replace('.','/')
    query = "SELECT file_history.fileID FROM `file_history` WHERE file_history.className LIKE '%{}%' AND file_history.projectName LIKE '%{}%'".format(className,projectName)
    res = db_obj.execute_read_query(cursor, query)
    if(cursor.rowcount==0):
        print(res)
        return -1, className
    else:
        return res[0][0], className

def get_all_codesmell_files_from_folder(folder):
    smellFiles = []
    for file in os.listdir(folder):
        if file.endswith(".ini"):
            smellFiles.append(os.path.join(folder , file))
    return smellFiles

def parse_java_smells(cursor, conn, dbObj,files, projectName, projectGroup, version,_file):
    for file in files:
        with open(file ,'r') as fp:

            tokens= file.split(" ")
            smellType= tokens[len(tokens)-1].strip(".ini")

            lines = fp.read()
            parse_and_store_content_from_line(cursor, conn, dbObj, lines, smellType, projectName, projectGroup, version,_file)
def getPathName(match):
    pathName = match + '.java'
    return pathName


def parse_and_store_content_from_line(cursor, conn, dbObj, lines, smellType, projectName, projectGroup,version,file):
    regex = r"[^LOC]-\d = ([a-z\d]+\..*)"
    regex_method = r"MethodName-0 = (.*)"

    #print(lines)

    matches = re.findall(regex, lines, re.MULTILINE | re.IGNORECASE)
    matches_method= re.findall(regex_method, lines, re.MULTILINE | re.IGNORECASE)
    pathName=className=methodName=""
    content=""

    if len(matches_method) > 0:
        #print(str(len(matches_method)))
        for matchNum, match in enumerate(matches):

            try:

                methodName = matches_method[matchNum]
                #print(methodName)
                methodName='"'+methodName+'"'

                contnet = match+ ":" + methodName + ":" + smellType
                write_to_database(cursor, conn, dbObj, contnet, projectName, projectGroup, version,file)
            except:
                methodName=""

                contnet = match+ ":" + methodName + ":" + smellType

                write_to_database(cursor, conn, dbObj, contnet, projectName, projectGroup, version,file)

    else:
        for matchNum, match in enumerate(matches):

            methodName = ""

            contnet = match + ":" + methodName + ":" + smellType

            write_to_database(cursor, conn, dbObj, contnet, projectName, projectGroup, version,file)

    return


    

def write_to_database(cursor, conn, dbObj, content, projectName, projectGroup, version,file):

    fields= content.split(":")
    toks= fields[0].split('.')
    className = toks[len(toks)-1] + '.java'
    try:
        val = float(fields[0])
        return
    except ValueError:
        fileId, cla= getId(fields[0],projectName, dbObj,cursor)
        if fileId==-1:
            file.write("{},{},{}\n".format(projectName, version, cla))
            print(cla + ":" + projectName+"not found")
            return
        query = "INSERT INTO `codeSmell`(`fileID`,`version`,`projectName`,`projectGroup`,`classPath`, `className`, `methodName`, `smellType`, `status`) VALUES ('{}','{}','{}','{}','{}','{}','{}','{}','{}')".format(fileId,version, projectName,projectGroup,fields[0], className,fields[1],fields[2],"not_tested")
        res=dbObj.execute_query(cursor, query, conn)




def parseJavaSmell(cursor,conn, db_obj,projectName,projectGroup, version, folder_path,file):

    smellFiles = get_all_codesmell_files_from_folder(folder_path)
    parse_java_smells(cursor,conn, db_obj, smellFiles, projectName, projectGroup, version,file)
