import functions as fn
import psycopg2 as psy
import datetime
from time import sleep


# Assumptions About the Tests:
#   1. Unlike non-exisiting papers will return (1, None)
#   2. Deleting non-exisiting papers will be successfully done with return
#      value (0, None)
#   3. If we try to get tags of an non-exisiting paper, we return (1, None)

# Basic APIs
def check_signup(conn):
    print("Checking signup ...")
    #check if it puts the username and password into db
    (status, value) = fn.signup(conn, "test1", "test1")
    if (status, value) != (0, None): return False
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s AND password = %s",
        ("test1", "test1"))
    if not (cur.rowcount > 0): return False
    #check using existing username
    (status, value) = fn.signup(conn, "test1", "pass")
    if (status, value) != (1, None): return False
    cur.execute("SELECT * FROM users WHERE username = %s AND password = %s",
        ("test1", "pass"))
    if cur.rowcount != 0: return False
    print("PASS")
    return True

def check_login(conn):
    print("Checking login ...")
    fn.signup(conn, "test1", "test1")
    #check if an correct user name and pass and login
    (status, value) = fn.login(conn, "test1", "test1")
    if (status, value) != (0, None): return False
    #check the case username doesn't exits
    (status, value) = fn.login(conn, "non-exisiting", "pass")
    if (status, value) != (1, None): return False
    #check the case username exists but password is wrong
    (status, value) = fn.login(conn, "test1", "abs")
    if (status, value) != (2, None): return False
    print("PASS")
    return True

# Event related
def check_add_new_paper(conn):
    print("Checking add_new_paper ...")
    fn.signup(conn, "test1", "test1")
    cur = conn.cursor()
    #ensure: non-exisiting users cannot add papers
    (status, value) = fn.add_new_paper(conn, "non-exisit", "t","d","t",["tag"])
    if (status, value) != (1, None): return False
    #encure: user can add new paper and the db is consistent
    (status, value) = fn.add_new_paper(conn, "test1", "title1", "desc1", "text1", ["tag1", "tag2"])
    if status != 0:
        print("cannot add new papers")
        return False
    cur.execute("SELECT pid,begin_time FROM papers WHERE username = %s AND title = %s", ("test1", "title1"))
    if(cur.rowcount <= 0): return False
    result = cur.fetchone()
    if(value != result[0]): return False
    #check if the timestamp is correct
    if(result[1] > datetime.datetime.now()): return False
    if(datetime.datetime.now() - result[1] > datetime.timedelta(minutes=1)): return False
    print("PASS")
    #check the case where the same user post two papers using the same title
    (status, new_value) = fn.add_new_paper(conn, "test1", "title1", "desc1", "text1", ["tag1", "tag2"])
    if(status != 0): return False
    if(new_value == value): return False
    return True

def check_delete_paper(conn):
    print("Checking delete_paper ...")
    cur = conn.cursor()
    #delete an non exisiting paper
    (status, value) = fn.delete_paper(conn, -1)
    if (status,value) != (0, None): return False
    #delete an exixsting paper
    (status, value) = fn.delete_paper(conn, 2)
    if (status, value) != (0, None): return False
    cur.execute("SELECT * FROM papers WHERE pid = %s", (2,))
    if cur.rowcount != 0: return False
    print("PASS")
    return True

def check_get_paper_tags(conn):
    print("Checking get_paper_tags ...")
    fn.add_new_paper(conn, "test1", "paper1", "d", "t", ["tag1", "tag2"])
    pid = get_pid(conn, "test1", "paper1")
    #check if correctly implemented
    (status, value) = fn.get_paper_tags(conn, pid)
    if(status != 0): return False
    if(value != ["tag1", "tag2"]): return False
    #check the case where a paper doesnt have any tags
    fn.add_new_paper(conn, "test1", "paper1-1", "d", "t", [])
    pid = get_pid(conn, "test1", "paper1-1")
    (status, value) = fn.get_paper_tags(conn, pid)
    if(status != 0): return False
    if(value != []): return False
    #check the case if the pid does not exist
    (status, value) = fn.get_paper_tags(conn, -1)
    if(status, value) != (1, None): return False
    print("PASS")
    return True

