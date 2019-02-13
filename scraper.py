#ict320, friday, 2pm

import sys, requests, os, json, re, operator, time, random
from itertools import tee,zip_longest

try:
    import jsonpickle
except:
    print('this scraper relies on jsonpickle for json handling of user classes.')
    print('you can get it at "https://jsonpickle.github.io/#download-install"')
    print('Aborting')
    sys.exit(1)


indent=0

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
}

#generate default delays if necessary
if not os.path.isfile('delays'):
    delays = {'url':(1,5),'reject':(150,300)}
    with open('delays','w') as f:
        json.dump(delays,f)

#load current delays
with open('delays') as f:
    delays = json.load(f)

#constants  —
#html prefix for ucalgary pages
ucalgary_root = 'https://www.ucalgary.ca/'
#html prefix for ucalgary pages
contacts_root = 'http://contacts.ucalgary.ca/'

# department titles
departments_path = 'pubs/calendar/current/course-desc-main.html'
#department classes
calendar_path_root='pubs/calendar/current/'

#parse this to build the faculty listing.
    #need the faculty listing to automate collecting course info.
    #also need faculty for determining breadth, so, very useful info either way.
faculties_path = 'directory/faculties'

#class timetables
    #figure out which faculty
    # sub faculty short into following path at %s, lowercase, such as cpsc, or arts
    # append class short and num as e.g. CPSC203
class_day_time_path = 'info/%s/courses/w19'


#globals
html_request = False
departments_calendar_load_fail = False
departments_calendar_class_tables_load_fail = False
contacts_departments_load_fail = False
contacts_classes_load_fail = False
repeat = 0


class CLASS:
    def __init__(self,d,c,s):
        d['dept']  = c[0].strip()
        d['num']   = c[1].strip()
        d['name']  = c[2].strip()
        d['short'] = s            
        for k in d.keys():
            #requisites, anti requisites, and the like are going to be here
            #intend to replace the text with the actual cross reference links
            setattr(self,k,d[k])
        setattr(self,'raw',d)
    
    def __repr__(self):
        s = '%s %s %s %s\n'%(self.short,self.dept,self.num,self.name)
        s = s + ('\treq: %s'% self.prereq if self.prereq else '')
        return s

#department is being used interchangeably with faculty here, may rename.
    
class DEPT:
    def __init__(self,short=None,name=None,IDS={}):
        self.name_short=short
        self.name=name
        self.IDS={}  #ID's should reference a CLASS object
        
        
#not in use yet
class FACULTY:
    def __init__(self,programs=None,departments=None,services=None,research=None):
        self.programs=programs
        self.departments=departments
        self.services=services
        self.research=research
    
def save_objs(path,obj):
    print('saving obj for',path)
    folder = os.path.dirname(path)
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    with open(path,'w') as f:
        json.dump(jsonpickle.encode(obj),f)
    
def strip_tags(s):
    n = s.find('<')
    if n == -1:
        return s
    result = ''
    html=False
    for c in s:
        if c is '<':
            html=True
        if not html:
            result = result+c
        if c == '>':
            html=False
    return result

def getTables(tables,short):
    pattern  = re.compile(r"<span|</span>")
    classes = {}
    for table in tables:  #for each class on page
        table = [line.replace('<br>','') for line in pattern.split(table) if 'class' in line and 'course-' in line and not 'label' in line]
        if table:
            class_info = {}
            code = []
            for line in table:
                line = line.split('course-')[1].split('">',1)
                line = line[0],strip_tags(line[1])
                if line[0] == 'code':
                    code.append(line[1])
                else:
                    class_info[line[0]] = line[1]
            classes[code[1]] = CLASS(class_info,code,short)            
    return classes
        

