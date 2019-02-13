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

name_to_short = {}

class CLASS:
    def __init__(self,d,c,s):
        d['dept']  = c[0].strip()
        d['num']   = c[1].strip()
        d['name']  = c[2].strip()
        d['short'] = s
        self.dept=d['dept']
        self.num=d['num']
        self.name=d['name']
        self.short=d['short']
        self.fields = ['dept','num','short','name','raw']
        for k in [x for x in d.keys() if x not in ['dept','num','name','short'] and len(d[x]) > 0]:
            #requisites, anti requisites, and the like are going to be here
            #intend to replace the text with the actual cross reference links
            setattr(self,k,d[k])
            self.fields.append(k)
        setattr(self,'raw',d)
#potential fields,
#        dept,num,name,short,prereq,antireq,coreq,hours,desc,notes,aka,repeat,nogpa
        #raw and various fields exist by the time I leave here        

    def get(self,s):
        return getattr(self,s,'')

    def __repr__(self):
        return json.dumps(self.raw)
    
    def __str__(self):
        s = '%s %s %s %s\n'%(self.short,self.dept,self.num,self.name)
        s = s + ('\treq:   %s\n'% self.prereq) if hasattr(self,'prereq') and self.prereq else ''
        s = s + ('\tareq:  %s\n'% self.antireq) if hasattr(self,'antireq') and self.antireq  else ''
        s = s + ('\tcreq:  %s\n'% self.coreq) if hasattr(self,'coreq') and self.coreq  else ''
        s = s + ('\tnotes: %s\n'% self.notes) if hasattr(self,'notes') and self.notes  else ''
        return s

#department is being used interchangeably with faculty here, may rename.
    
class DEPT:
    def __init__(self,short=None,name=None,IDS={}):
        self.short=short
        self.name=name
        self.IDS=IDS  #ID's should reference a CLASS object

    def __repr__(self):
        s = 'DEPT('+self.short+', '+self.name+', {'
        for k in self.IDS:
            s = s + k +': ' + self.IDS[k].__repr__()
        s = s +')'
        return s

        
        
#not in use yet
class FACULTY:
    def __init__(self,programs=None,departments=None,services=None,research=None):
        self.programs=programs
        self.departments=departments
        self.services=services
        self.research=research
    
def save_objs(path,obj):
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
            return table
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
    global name_to_short
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
                        name_to_short[title] = short
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

def load_or_scrape(root,path):
    global html_request
    raw = 'raw_html/'
    if os.path.exists(path):
        with open(path) as f:
            html_request = False
            return True, jsonpickle.decode(json.load(f))
    else:
        if os.path.exists(raw+path):
            #can get html locally
            with open(raw+path) as f:
                content = f.read()
                content = content.replace('\\xc3\\xa7','ç').replace('&amp;','&').replace('\\xc2\\xa0',' ').replace('\\xc3\\xa9','é')
                content = content.replace('\\xc3\\xbc','ü').replace('&#039;',"'").replace('\\xc3\\xa1','á')
                content = content.replace('\\xc3\\xad','í').replace('\\xc3\\xba','ú').replace('\\xc3\\xb6','ö')
                content = content.replace('\\xc2\\xa0',' ').replace('&#x0A','\n').replace('&nbsp;',' ').replace('\t',' ')
                return False, content

        html_request = True
        
        folder = os.path.dirname(raw+path)
        
        if not os.path.exists(folder):
            os.makedirs(folder)
        
        lines = requests.get(root+path,headers=headers).iter_lines()
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
        return faculties
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
    if type(faculties) == type({}) and len(faculties.keys()) > 0:#expand to a thorough test
        save_objs(faculties_path,faculties)
    else:
        if repeat == 3:
            return None
        repeat = repeat + 1
        os.remove(faculties_path)
        contacts_departments_load_fail = True
        faculties = parse_faclties()
    contacts_classes_load_fail = False
    print('finished',faculties_path)
    return faculties

#def parse_schedule_table(html):
    

    
def parse_schedules(short):
    #should load the object associated with 'tag'
    # except when that tag is a top level tag for other embedded classes, such as SENG under CPSC

    # if the short is a top level tag,ie, CPSC for SENG, it will:
    #   load only cpsc if cpsc exists
    #   parse cpsc, find cpsc, data, isec, and seng and will save each
    #
    # if the short is not top level, such as SENG under CPSC, it will:
    #   load only if seng already exists
    #   fail to load if seng does not exist, and will fail to find it under seng if it tries
    #
    # may need to rethink the loading process.
    # I will have all the infoin one go, but there will be some failures that are not actually falures along the way, guaranteed
    
