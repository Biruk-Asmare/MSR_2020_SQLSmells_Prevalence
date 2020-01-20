import os
import threading
import logging

import dbConnect as db
from pydriller import RepositoryMining, GitRepository
import subprocess
import BugStructure as bug
from subprocess import PIPE
import csv
import argparse
'''SELECT DISTINCT ProjectInformation.url
FROM ProjectInformation
WHERE ProjectInformation.projectName in (
select DISTINCT projectName FROM sqlquery)'''

urls=[]
projects=[]
def read_csv_for_urls(fileName):
    with open(fileName) as csv_file:
        content = csv.reader(csv_file, delimiter=',')
        for r in content:
            urls.append(r[0])
            #projectGroups.append(r[1])
    print("Done reading CSV file")
def clone_repo(url,path):
    folder=url.lstrip('https://github.com/')
    folder=folder.replace('/','_')

    command = "git clone {} {}".format(url, path+"/"+folder)
    result = subprocess.run(command, stdout=PIPE, stderr=PIPE, shell=True, encoding='Utf-8')
    print(result.stdout + result.stderr)
    print("Done: {}".format(url))


count=0
bugs = ["fixed ", " bug", "fixes ","fix ",
        " fix", " fixed", " fixes", "crash","solves", " resolves",
"resolves ", " issue", "issue ", "regression", "fall back", "assertion", "coverity", "reproducible",
"stack-wanted", "steps-wanted", "testcase", "failur", "fail", "npe ",
" npe", "except", "broken", "differential testing", "error", "addresssanitizer",
"hang ", " hang", "permaorange", "random orange", "intermittent", "test fix",
"steps to reproduce", "crash", "assertion", "failure", "leak", "stack trace", "heap overflow",
        "freez", "str:", "problem ", " problem", " overflow", "overflow ", "avoid ",
        " avoid",  "workaround ", " workaround", "break ", " break", " stop", "stop "];
pattern='(“fix” or “solve”) and (“bug” or “issue” or “problem” or “error”'
#



def getDetailsOfInduceCommit(db_obj,cursor,conn,project_name, gr,sha):
    commit= gr.get_commit(sha)
    # def __init__(self,db_name, bug_inducing_commit_id,project_name,message,commit_date, author_name, author_email)

    if commit.modifications is None:
        return
    bug_induce = bug.BugInduce(db_obj,cursor,conn, sha, project_name, commit.msg, commit.committer_date,
                               commit.author.name, commit.author.email)
    bug_induce.insert_into_database()  # insert bug induce file
    for modified_file in commit.modifications:
        # print("{} Modified files: {}".format(commit.hash,modified_file.new_path))
        if modified_file.filename.endswith('.java'):
            churn = modified_file.added + modified_file.removed
            bug_ind_file=bug.BugInduceFile(db_obj,cursor,conn,sha,modified_file.new_path,churn)
            bug_ind_file.insert_into_database() #insert in to bug induce file
        #self, db_name, induce_commit_id, file_name, diff_added, diff_deleted
def run_for_one_project(db_name,project_name, repo_path,thread_id=0):
    db_obj = db.DB()
    db_obj.set_db_name(db_name)
    cursor, conn = db_obj.connect_mysql()
    gr = GitRepository('{}/{}'.format(repo_path, project_name))
    totalCommits = gr.total_commits()
    count = 0
    try:
        for commit in RepositoryMining('{}/{}'.format(repo_path, project_name),
                                       only_modifications_with_file_types=['.java']).traverse_commits():
            msg = commit.msg.lower()  # convert the commit message to lower case
            for key in bugs:
                # def __init__(self,db_name, commit_id,project_name,message,identification_key,commit_date, author_name, author_email):
                if key in msg:
                    # print("{}:{}:{}".format(key, msg, commit.hash))
                    bugfix = bug.BugFix(db_obj,cursor,conn, commit.hash, project_name, msg, key, commit.committer_date,
                                        commit.author.name, commit.author.email)
                    bugfix.insert_into_database()  # insert bugfix
                    for modified_file in commit.modifications:
                        if modified_file.filename.endswith('.java'):
                            # print("{} Modified files: {}".format(commit.hash,modified_file.new_path)
                            churn = modified_file.added + modified_file.removed
                            bug_fix_file = bug.BugFixFile(db_obj,cursor,conn, commit.hash, modified_file.new_path, churn)
                            bug_induce_commits = gr.get_commits_last_modified_lines(commit, modified_file)
                            bugfix.set_induce_commits(bug_induce_commits.get(modified_file.new_path))
                            # at this point you can insert bug fix and modified files
                            bugfix.insert_into_bug_fix_induce()  # insert bug fix induce
                            bug_fix_file.insert_into_database()  # insert bug fix file
                            try:
                                for ind_commit in bug_induce_commits.get(modified_file.new_path):
                                    getDetailsOfInduceCommit(db_obj,cursor,conn, project_name, gr, ind_commit)
                            except:
                                print("no induce commits found")
                    break

            count = count + 1
            if count%100==0:
                print("Thread {}: Done processing: {} {}/{}".format(thread_id,commit.hash, count, totalCommits))
        db_obj.close_connection(conn)
    except:
        print("Exception occured")
def init_project_folders(repo_path):
    for project in os.scandir(repo_path):
        projects.append(project.name)
    print("Done scanning. {} projects".format(len(projects)))


def thread_runner(id,db_name,repo_path,logger):
    for index, project in enumerate(projects):
        if index%3==id:
            run_for_one_project(db_name,project,repo_path,id)
            print("{},{}/{}".format(project, index + 1, len(projects)))
            logger.info("{},{}/{}".format(project,index+1,len(projects)))
def batch_runner(db_name, repo_path,log_file):
    logpath = log_file
    logger = logging.getLogger('log')
    logger.setLevel(logging.INFO)
    ch = logging.FileHandler(logpath)
    ch.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(ch)

    ###init project folders
    init_project_folders(repo_path)
    #### create 8 threads to run in parallel
    threads = list()
    for i in range(0, 3):
        # thread = threading.Thread(target=runner_in_thread, args=(tokens[i], i))
        thread = threading.Thread(target=thread_runner, args=(i,db_name,repo_path,logger))
        threads.append(thread)
        thread.start()
    for t in threads:
        t.join()
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--repoPath", help="path for repository clone")
    parser.add_argument("-d", "--db_name", help="Database name", default="")
    parser.add_argument("-pn", "--project_name", help="ProjectName", default="")
    parser.add_argument("-c","--clone",help=" c for Clonning mode", default="NC")
    parser.add_argument("-b", "--batch", help=" b for Batch mode to run the script for multiple projects in parallel", default="NC")
    parser.add_argument("-u", "--url_file", help="FileName for the url list", default="")
    args = parser.parse_args()
    if args.clone == 'c':
        read_csv_for_urls(args.url_file)
        for url in urls:
            clone_repo(url, args.repoPath)
    if args.batch == 'b':
        batch_runner(args.db_name,args.repoPath,'finishedProjects.log')

if __name__ == '__main__':
    main()