#gets calendar class tables, loads file if exists, tests loaded obj, removes erroneous file and resets on failure
def getTableFile(path,short):
    global departments_calendar_class_tables_load_fail
    global repeat
    loaded = False
    try:
        loaded,table = load_or_scrape(ucalgary_root,calendar_path_root+path)
    except Exception as e:
        print(e)
        html=None
        table=None
    if loaded:
        departments_calendar_class_tables_load_fail = False
        return table
    else:
        html = table
        if html is not None:
            table = getTables(html.split('<table cellpadding')[1:],short)
            save_objs(calendar_path_root+path,table)
        else:
            if type(table) == type({}):
                print(table,'from',ucalgary_root+calendar_path_root+path)
            else:
                print(type(table),table)
            if repeat == 3:
                return None
            repeat = repeat + 1
            try:
                os.remove(calendar_path_root+path)
            except:
                pass
            departments_calendar_class_tables_load_fail = True
            table = getTableFile(path, short)
        
#gets calendar department links, loads file if exists, tests loaded obj, removes erroneous file and resets on failure
def parse_depts(departments_path):
    global departments_calendar_load_fail
    loaded,faculties = load_or_scrape(ucalgary_root,departments_path)
    if loaded:
        departments_calendar_load_fail = False
        return faculties
    else:
        departments={}
        lines = faculties.split('\n')
        for line in lines:
            line=str(line)
            line = line.replace('\t','').strip().split('<br/>')
            for subline in line:
                if 'link-text' in subline:
                    s = subline.split('link-text')
                    link=(s[0]).split('"')[-3]
                    title_short = (((s[1]).replace('>','<').split('<'))[1]).strip().split(' ')
                    if len(title_short[-1]) <= 4 and title_short[-1] == title_short[-1].upper():
                        title,short = ' '.join([s for s in title_short[:-1]]),title_short[-1]
                    else:
                        title,short = ' '.join([s for s in title_short]),''
                    if short and title and len(short) > 1:
                        departments[short]={'title':title,'link':link,'class':{}}
        if type(departments) == type({}) and 'ARKY' in departments.keys():
            save_objs(departments_path, departments)
        else:
            if repeat == 3:
                return None
            repeat = repeat + 1
            departments_calendar_load_fail = True
            os.remove(departments_path)
            departments = parse_depts(departments_path)
    departments_calendar_load_fail = False
    print('\tinit department links complete')
    return departments

def delay(s):
    n,n2 = delays[s]
    n = random.randint(n,n2)
    while n > 0:
        m = min(n,5)
        print('delaying,',m,'seconds',n,' seconds remain')
        time.sleep(m)
        n = n - m

def increase_delays():
    url = (1,5)
    reject = (150,300)
    
    delays['url'][0] = delays['url'][0] + url[0]
    delays['url'][1] = delays['url'][1] + url[1]
    delays['reject'][0] = delays['reject'][0] + reject[0]
    delays['reject'][1] = delays['reject'][1] + reject[1]
    with open('delays','w') as f:
        json.dump(delays,f)

def load_or_scrape(root,path):
    global html_request
    raw = 'raw_html/'
    if os.path.exists(path):
        with open(path) as f:
            html_request = False
            print('using local obj file')
            input()
            return True, jsonpickle.decode(json.load(f))
    else:
        if os.path.exists(raw+path):
            #can get html locally
            with open(raw+path) as f:
                print('using local html',raw+path)
                input()
                print('returning now')
                return False, f.read()
        html_request = True
        
        folder = os.path.dirname(raw+path)
        
        if not os.path.exists(folder):
            os.makedirs(folder)
        
        lines = requests.get(root+path,headers=headers).iter_lines()
        print('usng remote html')
        input()
        with open(raw+path,'w') as f:
            for line in lines:
                f.write(str(line))
        return load_or_scrape(root,path)


#will have faculties,with sub-departments, classes schedules, locations, and professors by end of this function
def parse_faculties():
    global repeat
    global contacts_departments_load_fail
    #if exist, open, else scrape
    loaded,faculties = load_or_scrape(contacts_root,faculties_path)
    if loaded:
        print('returning faculties obj')
        return faculties
    print('building new faculties obj')
#    else we scraped, we have parsing to do.
    html = ''.join([str(s) for s in faculties])

