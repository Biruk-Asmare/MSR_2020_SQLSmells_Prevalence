from pathlib import Path
import xml.etree.ElementTree as et
import dbConnect as db #contains class DB for database connection
import Config
def getId(className, projectName,db_obj, cursor):
    #correct the format of the className
    className.rstrip('.java')
    query = "SELECT file_history.fileID FROM `file_history` WHERE file_history.className LIKE '%{}%' AND file_history.projectName LIKE '%{}%'".format(className, projectName)
    res = db_obj.execute_read_query(cursor, query)
    if(cursor.rowcount==0):
        return -1
    else:
        return res[0][0]
def store_mysql_smell(file_name, projectGroup, projectName,  cursor, conn, dbObj,version, folder_path,file):
    xml_file=Path(folder_path+"/" + file_name)
    if xml_file.exists():
        tree=et.parse(xml_file)
        root=tree.getroot() #rerturn the root of the xml file
        #<Kind>IMPLICIT_COLUMNS</Kind>
    # elements order: kind(0) File(1) <Line>(2) <Certainty(3)<Message>(4)
        for smells in root:
            write_to_DB(cursor, conn, dbObj, smells, projectName,projectGroup, version,file)
    else:
        print(xml_file.name+ " does not exit")



def write_to_DB(cursor, conn, dbObj, smells, projectName,projectGroup, version,file):
    # split the path to get the class name or Sql file name
    if "_src/" in smells[1].text:
        tokens = smells[1].text.split("_src/")

    elif "_java/" in smells[1].text:
        tokens = smells[1].text.split("_java/")
    elif "src/" in smells[1].text:
        tokens = smells[1].text.split("src/")
    else:
        tokens=smells[1].text.split("/")
        tokens2= tokens[1].split("/")
        tokens[1]= tokens2[len(tokens2)-2] + "/" + tokens2[len(tokens2)-1]
    fileId = getId(tokens[1], projectName,dbObj,cursor)
    if fileId == -1:
        file.write("{}:,{},{},{}\n".format(smells[0].text,projectName, version,tokens[1]))
        return
    msg = smells[4].text.replace("'", "")
    query = "INSERT INTO sqlsmell (`fileID`,`projectGroup`,`version`,`projectName`,`kind`,`className`,`file`,`line`,`certainity`,`message`) VALUES ('{}','{}','{}','{}','{}','{}','{}','{}','{}','{}')".format(fileId,projectGroup, version,projectName, smells[0].text,tokens[1],smells[1].text, str(smells[2].text), smells[3].text, msg )
    res=dbObj.execute_query(cursor, query, conn)
    print(res)
