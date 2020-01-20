from pathlib import Path
import xml.etree.ElementTree as et
import dbConnect as db #contains class DB for database connection
import Config
import uuid

def getId(className,projectName,db_obj, cursor):
    #correct the format of the className
    className=className.rstrip('.java')
    className=className.replace('.','/')
    query = "SELECT file_history.fileID FROM `file_history` WHERE file_history.className LIKE '%{}%' AND file_history.projectName LIKE '%{}%'".format(className,projectName)
    res = db_obj.execute_read_query(cursor, query)
    if(cursor.rowcount==0):
        return -1
    else:
        return res[0][0]
def store_mysql_query(file_name, projectName, cursor, conn, dbObj, projectGroup, version, folder_path,file):
    xml_file = Path(folder_path+"/"+file_name)

    if xml_file.exists():
        tree = et.parse(xml_file)
        root = tree.getroot()  # rerturn the root of the xml file
        # <Kind>IMPLICIT_COLUMNS</Kind>
    # elements order: kind(0) File(1) <Line>(2) <Certainty(3)<Message>(4)
        for queries in root:
            write_to_DB(cursor, conn, dbObj, queries,projectName,projectGroup, version,file)

    else:
        print(xml_file.name + " does not exit")
def fix_class_names(classname):
    try:
        tokens= classname.split(":/")
        className = tokens[1].replace("/", ".")
        className = tokens[0] + ":" + className
    except IndexError:
        tokens = classname.split(":")
        className = tokens[1].replace("/", ".")
        className = tokens[0] + ":" + className
    return  className

def extract_class_name(path, projectName):
    # split the path to get the class name or Sql file name
    tokens = path.split("_src/")
    className = tokens[len(tokens)-1]
    return className


def write_to_DB(cursor, conn, dbObj, queries, projectName, projectGroup, version, file):

    query_id = str(uuid.uuid4())  # id to use as primary key
    if queries[0].text is None:
        msg = "{{na}}"
    else:
        msg = queries[0].text.replace("'", "")
#special code needs to be removed needed only for adempire

    execClass=extract_class_name(queries[4].text, projectName)
    print(execClass)
    if queries[2].text is None or queries[3].text is None:
       try:
        exec = queries[4].text
        if "_src/" in exec:
            tokens = exec.split("_src/")
            path=tokens[1]
        elif "_java/" in exec:
            tokens = exec.split("_java/")
            path = tokens[1]
        elif "src/" in exec:
            tokens = exec.split("src/")
            path = tokens[1]
        else:
            tokens = exec.split("/")
            tokens2 = tokens[1].split("/")
            tokens[1] = tokens2[len(tokens2) - 2] + "/" + tokens2[len(tokens2) - 1]
            path=tokens[1]
       except ValueError:
            exit("Exited"+exec)
    else:
        path2=""+queries[2].text+"."+queries[3].text
        path=path2.replace(".",'/')

    fileId = getId(path, projectName,dbObj, cursor)
    print("Smells"+path)
    if fileId == -1:
        file.write("Query: {},{},{}\n".format(projectName, version, path))
        print(path + " id not found")
        return
    query_to_insert_query = "INSERT INTO `sqlquery`(`fileID`,`version`,`projectGroup`,`projectName`,`queryId`, `value`, `execClassPath`, `execClass`, `execLine`, `execString`,`HotspotFinder`,`status`) VALUES ('{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}')".format(fileId,version,projectGroup, projectName, query_id,dbObj.escape_string(msg),path, execClass, str(queries[5].text),dbObj.escape_string( queries[6].text),queries[1].text,"not_tested")
    res=dbObj.execute_query(cursor, query_to_insert_query, conn)
    print(res)

    for calls in queries[7]:

        query_to_insert_callstack = "INSERT INTO `query_stack`(`version`,`projectName`,`query_id`, `method_full_name`, `class_path`, `class_name`, `line`) VALUES ('{}','{}','{}','{}','{}','{}','{}')".format(version, projectName, query_id, dbObj.escape_string(calls.attrib['method']), path,execClass, str(calls.attrib['methodLine']))

        dbObj.execute_query(cursor, query_to_insert_callstack, conn)


def parseQuery(fileName, cursor, conn, db_obj, projectName, projectGroup, version, folder_path,file):
    store_mysql_query(fileName, cursor, conn, db_obj, projectName, projectGroup,version,folder_path,file)