#    if exist, open, else scrape

    #special cases - these allow finding 49 more fields which aren't directly referenced
    #52 remain unknowns
    specials = {
        'acct':'ha',
        'almc':'slllc',
        'astr':'phas',
        'bcem':'bio',
        'bmen':'biomedical',
        'iphe':'sw',
        'knes':'kn',
        'neur':'bscneuro',
        'scie':'natsci',
        'glgy':'geos'
        }
    if short in specials:
        short = specials[short]
    
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
    if len(departments) == 0:
        return None
    department = {}
    for dept in departments:
        dept = dept[1:] #trim the tag we broke
        try:
            dept_short = (re.search('[A-Z]{2,5}',re.search('>[A-Z]{2,5} [0-9]{3}( |\.|[A-Z].)',dept).group()).group())
        except:
            print(dept)
            input(428)
        department[dept_short] = slice_course_table(dept_short,dept)
        
    if len(department) > 0:
        save_objs(class_day_time_path % short,department)
    return department

def slice_course_table(short,html):
    global repeat
    global contacts_classes_load_fail
    indices = [i.span()[0]+1 for i in re.finditer('>[A-Z]{2,5} [0-9]{3}( |\.)',html)]
    indices.insert(0,0)
    classes = {}
    p = True
        
    for info in [html[indices[i]:indices[i+1]] for i in range(len(indices)-1)][1:]:
        info_old = info
        short,info = info.split(' ',1)[0],info.split(' ',1)[1]
        num,info = info.split(' ',1)[0],(info.split(' ',1)[1])[2:]
        name,info = info[:info.find('<')],info[info.find('<'):]
        info = info.replace('>SEM','>SEM_SEM').replace('>LEC ','>LEC_LEC ').replace('>TUT ','>TUT_TUT ').replace('>LAB ','>LAB_LAB ').replace('>Notes:','>NOTES_Notes:').replace('>Details<','>DETAILS_Details<')
        info = info.replace('>TBA','> TBA')
        
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
            p_num = re.match('[0-9]{1,2}',x[0][1])
            day = re.search('([A-Z]+)',x[0][1])
            if p_num is not None:
                p_num = int(p_num.group(0))
            if day is not None:
                day  = day.group(0)
            t = x[0][0]
            if t not in this:
                this[t] = {}
            this[t][p_num] = {}
            this[t][p_num]['day'] = day
            this[t][p_num]['time'] = x[0][2]
            this[t][p_num]['room'] = x[1]
            this[t][p_num]['prof'] = x[2]
        classes[num]={'num':num,'name':name,'short':short,'details':this}
    return classes

def scrape_department_and_class_reqs():
    departments = parse_depts(departments_path)
    full_class_info = {}
    finished_departments = False
    while not finished_departments:
        for d in departments.keys():
            class_table = getTableFile(departments[d]['link'],d)
            full_class_info[d] = DEPT(d,departments[d]['title'],class_table)
        finished_departments = not(departments_calendar_load_fail or departments_calendar_class_tables_load_fail)
    return full_class_info

def scrape_faculties_and_class_schedules(depts):
    faculties = parse_faculties()
    departments = {}
    for dept in depts.keys():
        schedules = parse_schedules(dept.lower())
        if schedules is not None:
            for short in schedules.keys():
                    
                departments[short] = schedules[short]
    return departments

def get_everything():
    print('getting class requisites')
    departments = scrape_department_and_class_reqs()
#    for d in departments:
#        for i in departments[d].IDS:
#            for field in departments[d].IDS[i].fields:
#                if field != 'raw':
#                    print(field)
#                    print('\t',getattr(departments[d].IDS[i],field))
#            input(520)
    print('getting class schedules')
    faculties = scrape_faculties_and_class_schedules(departments)
    print('data scrape/load completed')
    not_found = [x for x in departments.keys() if x not in faculties.keys()]
    found = {}
    for key in departments.keys():
        if key in faculties:
            found[key] = departments[key]
            found[key].IDS = faculties[key]
    dept_count = 0
    class_count = 0
    schedule_count = 0

    last_dept=None
    last_class=None

#    pretty_print_classes(found)
#    pretty_print_notes_field(found)


def pretty_print_notes_field(found):
    for key in sorted(found.keys()):
        for i in sorted(found[key].IDS.keys()):
            if len(found[key].IDS[i]['details'].keys()) > 0:
                for t in ['SEM','LEC','LAB','TUT']:
                    if t in found[key].IDS[i]['details']:
                        for n in sorted(found[key].IDS[i]['details'][t].keys()):
                            print(found[key].IDS[i])
                            input(546)


#outputs every class that yielded schedule data, and for each of those the schedules indented on following lines.
def pretty_print_classes(found):
    for key in sorted(found.keys()):
        for i in sorted(found[key].IDS.keys()):
            if len(found[key].IDS[i]['details'].keys()) > 0:
#                print(found[key].IDS[i]['short'],found[key].IDS[i]['num'],found[key].IDS[i]['name'])
                for t in ['SEM','LEC','LAB','TUT']:
                    if t in found[key].IDS[i]['details']:
                        for n in sorted(found[key].IDS[i]['details'][t].keys()):
#                            print('\t',t,n,found[key].IDS[i]['details'][t][n]['day'],found[key].IDS[i]['details'][t][n]['time'],found[key].IDS[i]['details'][t][n]['room'],found[key].IDS[i]['details'][t][n]['prof'])
                            schedule_count = schedule_count+1
                            if key != last_dept:
                                dept_count = dept_count+1
                                last_dept = key
                            if found[key].IDS[i] != last_class:
                                class_count = class_count +1
                                last_class = found[key].IDS[i]
