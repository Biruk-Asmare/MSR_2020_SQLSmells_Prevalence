import requests
import time
import datetime
import dbConnect as db
import argparse


headers = {"Authorization": "token %s" % ""}

repoCount = ""
remaining = ""
resetAt = ""
cursor = ""
currentCount = 0

f = open("filterd_repo.csv", "a")
def run_query(query):
    response = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        #raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))
        print(response.json())
        return ""


def extract_helper_info(result):
    global repoCount, remaining, resetAt, cursor
    repoCount = result['data']['search']['repositoryCount']
    remaining = result['data']['rateLimit']['remaining']
    resetAt = result['data']['rateLimit']['resetAt']
    cursor= result['data']['search']['pageInfo']['endCursor']
def init_variables(keyword="",language='java',min_forks=10, min_stars=10):
    query = """
        {
          rateLimit {
            limit
            cost
            remaining
            resetAt
          }
          search(query: " """+keyword+"""language:"""+language+"""  is:public forks:>"""+str(min_forks)+""" stars:>"""+str(min_stars)+"""", type: REPOSITORY, first:100) {

            repositoryCount
            pageInfo {
              endCursor
              startCursor
              hasNextPage
            }
            edges  {
              node  {
                ... on Repository {
                  name
                  hasIssuesEnabled
                  url
                  forks{
                    totalCount
                  }
                  stargazers{
                    totalCount
                  }


                 }
              }
            }
          }
        }
        """

    result= run_query(query)
    extract_helper_info(result)
    return result

def filter_results(result, dbase, cursor, conn, keyword):
    edges = result['data']['search']['edges']
    count=0
    for edge in edges:
        if edge['node']['hasIssuesEnabled']==True:
            upload_filtered_projects_to_DB(edge['node']['name'], keyword, edge['node']['url'],edge['node']['stargazers']['totalCount'], edge['node']['stargazers']['totalCount'],dbase, cursor, conn)
        count = count + 1
    global currentCount
    currentCount = currentCount+count
def search_repository(after,keyword="",language='java',min_forks=10, min_stars=10):
    after='"'+after+'"'
    query = """
    {
      rateLimit {
        limit
        cost
        remaining
        resetAt
      }
      search(query: " """+keyword+"""language:"""+language+"""  is:public forks:>"""+str(min_forks)+""" stars:>"""+str(min_stars)+"""",  type: REPOSITORY, after:"""+after+"""
  first:100) {

        repositoryCount
        pageInfo {
          endCursor
          startCursor
          hasNextPage
        }
        edges  {
          node  {
            ... on Repository {
              name
              hasIssuesEnabled
              url
              forks{
                    totalCount
                  }
              stargazers{
                totalCount
              }


             }
          }
        }
      }
    }
    """
    result = run_query(query)
    return result



def upload_filtered_projects_to_DB(name, keyword, url,star,fork, dbase,curser,connection):

    query = "INSERT INTO `Sample_Projects`( `projectName`, `projectUrl`, `stars`, `forks`, `usedKeyword`,`status`) VALUES ('{}','{}','{}','{}','{}','found')".format(name,url,str(star), str(fork),keyword)
    res=dbase.execute_query(curser, query, connection)
    if res is not None:
        print(str(res))


#pprint.pprint(result)

#print(resetAt)
#

#print(str(restTime-(time.time()+4*3600))) #account for time zone differences


def main():
    ############## Arg parse #########
    parser = argparse.ArgumentParser()
    parser.add_argument("-k","--keyword",help="Keyword to search through repositories", default=" ")
    parser.add_argument("-l","--language", help="language of the repository", default="java")
    parser.add_argument("-ms", "--min_star", help="Minimum number of stars", type=int, default=10)
    parser.add_argument("-mf", "--min_fork", help="Minimum number of forks", type=int, default=10)
    args=parser.parse_args()
    dbase = db.DB()
    db_cursor, conn = dbase.connect_mysql()
    print("Connection successful")
    #res = init_variables()  #keyword="android app",min_stars=2, min_forks=2
    res=init_variables(keyword=args.keyword, language=args.language, min_forks=args.min_fork, min_stars=args.min_star)
    #res=init_variables(keyword="android app",min_stars=2, min_forks=2)
    extract_helper_info(res)
    filter_results(res,dbase, db_cursor, conn,args.keyword)

    while currentCount < repoCount and currentCount < 1000:
        print(str(currentCount) + "/" + str(repoCount))
        print("Cursor position: " + str(cursor))
        if remaining > 0:
            res=search_repository(cursor, keyword=args.keyword, language=args.language, min_forks=args.min_fork, min_stars=args.min_star)
            #res = search_repository(cursor,keyword="android app",min_stars=2, min_forks=2)
            extract_helper_info(res)
            filter_results(res,dbase, db_cursor, conn, args.keyword)
            #print("Cursor position: " + str(cursor))
            #print(res)
        else:
            restTime = time.mktime(datetime.datetime.strptime(resetAt, '%Y-%m-%dT%H:%M:%SZ').timetuple())
            print("Sleeping until the rate limit is reset")
            time.sleep(restTime + 2 -(time.time()+4*3600)) #2seconds is just to make sure
    conn.close()
    print("I am done")

if __name__ == "__main__":
    main()