# Vote related
def check_like_paper(conn):
    print("Checking like_paper ...")
    cur = conn.cursor()
    #create new user
    fn.signup(conn, "test100", "test100")
    #add new paper for the user
    fn.add_new_paper(conn, "test100", "paper100", "d", "t", "tag")
    #ensure: a user cannot like his or her own paper
    pid = get_pid(conn, "test100", "paper100")
    (status, value) = fn.like_paper(conn, "test100", pid)
    if (status, value) != (1, None): return False
    #add a new paper from another user
    fn.signup(conn, "test101", "test101")
    fn.add_new_paper(conn, "test101", "paper101", "d", "t", "tag")
    pid = get_pid(conn, "test101", "paper101")
    (status, value) = fn.like_paper(conn, "test100", pid)
    if (status, value) != (0, None): return False
    #ensure: paper liked is consistent with the database
    cur.execute("SELECT * FROM likes WHERE pid = %s AND username = %s", (pid, "test100"))
    if (cur.rowcount == 0): return False
    #ensure: a user cannot like a paper twice
    (status, value) = fn.like_paper(conn, "test100", pid)
    if (status, value) != (1, None): return False
    #all tests passed
    print("PASS")
    return True

def check_unlike_paper(conn):
    print("Checking unlike_paper ...")
    cur = conn.cursor()
    #create two users
    fn.signup(conn, "test102", "test102")
    fn.signup(conn, "test103", "test103")
    #add new paper for the second user
    fn.add_new_paper(conn, "test103", "paper103", "d", "t", "tag")
    pid = get_pid(conn, "test103", "paper103")
    #ensure: a user cannot like a paper he or she has not liekd
    (status, value) = fn.unlike_paper(conn, "test102", pid)
    if (status, value) != (1, None): return False
    fn.like_paper(conn, "test102", pid)
    #ensure: unlike function is consistent with database
    (status, value) = fn.unlike_paper(conn, "test102", pid)
    if (status, value) != (0, None): return False
    cur.execute("SELECT * FROM likes WHERE pid = %s AND username = %s", (pid, "test100"))
    if (cur.rowcount > 0): return False
    #ensure: a user cannot unlike a paper he or she already unliked
    (status, value) = fn.unlike_paper(conn, "test102", pid)
    if (status, value) != (1, None): return False
    #all tests passed
    print "PASS"
    return True

def check_get_likes(conn):
    print("Checking get_likes ...")
    #create three users
    fn.signup(conn, "test104", "test104")
    fn.signup(conn, "test105", "test105")
    fn.signup(conn, "test106", "test106")
    #create a new paper for one user
    fn.add_new_paper(conn, "test104", "paper104", "d", "t", "tag")
    pid = get_pid(conn, "test104", "paper104")
    #ensure: fail on non-exist paper
    (status, value) = fn.get_likes(conn, -1)
    if (status, value) != (1, None): return False
    #ensure: number of likes consistent with database
    (status, value) = fn.get_likes(conn, pid)
    if (status, value) != (0, 0): return False
    fn.like_paper(conn, "test105", pid)
    (status, value) = fn.get_likes(conn, pid)
    if (status, value) != (0, 1): return False
    #ensure: the function workes on more than 2 likes
    fn.like_paper(conn, "test106", pid)
    (status, value) = fn.get_likes(conn, pid)
    if (status, value) != (0, 2): return False
    #all tests passed
    print("PASS")
    return True