#    print('contains information on',schedule_count,'separate schedule items')
    print(dept_count,'departments,',class_count,'classes,',schedule_count,'schedule items')
    

    
get_everything()

#################################
#                               #
#     Concentration Details     #
#                               #
#################################
#faculties, pick one to begin
#https://www.ucalgary.ca/pubs/calendar/current/index.html
#  selecting faculty of science, https://www.ucalgary.ca/pubs/calendar/current/sc.html
#  pick url for Program details, https://www.ucalgary.ca/pubs/calendar/current/sc-4.html
#    pick concentration url
#    picking Computer Science, https://www.ucalgary.ca/pubs/calendar/current/sc-4-3.html
#      page contains some info, so parse as baseline
#      select from programs in, Maj/Hon/Intern programs, Combined, and minor
#        selecting programs in, https://www.ucalgary.ca/pubs/calendar/current/sc-4-3-1.html
#          contains info on CPSC Major, Master, BSC in, plus specific concentrations
#          important field labels?
#    
#
#
#################################
#                               #
#    structural data layout     #
#                               #
#################################
#
#   intend to create a UofC structure which contains faculties under a semester(one for now)
#
#   using . notation for convenience/brevity/clarity, may use lists, dicts, or attributes as is convenient in the data
#
#     faculties may contain programs and courses.
#           subject to potentially significant change
#       faculty.semester.program...
#       faculty.semester.courses...
#
#   programs may contain requisite types(req n 400 levels), and courses links
#           subject to potentially significant change
#       program.entry.req_n                         # (field entry reqs, high school, etc)
#       program.entry.a_req                         # (field entry anti reqs, low gpa, F's, etc)
#                               disjoint branching point
#       program.grad                                # (top level program division, masters, honours, etc)
#       program.grad.reqs                           # (top level requisites common to all concentrations)
#       program.grad.a_reqs                         # (top level anti-requisites common to all concentrations)
#                               disjoint branching point
#       program.grad.conc                           # (top level program sub division, specific concentrations, or lack of)
#       program.grad.conc.attribute                 # (concentration specific information)
#       program.grad.conc.reqs.attributes           # (did time, took course, has credits, etc)
#       program.grad.conc.reqs.courses              # (courses needed, potentially further subdivided, 300's, 400's, 500's, etc) 
#       program.grad.conc.a_req.attribute           # (didn't do thing, fail, low gpa, etc)
#       program.grad.conc.a_req.courses             # (courses excluded, potentially further subdivided, 300's, 400's, 500's, etc)
#
#   departments currently contain:
#       dept.field                                  # (short for department it belongs to, such as CPSC, may not be sme as faculty)
#       dept.name                                   # (full name of department)
#       dept.IDS                                    # (class numbers, such as 471 for CPSC 471
#       dept.IDS.<CLASS>                            # (class object, see below)                         
#       dept.faculty                                # (not yet present, reference to parent faculty)
#
#
#   classes currently contain their requisite tree and schedule information for given semester
#       class.num                                   # (the classnumber, such as 471 for CPSC 471)
#       class.name                                  # (the class name, such as Database Management Systems I)
#       class.short                                 # (the short tag for the class, such as CPSC)
#       class.details                               # (details, will likely replace with a schedule object to be built soon
#       class.details.type                          # (LEC,LAB,TUT,SEM)
#       class.details.type.n                        # (number of type, 2 for tut2, 3 for lec3, etc)
#       class.details.type.n.day                    # (day of class, in string format with MTWRF for mon, tues, wed, thurs, fri respectively)
#       class.details.type.n.time                   # (time of each class, currently in string format as "XX:XX - XX:XX" 
#       class.details.type.n.room                   # (room the class is held in)
#       class.details.type.n.prof                   # (prof/TA teaching)
#       class.details.type.n.seats                  # (not yet contained, want/need this for knowing if schedule is open)
#       class.details.type.n.free                   # (not yet contained, want/need this for knowing if schedule is open)
#       class.details.type.n.associated             # (not yet contained, want/need this for knowing related classes, such as Lec N must take TUT M and Lab O)
#
#   might generate a schedule to replace the class details field with
#   schedule may contain relevant class info:
#       sched.type                                  # (LEC,LAB,TUT,SEM)
#       sched.type.n                                # (number of type, 2 for tut2, 3 for lec3, etc)
#       sched.type.n.day                            # (day of class, in string format with MTWRF for mon, tues, wed, thurs, fri respectively)
#       sched.type.n.time                           # (time of each class, currently in string format as "XX:XX - XX:XX" 
#       sched.type.n.room                           # (room the class is held in)
#       sched.type.n.prof                           # (prof/TA teaching)
#       sched.type.n.seats                          # (want/need this for knowing if schedule is open)
#       sched.type.n.free                           # (want/need this for knowing if schedule is open)
#       sched.type.n.associated                     # (obj cross references, want/need this for knowing related classes, such as Lec N must take TUT M and Lab O)
#       















1