#    html = open('faculties.txt').read()

    faculties = {}
    if '404 - Page Not Found' in html:
        print('404 - Page Not Found')
        return
    
    #kill false positives
    html = html.replace('Faculties |','').replace('Faculties</div>','</div>').replace('Professional Faculties','Professional_Faculties')
    html = html.replace('&nbsp;','').replace('&amp;','&').replace('&#039;',"'")  #replace tags nbsp, ampersand, appostrophe, with chars

    html = html.split('Faculties',1)[1]  #toss everything before programs table begins
    top_categories,remainder = html.replace('>Faculties<','>  Faculties  <').split('  Faculties  ',1)
    top_categories = [strip_tags(line).replace('\t',' ') for line in top_categories.split('\n') if 'website' in line]
    facs = remainder.replace('<tr','~~<tr').split('~~')[1::2]
    programs = remainder.replace('<tr','~~<tr').split('~~')[::2]
    for fac,program in zip(facs,programs):
        fac = strip_tags(fac)
        s = fac.find('http')
        faculty = fac[:s]
        web = fac[s:]
        faculties[faculty] = {}
        faculties[faculty]['web'] = web

        #separate the departments divisions
        divisors = {
            'p1' : 'Programs: ',
            'p2' : 'Projects: ',
            'd'  : 'Departments: ',
            's'  : 'Services: ',
            'r'  : 'Research Units: ',
            'o'  : 'Organizations: ',
            'a'  : 'Also Known As: ',
            'c1' : 'Centers: ',
            'c2' : 'Centres: ',
            }

        points = {}
        program=strip_tags(program)
        for div in divisors.values():
            if program.find(div) > -1:
                points[program.find(div)] = div
        points = [[k,points[k]] for k in sorted(points.keys())]

        for i in range(len(points)):
            if i+1 < len(points):
                points[i] = points[i],points[i].insert(1,points[i+1][0])
            else:
                points[i] = points[i],points[i].insert(1,len(program))

        divided = {}
        for point in points:
            s,e,t = point[0]
            s = s+len(t)
            divided[t] = (program[s:e]).replace(', ',',').split(',')

        faculties[faculty] = divided
        #Arts Exists
    if type(faculties) == type({}) and 'arts' in faculties:#expand to a thorough test
        save_objs(faculties_path,faculties)
    else:
        if repeat == 3:
            return None
        repeat = repeat + 1
        os.remove(faculties+path)
        contacts_departments_load_fail = True
        faculties = parse_faclties()
    contacts_classes_load_fail = False
    print('finished',faculties_path)
    return faculties

#def parse_schedule_table(html):
    

    
def parse_schedules(short):
    
#    if exist, open, else scrape
    try:
        os.remove(class_day_time_path % short)
    except:
        pass
    loaded,classes = load_or_scrape(contacts_root,class_day_time_path % short)
    if loaded:
        return classes
#    else we scraped, we have parsing to do.

    html = ''.join(classes[2:].replace("'b'",'\n'))

    if '404 - Page Not Found' in html:
        print('404 - Page Not Found')
        return
    html = ''.join(html)
    departments = html.split('unitis-courses-heading')[1:]
    department = {}
    for dept in departments:
        dept = dept[1:] #trim the tag we broke
        dept_short = re.search('[A-Z]{3,4}',re.search('[A-Z]{3,4} [0-9]{3}',dept).group()).group()
        department[dept_short] = slice_course_table(dept_short,dept)
    return department