# Search related
def check_get_timeline(conn):
    print("Checking get_timeline ...")
    cur = conn.cursor()
    fn.signup(conn,"test1", "test1")
    #check the case where user haven't post any papers
    (status, value) = fn.get_timeline(conn, "test1", 10)
    if(status, value) != (0, []): return False
    #post some papers
    fn.add_new_paper(conn, "test1", "paper1-1", "d", "t", ["tag1-1"])
    fn.add_new_paper(conn, "test1", "paper1-2", "d", "t", ["tag1-2", "fun"])
    fn.add_new_paper(conn, "test1", "paper1-2", "d", "t", ["tag1-3", "nope"])
    #check if the user does not exists
    (status, value) = fn.get_timeline(conn, "non-exist", 10)
    if (status,value) != (1, None): return False
    #check if the return value is correct
    (status, value) = fn.get_timeline(conn, "test1", 2)
    if(status != 0): return False
    if(len(value)!=2): return False
    pids = [x[0] for x in value]
    if(pids != [3,2]): return Falss
    unames = [x[1] for x in value]
    if(unames != ["test1", "test1"]): return False
    timestamps = [x[3] for x in value]
    if(max(timestamps) != timestamps[0] or min(timestamps) != timestamps[1]): return False

    print("PASS")
    return True

def check_get_timeline_all(conn):
    print("Checking get_timeline_all ...")
    fn.signup(conn, "test2", "test2")
    fn.add_new_paper(conn, "test2", "paper2-1", "d", "t", ["tag2-1"])
    #check if the return value is correct
    (status, value) = fn.get_timeline_all(conn, 2)
    if(status != 0): return False
    if(len(value) != 2): return False
    pids = [x[0] for x in value]
    if(pids != [4,3]): return False
    unames = [x[1] for x in value]
    if(unames != ["test2", "test1"]): return False
    timestamps = [x[3] for x in value]
    if(max(timestamps) != timestamps[0] or min(timestamps) != timestamps[1]): return False
    #check the case where no paper postes at all
    fn.reset_db(conn)
    (status, value) = fn.get_timeline_all(conn, 10)
    if(status, value) != (0, []): return False
    print("PASS")
    return True

def check_get_most_popular_papers(conn):
    print("Checking get_most_popular_papers ...")
    fn.signup(conn, "test1", "test1")
    fn.signup(conn, "test2", "test2")
    #check the case where no papers are posted
    (status, value) = fn.get_most_popular_papers(conn,
        datetime.datetime.now()-datetime.timedelta(hours=1))
    if(status, value) != (0, []): return False

    fn.add_new_paper(conn, "test1", "paper1-1", "d", "t", [])
    fn.like_paper(conn, "test2", 1)
    #check the normal case
    (status, value) = fn.get_most_popular_papers(conn,
        datetime.datetime.now()-datetime.timedelta(hours=1))
    if(status !=0):return False
    if(len(value) != 1): return False
    tup = value[0]
    keys = [tup[0], tup[1], tup[2]]
    if(keys != [1, "test1", "paper1-1"]): return False
    #check the case where there are paper posted but begint_time filtered them out
    sleep(1)
    (status, value) = fn.get_most_popular_papers(conn,
        datetime.datetime.now()-datetime.timedelta(seconds=1))
    if(status, value) != (0,[]):return False
    print("PASS")
    return True

def check_get_papers_by_tag(conn):
    print("Checking get_paper_by_tag ...")
    fn.add_new_paper(conn, "test1", "paper1-2", "d", "t", ["tag1", "tag2"])
    fn.add_new_paper(conn, "test2", "paper2-1", "d", "t", ["tag1", "tag3"])
    #check the care for non-exisiting tags
    (status, value) = fn.get_papers_by_tag(conn, "non-exisit tag")
    if(status, value) != (0, []): return False
    #chekc normal cases and the content and order of the returned value
    (status, value) = fn.get_papers_by_tag(conn, "tag1")
    if(status != 0):return False
    if(len(value) !=2):return False
    unames = [x[1] for x in value]
    if(unames != ["test2", "test1"]): return False
    (status, value) = fn.get_papers_by_tag(conn, "tag2")
    if(status != 0 ): return False
    if(len(value) != 1): return False
    if(value[0][1] != "test1"): return False
    print("PASS")
    return True

