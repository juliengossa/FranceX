
import requests
import json
import xmltodict
import math
import sys
import time

class Inpi:
    session = None

    def __init__(self, username, password):
        self.session = requests.Session()

        response = self.session.get("https://api-gateway.inpi.fr/services/uaa/api/authenticate")
        token = self.session.cookies['XSRF-TOKEN']

        headers = {
            'Accept': 'application/json, text/plain, */*',
            'X-XSRF-TOKEN': self.session.cookies['XSRF-TOKEN'],
            'Content-Type': 'application/json',
            'Connection': 'keep-alive'
        }

        response = self.session.post('https://api-gateway.inpi.fr/auth/login',
            json = {"username":username,"password":password,"rememberMe":True},
            headers=headers, verify=False)

        # self.session.cookies['access_token']
        # self.session.cookies['refresh_token']

        #resptest = session.get("https://api-gateway.inpi.fr/services/apidiffusion/api/marques/xml/FR4216963",headers=headers, verify=False)

    searchvar = [
        'ApplicationNumber','Mark',
        'MarkCurrentStatusCode', 'ApplicationDate', 'ExpiryDate',
        'DEPOSANT', 'DEPOTIT', 'MarkFeature',]
        #'ApplicantLegalEntity','IndividualIdentifier', 'OrganizationName']

    def get_searchvar(self):
        return self.searchvar+['url']

    def post_search(self, query, position, size):
        searchdata = {
          "query": query,
          "position": position,
          "size": size,
          "fields": self.searchvar,
          "collections": [ "FR" ],# #"EU", #"WO"],
          "facetsList": [ "APPLICANT", "CLASSIFICATION" ],
          "sortList": [ "APPLICATION_DATE DESC", "MARK ASC" ]
        }

        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-XSRF-TOKEN': self.session.cookies['XSRF-TOKEN']
        }
        respquery = self.session.post("https://api-gateway.inpi.fr/services/apidiffusion/api/marques/search",
            json=searchdata, headers=headers, cookies=self.session.cookies)

        r = respquery.json()
        try:
            return r['results']
        except:
            raise IOError(respquery.content)

    def search(self, query="[Mark=France]", position=0, size=10, limit=math.inf):
        marks = []
        while True:
            print("### Searching: "+str(position)+"/"+str(limit)+" "+str(size), file=sys.stderr)
            while True:
                try:
                    res = self.post_search(query,position,size)
                    time.sleep(0.5)
                    break
                except IOError as e:
                    print("Too many requests. Waiting 5 minute.", file=sys.stderr)
                    time.sleep(300)

            print("### Found: "+str(len(res)), file=sys.stderr)
            marks += res

            if len(res) == 0: break
            position+=len(res)
            if position > limit: break

        return marks

    def mark2array(self, mark):
        # shrink values to value
        for f in mark['fields']:
            if 'values' in f:
                f['value'] = ",".join(f['values'])

        fields = { f['name']:f['value'] for f in mark['fields'] }
        f = []
        for v in self.searchvar:
            f.append(fields[v] if v in fields else "NA")
        f.append(mark['xml']['href'])
        return f

    def get_notice(self, url):
        headers = {
            'X-XSRF-TOKEN': self.session.cookies['XSRF-TOKEN']
        }
        respnotice = self.session.get(url, #"https://api-gateway.inpi.fr/services/apidiffusion/api/marques/notice/"+id,
            headers=headers, cookies=self.session.cookies)
        try:
            r = xmltodict.parse(respnotice.content)
            return r['TradeMark']
        except:
            raise IOError(respnotice.status_code)

    notvar = ['RegistrationOfficeCode', 'ApplicationNumber', 'ApplicationDate',
        'FilingPlace', 'ApplicationLanguageCode', 'ExpiryDate',
        'MarkCurrentStatusCode', 'MarkFeature']

    def get_noticevar(self):
        return ['Mark','Operation'] + self.notvar + \
            ['ClassificationKindCode','ClassDescription'] + \
            ['ApplicantCount','ApplicantLegalEntity','IndividualIdentifier',
            'OrganizationName','AddressCity','AddressCountryCode']

    def notice2array(self, n):
        infos = []
        infos.append(n['WordMarkSpecification']['MarkVerbalElementText'])
        infos.append(n['@operationCode'])
        for v in self.notvar:
            infos.append(n[v] if v in n else "NA")
        # Classification
        try: infos.append(n['GoodsServicesDetails']['GoodsServices']['ClassificationKindCode'])
        except: infos.append("NA")
        cd = n['GoodsServicesDetails']['GoodsServices']['ClassDescriptionDetails']['ClassDescription']
        try: infos.append(cd['ClassNumber'])
        except: infos.append(",".join([c['ClassNumber'] for c in cd]))
        # Applicant
        applicantsCount = len(n['ApplicantDetails']['Applicant'])
        infos.append(applicantsCount)
        try: applicant = n['ApplicantDetails']['Applicant'][0]
        except: applicant = n['ApplicantDetails']['Applicant']
        try: infos.append(applicant['ApplicantLegalEntity'])
        except: infos.append("NA")
        address = applicant['ApplicantAddressBook']['FormattedNameAddress']
        try: infos.append(address['Name']['FormattedName']['IndividualIdentifier'])
        except: infos.append("NA")
        try: infos.append(address['Name']['FormattedName']['OrganizationName'])
        except: infos.append("NA")
        try: infos.append(address['Address']['FormattedAddress']['AddressCity'])
        except: infos.append("NA")
        try: infos.append(address['Address']['AddressCountryCode'])
        except: infos.append("NA")
        # return
        return infos

