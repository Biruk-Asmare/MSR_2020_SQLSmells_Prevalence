import requests
import dbConnect as db
import time
import threading
tokens= []
headers = {"Authorization": "token %s" % tokens[0]}
TotalProjects=0
def runner_in_thread(token,id):
    dbase = db.DB()
    db_cursor, conn = dbase.connect_mysql()
    #urls = read_url_from_database(db_cursor, dbase)
    urls = read_url_from_database(db_cursor,dbase)
    TotalProjects=len(urls)

    header = {"Authorization": "token %s" % token}
    final_index=0
    for index, url in enumerate(urls):
        if index % 8 == id:
            final_index=index
            for indK, key in enumerate(keywords):
                remaining, reset = get_rate_limit(header)
                if remaining < 1:
                    print("sleeping for "+str(reset - time.time()))
                    time.sleep(abs(reset+2 - time.time()))
                else:
                    res = run_query(key, "java", url, header)

                    try:
                        if res['total_count'] >= 1:
                            key_label= set_keyword(indK)
                            print(key_label)
                            add_project_to_selected_projects(url, key_label, dbase, db_cursor, conn,id)

                            break
                    except:
                        if res['message'].startswith("You have triggered an abuse detection"):
                            print("Sleeping rate limit abused...sleeping for 3 minutes ")
                            time.sleep(180)
                            print(res['message'])
                            print(url)
        update_status_sampleProjects(url, dbase, db_cursor, conn)
        print("Thread {} finished {}/{}".format(id, final_index, TotalProjects))
def set_keyword(index):
    keyword=""
    if index >=0 and index <= 2:
      keyword="android"
    elif index >=3 and index <= 7:
        keyword="hibernate"
    elif index >=8 and index <= 11:
        keyword="spring"
    elif index >=12 and index <= 14:
        keyword="jpa"
    elif index == 15 or index == 16:
        keyword="jdbc"
    return keyword

def runner_in_thread_for_selected(token,id):
    dbase = db.DB()
    db_cursor, conn = dbase.connect_mysql()
    #urls = read_url_from_database(db_cursor, dbase)
    urls = read_url_from_database_selected_projects(db_cursor,dbase)
    header = {"Authorization": "token %s" % token}
    final_index=0;
    for index, url in enumerate(urls):
        if index % 8 == id:
            final_index=index
            for key_index, key in enumerate(keywords):
                remaining, reset = get_rate_limit(header)
                if remaining < 1:
                    print("sleeping for "+str(reset - time.time()))
                    time.sleep(abs(reset+2 - time.time()))
                else:
                    res = run_query(key, "java", url, header)

                    try:
                        if res['total_count'] >= 1:
                            print(key)
                            if key_index == 0:
                                set_selected_project_type(url, "Android", dbase, db_cursor, conn,id)
                                break
                            elif key_index == 1:
                                set_selected_project_type(url, "Hibernate", dbase, db_cursor, conn,id)
                                break
                            elif key_index == 2:
                                set_selected_project_type(url, "JPA", dbase, db_cursor, conn, id)
                                break
                            elif key_index == 3:
                                set_selected_project_type(url, "Spring", dbase, db_cursor, conn,id)
                                break
                            elif key_index == 4:
                                set_selected_project_type(url, "JDBC", dbase, db_cursor, conn, id)
                                break

                    except:
                        if res['message'].startswith("You have triggered an abuse detection"):
                            print("Sleeping rate limit abused...sleeping for 3 minutes ")
                            time.sleep(180)
                            print(res['message'])
                            print(url)

        print("<"+str(id)+"> Finished index <" + str(final_index) + ">")
        update_status_sampleProjects(url, dbase, db_cursor, conn)



def run_query(keyword, language, url, headers):
    #remove the web address from URL
    repo=url.replace("https://github.com/","")

    query="https://api.github.com/search/code?q={} in:file language:{} repo:{}"
    query= query.format(keyword,language,repo)
    #print(query)

    response = requests.get(query,  headers=headers)
    return response.json()
        #return ""



keywords= ['android.database.sqlite.SQLiteDatabase','android.database.DatabaseUtils','android.database.sqlite.SQLiteStatement',
           'org.hibernate.Session', 'org.hibernate.SharedSessionContract','org.hibernate.SharedSessionContract','org.hibernate.Query','org.hibernate.SQLQuery',
           'org.springframework.orm.hibernate.HibernateTemplate', 'org.springframework.orm.hibernate3.HibernateTemplate','org.springframework.orm.hibernate4.HibernateTemplate','org.springframework.orm.hibernate5.HibernateTemplate',
           'javax.persistence.EntityManager','javax.persistence.Query','javax.persistence.TypedQuery',
            'java.sql.Statement','java.sql.PreparedStatement']


def read_url_from_database(cursor, db_obj):
    urls=[]
    query = "SELECT Sample_Projects.projectUrl FROM `Sample_Projects` WHERE Sample_Projects.status='found' ORDER BY Sample_Projects.projectUrl"
    rows = db_obj.execute_read_query(cursor, query)
    for r in rows:
        urls.append(r[0])  # store each class name in the class name list
    return urls

def read_url_from_database_selected_projects(cursor, db_obj):
    urls=[]
    query = "SELECT selctedProjects.project_url FROM `selctedProjects`"
    #query= "SELECT * FROM `selctedProjects` WHERE selctedProjects.project_type=''"
    rows = db_obj.execute_read_query(cursor, query)
    for r in rows:
        urls.append(r[0])  # store each class name in the class name list
    return urls

def add_project_to_selected_projects(url,key_label,dbase,curser,connection,id):
    query = "INSERT INTO `selctedProjects`(`projectUrl`,`projectType`,`status`) VALUES ('{}','{}','selected')"
    query = query.format(url, key_label)
    res = dbase.execute_query(curser, query, connection)
    if res is not None:
        print(res)

    print(""+str(id)+": "+ url)
def update_status_sampleProjects(url, dbase, cursor, connection):
    query= "UPDATE Sample_Projects SET Sample_Projects.status='tested' WHERE Sample_Projects.projectUrl='{}'".format(url)
    res = dbase.execute_query(cursor, query, connection)
    if res is not None:
        print("Update status method "+str(res))


def set_selected_project_type(url,keyword,dbase,curser,connection, id):
    query = "UPDATE `selctedProjects` SET `project_type`='{}' WHERE selctedProjects.project_url='{}'"
    query = query.format(keyword,url)
    res = dbase.execute_query(curser, query, connection)
    if res is not None:
        print(res)
    print("" + str(id) + ": " + keyword + " : " +url)

def get_rate_limit(header):
    response = requests.get('https://api.github.com/rate_limit',headers=header)
    res=response.json()
    remaining= int(res['resources']['search']['remaining'])
    reset=int(res['resources']['search']['reset'])
    return remaining, reset


def main():

    #### create 8 threads to run in parallel
    threads = list()
    for i in range(0,8):
        #thread = threading.Thread(target=runner_in_thread, args=(tokens[i], i))
        thread = threading.Thread(target=runner_in_thread, args=(tokens[i], i))
        threads.append(thread)
        thread.start()
    for t in threads:
         t.join()


if __name__ == "__main__":
    main()
