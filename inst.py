import requests
import argparse
import time
import os

def creds():
    print("OsInstagram")
    print("---------------------\n")
    print("Author: Kirk")
    print("HTB Profile: https://www.hackthebox.eu/home/users/profile/188681")
    print("GitHub: https://github.com/haqgg\n\n")


def parser():
    parser = argparse.ArgumentParser(description="[+] Usage: ./inst.py -n nickname \n | NOTE: If you dont want to save photos or parse pages, set: -sp 0 -pp 0")
    parser.add_argument("-n", dest="nickname")
    parser.add_argument("-sp", dest="sp", type=int, default=1)
    parser.add_argument("-pp", dest="pp", type=int, default=1)

    options = parser.parse_args()

    return options


def main(nickname, sp, pp):
    todos = requests.get("https://www.instagram.com/" + nickname + "?__a=1").json()
    if todos == {}:
        print("[-] Page Not Found")
        exit()

    if pp:
        try:
            os.mkdir(nickname)
            if todos["graphql"]["user"]["edge_owner_to_timeline_media"]["count"]:
                os.mkdir(nickname + "/posts/")
        except FileExistsError:
            print("[-] Folder already exists. Delete or rename it")
            exit()

    parse_page(todos, pp)

    if pp:
        print("\n[+] Got ", todos["graphql"]["user"]["edge_owner_to_timeline_media"]["count"], "post(s).")
        if not todos["graphql"]["user"]["is_private"]:
            print("[+] Downloading...")
            get_req_photos12(todos["graphql"]["user"], sp)
        else:
            print("[-] Account is private")
    print("[+] Done")


def get_shortcodes(whatget, howmuchget, sp):
    for i in range(howmuchget):
        req = requests.get("https://instagram.com/p/" + whatget["edges"][i]["node"]["shortcode"] + "/?__a=1").json()
        parse_media(req["graphql"]["shortcode_media"], whatget["edges"][i]["node"]["shortcode"], sp)


def get_req_morephotos(todos, idprofile, sp):
    if todos["edge_owner_to_timeline_media"]["page_info"]["has_next_page"]:
        data_for_get_req = 'https://www.instagram.com/graphql/query/?query_hash=f2405b236d85e8296cf30347c9f08c2a' \
                           '&variables=%7B%22id%22%3A%22' + idprofile + '%22%2C%22first%22%3A50%2C%22after%22%3A%22' \
                           + todos["edge_owner_to_timeline_media"]["page_info"]["end_cursor"].split("==")[0] + \
                           '%3D%3D%22%7D '

        json_media = requests.get(data_for_get_req).json()
        get_shortcodes(json_media["data"]["user"]["edge_owner_to_timeline_media"], len(str(json_media["data"]["user"]).split("'shortcode': '")) - 1, sp)
        get_req_morephotos(json_media["data"]["user"], idprofile, sp)


# getting links of the posts
def get_req_photos12(todos, sp):
    if todos["edge_owner_to_timeline_media"]["count"] <= 12:
        get_shortcodes(todos["edge_owner_to_timeline_media"], todos["edge_owner_to_timeline_media"]["count"], sp)
    else:
        get_shortcodes(todos["edge_owner_to_timeline_media"], 12, sp)
        get_req_morephotos(todos, todos["id"], sp)