def check_get_papers_by_keyword(conn):
    # Tested the cases where keywords are in title, description or text
    print("Checking get_papers_by_keyword ...")
    (dum, pid1) = fn.add_new_paper(conn, "test1", "keyword1", "d", "t", [])
    (dum, pid2) = fn.add_new_paper(conn, "test1", "p", "keyword1", "t", [])
    (dum, pid3) = fn.add_new_paper(conn, "test1", "p", "d", "keyword1", [])
    (dum, pid4) = fn.add_new_paper(conn, "test1", "p", "d", "t", ["keyword1"])
    (status, value) = fn.get_papers_by_keyword(conn, "keyword1", 2)
    if(status != 0): return False
    if(len(value) != 2): return False
    ans = [pid3, pid2]
    res = [x[0] for x in value]
    if(res != ans): return False
    # Tested the case where no papers have the keywords
    (status, value) = fn.get_papers_by_keyword(conn, "non-exisit")
    if(status, value) != (0, []): return False
    print("PASS")
    return True

def check_get_papers_by_liked(conn):
    print("Checking get_papers_by_liked ...")
    #   1. Tested the normal case
    fn.like_paper(conn, "test2", 2)
    fn.like_paper(conn, "test2", 4)
    fn.like_paper(conn, "test2", 5)
    fn.like_paper(conn, "test2", 6)
    (status, value) = fn.get_papers_by_liked(conn, "test2", 3)
    if(status != 0): return False
    if(len(value) != 3): return False
    pids = [x[0] for x in value]
    if(pids != [6,5,4]): return False
    #   2. Tested the case where the user hasn't like any paper.
    fn.signup(conn, "test5", "test5")
    (status, value) = fn.get_papers_by_liked(conn, "test5")
    if(status, value) != (0, []): return False
    #   3. Tested non-exisiting users
    (status, value) = fn.get_papers_by_liked(conn, "non-exisiting")
    if(status, value) != (1, None): return False
    print("PASS")
    return True

def check_get_recommend_papers(conn):
    print("Checking get_recommend_papers ...")
    fn.reset_db(conn)
    #   1. Tested the case where nobody has liked the same paper as the user
    fn.signup(conn, "user", "user")
    fn.signup(conn, "test1", "test1")
    fn.signup(conn, "test2", "test2")
    fn.signup(conn, "test3", "test3")
    (dum, pid1) = fn.add_new_paper(conn, "test1", "p1", "d", "t", [])
    (dum, pid2) = fn.add_new_paper(conn, "test1", "p2", "d", "t", [])
    (dum, pid3) = fn.add_new_paper(conn, "test1", "p3", "d", "t", [])
    fn.like_paper(conn, "user", pid1)
    fn.like_paper(conn, "test2", pid2)
    fn.like_paper(conn, "test2", pid3)
    fn.like_paper(conn, "test3", pid3)
    (status, value) = fn.get_recommend_papers(conn, "user")
    if(status, value) != (0, []): return False
    #   2. Tested the case where people who liked the same paper has not like another
    #      paper that is not liked by the user
    fn.signup(conn, "test4", "test4")
    fn.like_paper(conn, "test4", pid1)
    (status, value) = fn.get_recommend_papers(conn, "user")
    if(status, value) != (0, []): return False
    #   3. Tested the correctness of the implementations, including content, the
    #      number of paper displayed and the order
    fn.like_paper(conn, "test2", pid1)
    fn.like_paper(conn, "test3", pid1)
    (status, value) = fn.get_recommend_papers(conn, "user")
    if(status != 0): return False
    if(len(value) != 2): return False
    pids = [x[0] for x in value]
    if(pids != [pid3, pid2]): return False
    #   4. Tested the case for non-exisiting user
    (status, value) = fn.get_recommend_papers(conn, "non-exisiting")
    if(status, value) != (1, None): return False
    print("PASS")
    return True