def slice_course_table(short,html):
    global repeat
    global contacts_classes_load_fail
    indices = [i.span()[0] for i in re.finditer('[A-Z]{3,4} [0-9]{3}',html)]
    indices.insert(0,0)
    classes = {}
    for info in [html[indices[i]:indices[i+1]] for i in range(len(indices)-1)][1:]:
        short,info = info.split(' ',1)[0],info.split(' ',1)[1]
        num,info = info.split(' ',1)[0],(info.split(' ',1)[1])[2:]
        name,info = info[:info.find('<')],info[info.find('<'):]
        info = info.replace('>SEM','>SEM_SEM').replace('>LEC ','>LEC_LEC ').replace('>TUT ','>TUT_TUT ').replace('>LAB ','>LAB_LAB ').replace('>Notes:','>NOTES_Notes:').replace('>Details<','>DETAILS_Details<')
        info = info.replace('\t',' ').replace('\\xc2\\xa0',' ').replace('&nbsp;',' ').replace('>TBA','> TBA').replace('&#x0A','')
        details = re.split('SEM_|LEC_|TUT_|LAB_|NOTES_|DETAILS_|<br />',info)
        CLS=[]
        RMS=[]
        PRF=[]
        NTS=[]
        DET=[]
        this = {}
        for d in details:
            s = strip_tags(d)
            match=re.search('[0-9]{2}:[0-9]{2} - [0-9]{2}:[0-9]{2}',s)
            if match or 'TBA' in s:
                s = s.split(' ',2)
                if 'SEM' in s or 'LEC' in s or 'TUT' in s or 'LAB' in s:
                    CLS.append(s)
            elif 'map/interactive' in d:
                RMS.append(s)
            elif 'Notes' in s:
                NTS.append(s.split(' ',1)[1])
            elif 'Details' in s:
                DET.append(s.split(' ',1)[1])
            elif '/profiles/' in d:
                PRF.append(s)
            
        c = zip(CLS,RMS,PRF)
        for x in c:
            this['type'] = x[0][0]
            p_num = re.match('[0-9]{1,2}',x[0][1])
            day = re.search('([A-Z]+)',x[0][1])
            if p_num is not None:
                this['p_num'] = p_num.group(0)
            if day is not None:
                this['day']  = day.group(0)
            this['time'] = x[0][2]
            this['room'] = x[1]
            this['prof'] = x[2]
        classes[num]={'num':num,'name':name,'short':short,'details':this}
    if type(classes) == type({}) and len(classes.keys()) > 0:
        print('saving object for',class_day_time_path % short)
        save_objs(class_day_time_path % short,classes)
        contacts_classes_load_fail = False
    else:
        print('not saving object for',class_day_time_path % short)
        try:
            print('\t',type(classes),len(classes.keys()),classes.keys())
        except:
            print('\t',type(classes))
        if repeat == 3:
            return None
        repeat = repeat + 1
        if os.path.exists(class_day_time_path % short):
            os.remove(class_day_time_path % short)
        contacts_classes_load_fail = True
        classes = parse_schedules(short)
    return classes

        

def scrape_department_and_class_reqs():
    departments = parse_depts(departments_path)
    full_class_info = {}
    finished_departments = False
    delayed=False
    while not finished_departments:
        for d in departments.keys():
            repeat = 0   #reset the repeat trigger
            full_class_info[d] = DEPT(d,departments[d]['title'],getTableFile(departments[d]['link'],d))
            if repeat == 3:  #probably got myself banned, parsing errors are likely to crash out the script
                if delayed:
                    increase_delays()
                    delayed=False
                delay('reject')  #sleep 5 minutes to try and get unbanned
                delayed=True
                break       #exit current loop, to startthe process over on iterate while
            #if either fails, not_finished is still true, we need to cycle around again.
            if html_request:
                delay(random.randint(1,5))
        finished_departments = not(departments_calendar_load_fail or departments_calendar_class_tables_load_fail)
    return full_class_info

def scrape_faculties_and_class_schedules(depts):
    faculties = parse_faculties()
    for short in faculties.keys():
        schedules = parse_schedules(short.lower())

def get_everything():
    print('getting class requisites')
    departments = scrape_department_and_class_reqs()
    print('getting class schedules')
    scrape_faculties_and_class_schedules(departments)
    print('data scrape/load completed')
    for dept in departments.keys():
#        print(dept)
        print('\t',departments[dept].keys())

#get_everything()

print(parse_schedules('cpsc').keys())