# getting infos about account
def parse_page(todos, sp):
    print("[+] Getting info about profile")
    follow_inst = str(todos["graphql"]["user"]["edge_follow"]["count"])
    followed_by_inst = str(todos["graphql"]["user"]["edge_followed_by"]["count"])
    content_inst = str(todos["graphql"]["user"]["edge_owner_to_timeline_media"]["count"])
    biography = todos["graphql"]["user"]["biography"]
    name = todos["graphql"]["user"]["full_name"]
    username = todos["graphql"]["user"]["username"]
    verified = str(todos["graphql"]["user"]["is_verified"])
    fb = str(todos["graphql"]["user"]["connected_fb_page"])
    business = str(todos["graphql"]["user"]["is_business_account"])

    try:
        link = "\nLink: " + todos["graphql"]["user"]["external_link"]
    except:
        link = ''

    info = "Name: " + name + "\nUsername: " + username + "\nBiography: " + biography + "\nVerified: " + verified + "\nFollow: " + follow_inst + "\nFollowed: " + \
           followed_by_inst + "\nNumber of posts: " + content_inst + link + "\nBusiness account: " + business + \
           '\nConnected to facebook: ' + fb
    if sp:
        file = open(username + "/info.txt", "w", encoding="utf-8")
        file.write(info)
        file.close()
    print(info)


# functions for comments
def get_req_com(shortcode, comments, page_info, list_of_comments, m, nickname):
    list_of_comments += str(comments)
    if page_info["has_next_page"]:
        end_cursor = page_info["end_cursor"]
        data_for_get_req = 'https://www.instagram.com/graphql/query/?query_hash=f0986789a5c5d17c2400faebf16efd0d' \
                           '&variables=%7B%22shortcode%22%3A%22' + shortcode + '%22%2C%22first%22%3A50' \
                                                                               '%2C%22after%22%3A%22' + \
                           end_cursor.split("==")[0] + '%3D%3D%22%7D'
        json_media = requests.get(data_for_get_req).json()
        try:
            comments = json_media["data"]["shortcode_media"]["edge_media_to_comment"]["edges"]
            page_info = json_media["data"]["shortcode_media"]["edge_media_to_comment"]["page_info"]
            get_req_com(shortcode, comments, page_info, list_of_comments, m, nickname)
        except Exception as e:
            if json_media['message'] == "rate limited":
                print("[-] Rate limit. Please wait... (8 min.)")
                time.sleep(480)
                get_req_com(shortcode, comments, page_info, list_of_comments, m, nickname)
            else:
                print("[-] Error:", "\n", e, json_media)
                pass
    else:
        comments = parse_comm(list_of_comments)
        with open(nickname + "/posts/" + str(m) + "/comments.txt", "w", encoding="utf-8") as file:
            file.write(comments)

        with open(nickname + "/all_comments.txt", "a", encoding="utf-8") as file_all_comments:
            file_all_comments.write(comments)


def parse_comm(list_of_comments):
    list_comments = ''
    num = str(list_of_comments).split("'node':")

    for i in range(1, len(num)):
        if str(num[i]).split("'edge_liked_by': {'count': ")[1].split("}")[0] == '0':
            likes = ''
        else:
            likes = "\t" + str(num[i]).split("'edge_liked_by': {'count': ")[1].split("}")[0] + " like(s)"
        username = str(num[i]).split("'username': '")[1].split("'},")[0]

        try:
            text = str(num[i]).split("'text': '")[1].split("'")[0]
        except:
            text = str(num[i]).split(''''text': "''')[1].split('"')[0]

        list_comments += username + ":  '" + text + "'" + likes + "\n"

    return list_comments


def comm(json_page, m):
    global comments, page_info
    try:
        comments = json_page["edge_media_to_parent_comment"]["edges"]
        page_info = json_page["edge_media_to_parent_comment"]["page_info"]
    except KeyError:
        comments = json_page["edge_media_to_comment"]["edges"]
        page_info = json_page["edge_media_to_comment"]["page_info"]
    except Exception != KeyError as e:
        print("\n\n", json_page, "\n[-] Error:", e)
        exit()
    get_req_com(json_page["shortcode"], comments, page_info, '', m, json_page["owner"]["username"])