# Statistics related
def check_get_most_active_users(conn):
    print("Checking get_most_active_users ...")
    #create three users
    fn.signup(conn, "test200", "test200")
    fn.signup(conn, "test201", "test201")
    fn.signup(conn, "test202", "test202")
    #no user has posted any paper
    (status, value) = fn.get_most_active_users(conn, 3)
    if (status, value) != (0, []): return False
    #one user has posted paper
    fn.add_new_paper(conn, "test200", "paper200", "d", "t", ["tag"])
    (status, value) = fn.get_most_active_users(conn, 3)
    if (status, value) != (0, ["test200"]): return False
    #ensure: break tie by username
    fn.add_new_paper(conn, "test201", "paper201", "d", "t", ["tag"])
    (status, value) = fn.get_most_active_users(conn, 3)
    if (status, value) != (0, ["test200", "test201"]): return False
    #ensure: usernames ordered by paper numbers
    fn.add_new_paper(conn, "test201", "paper201_2", "d", "t", ["tag"])
    fn.add_new_paper(conn, "test202", "paper202", "d", "t", ["tag"])
    fn.add_new_paper(conn, "test202", "paper202_2", "d", "t", ["tag"])
    fn.add_new_paper(conn, "test202", "paper202_3", "d", "t", ["tag"])
    (status, value) = fn.get_most_active_users(conn, 5)
    if (status, value) != (0, ["test202", "test201", "test200"]): return False
    #ensure: return username length is limited by the argument
    (status, value) = fn.get_most_active_users(conn, 2)
    if (status, value) != (0, ["test202", "test201"]): return False

    #all tests passed
    print("PASS")
    return True

def check_get_most_popular_tags(conn):
    print("Checking get_most_popular_tags ...")
    fn.reset_db(conn)
    #create user
    fn.signup(conn, "test203", "test203")
    #no tag exist
    (status, value) = fn.get_most_popular_tags(conn, 2)
    if (status, value) != (0, []): return False
    #one paper exists
    fn.add_new_paper(conn, "test203", "paper203_1", "d", "t", ["tag_1"])
    (status, value) = fn.get_most_popular_tags(conn, 2)
    if (status, value) != (0, [("tag_1", 1)]): return False
    #break tie by tag name
    fn.add_new_paper(conn, "test203", "paper203_2", "d", "t", ["tag_2"])
    (status, value) = fn.get_most_popular_tags(conn, 3)
    if (status, value) != (0, [("tag_1",1), ("tag_2",1)]): return False
    #ensure: tag names ordered by appearances
    fn.add_new_paper(conn, "test203", "paper203_3", "d", "t", ["tag_2", "tag_3"])
    fn.add_new_paper(conn, "test203", "paper203_4", "d", "t", ["tag_2", "tag_3"])
    (status, value) = fn.get_most_popular_tags(conn, 5)
    if (status, value) != (0, [("tag_2",3), ("tag_3",2), ("tag_1",1)]): return False
    #ensure: return tag name limited by argument
    (status, value) = fn.get_most_popular_tags(conn, 2)
    if (status, value) != (0, [("tag_2",3), ("tag_3",2)]): return False
    #all tests passed
    print("PASS")
    return True

def check_get_number_papers_user(conn):
    print("Checking get_number_papers_user ...")
    #create user
    fn.signup(conn, "test204", "test204")
    #no paper posted by the user
    (status, value) = fn.get_number_papers_user(conn, "test204")
    if (status, value) != (0, 0):
        print("Fail: no paper posted by user")
        return False
    #user posted one paper
    fn.add_new_paper(conn, "test204", "paper204", "d", "t", ["tag"])
    (status, value) = fn.get_number_papers_user(conn, "test204")
    if (status, value) != (0, 1):
        print("Fail: user posted one paper")
        return False
    fn.add_new_paper(conn, "test204", "paper204_2", "d", "t", ["tag"])
    (status, value) = fn.get_number_papers_user(conn, "test204")
    if (status, value) != (0, 2):
        print("Fail: user posted multiple papers")
        print False

    #all test passed
    print("PASS")
    return True