# n = getNotice("https://api-gateway.inpi.fr/services/apidiffusion/api/marques/notice/FR5052699")
# notice2infos(n)
#notice2infos(respnotice.content)





# headers = {
#     'Accept': 'application/json',
#     'Content-Type': 'application/json',
#     'X-XSRF-TOKEN': session.cookies['XSRF-TOKEN']
# }
#
# respquery = session.post("https://api-gateway.inpi.fr/services/apidiffusion/api/marques/search",
#     json=query, headers=headers, cookies=session.cookies)
#
# r = respquery.json()
#
# headers = {
#     'X-XSRF-TOKEN': session.cookies['XSRF-TOKEN']
# }
#
# mid = "FR5013228"
# respnotice = session.get("https://api-gateway.inpi.fr/services/apidiffusion/api/marques/notice/"+mid,
#     headers=headers, cookies=session.cookies)




#
# curl -k --tlsv1.2 -v -c cookie.txt https://api-gateway.inpi.fr/services/uaa/api/authenticate
# export TOKEN=`cat cookie.txt | grep XSRF-TOKEN | awk '{print $7}'`
# echo "TOKEN = " $TOKEN
# export ID1=`curl -k --tlsv1.2 -b cookie.txt -c cookie.txt -v 'https://api-gateway.inpi.fr/auth/login' -H'Accept: application/json, text/plain, */*' -H "X-XSRF-TOKEN: $TOKEN" -H 'Content-Type:application/json' -H 'Connection: keep-alive' -H "Cookie: XSRF-TOKEN= $TOKEN" -d '{"username":"julien.gossa@gmail.com","password":"v$2]*U>?Dt+DDWj","rememberMe":true}'`
# export access_token=`cat cookie.txt | grep access_token | awk '{print $7}'`;
# echo access_token = " $access_token
# export refresh_token=`cat cookie.txt | grep refresh_token | awk '{print $7}'`;
# echo refresh_token = " $refresh_token
#
# curl -X POST -k --tlsv1.2 -v 'https://api-gateway.inpi.fr/services/apidiffusion/api/marques/search' -H 'accept: application/xml' -H 'Content-Type: application/json' -H "X-XSRF-TOKEN: $TOKEN" -H "Cookie: XSRF-TOKEN=$TOKEN; access_token=$access_token;session_token=$refresh_token" -d '{ "collections": [ "FR", "WO" ], "query": "[(Mark OU DEPOSANT)=inpi]"}'
