# !/usr/bin/env python
# -*- coding:utf-8 -*-
__author__ = 'bit4'
__github__ = 'https://github.com/bit4woo'
import multiprocessing
import threading
import urlparse
import urllib
import requests
import re
import hashlib

class Netcraft(multiprocessing.Process):
    def __init__(self, domain, proxy=None):
        self.base_url = 'http://searchdns.netcraft.com/?restriction=site+ends+with&host={domain}'
        #self.domain = urlparse.urlparse(domain).netloc
        self.domain = domain
        self.subdomains = []
        self.session = requests.Session()
        self.engine_name = "Netcraft"
        multiprocessing.Process.__init__(self)
        self.q = []
        self.timeout = 10
        self.print_banner()
        return

    def run(self):
        domain_list = self.enumerate()
        for domain in domain_list:
            self.q.append(domain)
        print "[-] {0} found {1} domains".format(self.engine_name, len(self.q))
        return self.q

    def print_banner(self):
        print "[-] Searching now in %s.." %(self.engine_name)
        return

    def req(self, url, cookies=None):
        cookies = cookies or {}
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:38.0) Gecko/20100101 Firefox/40.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-GB,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        }
        try:
            resp = self.session.get(url, headers=headers, timeout=self.timeout,cookies=cookies)
        except Exception as e:
            print e
            resp = None
        return resp

    def get_response(self,response):
        if response is None:
            return None
        if hasattr(response, "text"):
            return response.text
        else:
            return response.content

    def get_next(self, resp):
        link_regx = re.compile('<A href="(.*?)"><b>Next page</b></a>')
        link = link_regx.findall(resp)
        link = re.sub('host=.*?%s'%self.domain, 'host=%s'%self.domain, link[0])
        url = 'http://searchdns.netcraft.com'+link
        return url

    def create_cookies(self, cookie):
        cookies = dict()
        cookies_list = cookie[0:cookie.find(';')].split("=")
        cookies[cookies_list[0]] = cookies_list[1]
        cookies['netcraft_js_verification_response'] = hashlib.sha1(urllib.unquote(cookies_list[1])).hexdigest()
        return cookies

    def get_cookies(self,headers):
        if 'set-cookie' in headers:
            cookies = self.create_cookies(headers['set-cookie'])
        else:
            cookies = {}
        return cookies

    def enumerate(self):
        start_url = self.base_url.format(domain='example.com')
        resp = self.req(start_url)
        cookies = self.get_cookies(resp.headers)
        url = self.base_url.format(domain=self.domain)
        while True:
            resp = self.get_response(self.req(url,cookies))
            self.extract_domains(resp)
            if not 'Next page' in resp:
                return self.subdomains
                break
            url = self.get_next(resp)

    def extract_domains(self, resp):
        link_regx = re.compile('<a href="http://toolbar.netcraft.com/site_report\?url=(.*)">')
        try:
            links_list = link_regx.findall(resp)
            for link in links_list:
                subdomain = urlparse.urlparse(link).netloc
                if not subdomain.endswith(self.domain):
                    continue
                if subdomain and subdomain not in self.subdomains and subdomain != self.domain:
                    #if verbose:
                        #print "%s%s: %s%s"%(R, self.engine_name, W, subdomain)
                    self.subdomains.append(subdomain.strip())
            return links_list
        except Exception as e:
            print e
            pass


if __name__ == "__main__":
    x = Netcraft("meizu.com","https://127.0.0.1:9999")
    print x.run()