def check_get_most_popular_tag_pairs(conn):
    print("Checking get_most_popular_tag_pairs ...")
    fn.reset_db(conn)
    fn.signup(conn, "test1", "test1")
    fn.signup(conn, "test2", "test2")
    fn.add_new_paper(conn, "test1", "p1", "d", "t", ["tag1"])
    fn.add_new_paper(conn, "test1", "p1", "d", "t", ["tag2"])
    fn.add_new_paper(conn, "test1", "p1", "d", "t", ["tag3"])
    #check the case where no tag pairs exists
    (status, value) = fn.get_most_popular_tag_pairs(conn)
    if(status, value) != (0, []): return False
    #check the normal cases
    fn.add_new_paper(conn, "test1", "p1", "d", "t", ["tag1", "tag2", "tag3"])
    fn.add_new_paper(conn, "test2", "p2", "d", "t", ["tag2", "tag3", "tag4"])
    fn.add_new_paper(conn, "test1", "p3", "d", "t", ["tag3", "tag4", "tag5"])
    (status, value) = fn.get_most_popular_tag_pairs(conn, 2)
    if(status != 0): return False
    if(len(value) !=2): return False
    if value != [("tag2", "tag3", 2), ("tag3", "tag4", 2)]: return False
    print("PASS")
    return True

def check_get_number_liked_user(conn):
    print("Checking get_number_liked_user ...")
    #check the case for non-exisiting user
    (status, value) = fn.get_number_liked_user(conn, "non-exisiting")
    if(status, value) != (1, None): return False
    #check the case where a user never liked a paper
    (status, value) = fn.get_number_liked_user(conn, "test1")
    if(status, value) != (0, 0): return False
    #chekc the normal case
    fn.like_paper(conn, "test2", 2)
    fn.like_paper(conn, "test2", 3)
    fn.like_paper(conn, "test2", 4)
    (status, value) = fn. get_number_liked_user(conn, "test2")
    if(status, value)!= (0,3): return False
    print("PASS")
    return True

def check_get_number_tags_user(conn):
    print("Checking get_numebr_tags_user ...")
    #check the case for non-exisiting user
    (status, value) = fn.get_number_tags_user(conn, "non-exisiting")
    if(status, value) != (1, None): return False
    #check for the case where the user post a paper but never attacha a tag
    fn.signup(conn, "test3", "test3")
    fn.add_new_paper(conn, "test", "p", "d", "t", [])
    (status,value) = fn.get_number_tags_user(conn, "test3")
    if(status, value) != (0,0): return False
    #check the nomal case
    (status, value) = fn.get_number_tags_user(conn, "test2")
    if(status, value) != (0,3):return False
    print("PASS")
    return True

def main():
    #assuming reset_db is correctly implemented
    conn = psy.connect("dbname=vagrant user=vagrant")

    if(
    # Basic APIs
    fn.reset_db(conn) and
    check_signup(conn) and
    check_login(conn) and

    # Event related
    fn.reset_db(conn) and
    check_add_new_paper(conn) and
    check_delete_paper(conn) and
    check_get_paper_tags(conn) and

    # Vote related
    fn.reset_db(conn) and
    check_like_paper(conn) and
    check_unlike_paper(conn) and
    check_get_likes(conn) and

    # Search related
    fn.reset_db(conn) and
    check_get_timeline(conn) and
    check_get_timeline_all(conn) and
    check_get_most_popular_papers(conn) and
    check_get_papers_by_tag(conn) and
    check_get_papers_by_keyword(conn) and
    check_get_papers_by_liked(conn) and
    check_get_recommend_papers(conn) and

    # Statistics related
    fn.reset_db(conn) and
    check_get_most_active_users(conn) and
    check_get_most_popular_tags(conn) and
    check_get_number_papers_user(conn) and
    check_get_most_popular_tag_pairs(conn) and
    check_get_number_liked_user(conn) and
    check_get_number_tags_user(conn)
    ):
        print("Passed all tests")
        fn.reset_db(conn)
# Helper functions
def get_pid(conn, uname, title):
    cur = conn.cursor()
    cur.execute("SELECT pid FROM papers WHERE username = %s AND title = %s", (uname, title))
    return cur.fetchone()[0]

if __name__ == "__main__":
    main()