# saving infos and photoes from account
def parse_media(json_page, m, sp):
    global text, checker_for_comment
    view_count = ''
    os.mkdir(json_page["owner"]["username"] + "/posts/" + str(m))
    captions = 'Caption(s) and Data: '
    print("[+] Downloading post " + str(m))
    if json_page["__typename"] == "GraphVideo":
        view_count = str("View count = " + str(json_page["video_view_count"]))
        out = open(json_page["owner"]["username"] + "/posts/" + str(m) + "/video.txt", "w")
        out.write(str("https://instagram.com/p/" + json_page["shortcode"]))
        out.close()

    if json_page["__typename"] == "GraphImage":
        photo = str(json_page["display_resources"][-1]["src"])
        p = requests.get(photo)
        if sp:
            with open(json_page["owner"]["username"] + "/posts/" + str(m) + "/img" + str(m) + ".jpg", "wb") as out:
                out.write(p.content)
        captions = "\n" + json_page["accessibility_caption"]

    if json_page["__typename"] == "GraphSidecar":
        for i in range(len(json_page["edge_sidecar_to_children"]["edges"])):
            photoes = json_page["edge_sidecar_to_children"]["edges"][i]["node"]["display_resources"][-1]["src"]
            p = requests.get(photoes)
            if sp:
                with open(json_page["owner"]["username"] + "/posts/" + str(m) + "/img" + str(i) + ".jpg", "wb") as out:
                    out.write(p.content)
            try:
                captions += "Photo №" + str(i) + "-" + str(json_page["edge_sidecar_to_children"]["edges"][i]
                                                             ["node"]["accessibility_caption"]) + "\n"
            except:
                view_count = str("View count = " + str(json_page["edge_sidecar_to_children"]["edges"][i]
                                                         ["node"]["video_view_count"]))
                with open(json_page["owner"]["username"] + "/posts/" + str(m) + "/video.txt", "w") as out:
                    out.write(str("https://instagram.com/p/" + json_page["shortcode"]))

    likes = "Likes: " + str(json_page["edge_media_preview_like"]["count"]) + "\n"
    link = "Link - " + "instagram.com/p/" + json_page["shortcode"] + "\n"
    location = json_page["location"]

    if location:
        with open(json_page["owner"]["username"] + "/all_locations.txt", "a", encoding="utf-8") as file:
            file.write("post " + str(m) + "\n" + str(location) + "\n")
    else:
        location = ''

    if not json_page["edge_media_to_tagged_user"]["edges"]:
        tagged_user = ''
    else:
        print()
        tagged_user = '\nTagged user(s): '
        for i in range(len(str(json_page["edge_media_to_tagged_user"]).split("node"))-1):
            tagged_user += "@" + json_page["edge_media_to_tagged_user"]["edges"][i]["node"]["user"]["username"] + \
                           " (" +json_page["edge_media_to_tagged_user"]["edges"][i]["node"]["user"]["full_name"] + ")\n"
        with open(json_page["owner"]["username"] + "/all_tagged.txt", "a", encoding="utf-8") as file:
            file.write(str("post " + str(m) + ":" + tagged_user + "\n"))

    file = open(json_page["owner"]["username"] + "/posts/" + str(m) + "/info.txt", "w", encoding="utf-8")

    try:
        text = "text: '" + str(json_page["edge_media_to_caption"]["edges"][0]["node"]["text"]) + "'\n"
    except:
        text = "text: None\n"

    all_information = str(
        text + likes + tagged_user + "\nLocation: " + str(location) + captions + view_count + "\n" + link)
    file.write(all_information)
    file.close()

    try:
        checker_for_comment = json_page["edge_media_to_parent_comment"]["count"]
    except:
        checker_for_comment = json_page["edge_media_to_comment"]["count"]

    if checker_for_comment != 0:
        comm(json_page, m)


try:
    options = parser()
    pp = options.pp
    sp = options.sp
    nickname = options.nickname
    creds()
    main(nickname, sp, pp)

except KeyboardInterrupt:
    print("\n\n[-] Detected Ctrl + C ... Program Existed")
    exit()

except Exception as e:
    with open("log.txt", "w") as fileerror:
        fileerror.write(str(e))
    print("\n\n[-] Some problem, check nickname/log.txt")
    exit()
