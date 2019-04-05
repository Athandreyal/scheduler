#ict320, friday, 2pm

# AMAT and PMAT deprecated, adding them manually to the full and short name dicts



import sys, requests, os, json, re, operator, time, random, sqlite3
import bool_parser as parse
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

#objs_path for intermediate objects to reduce processing time while iteratively building up
objs_path = 'tmp/objs'

#globals
html_request = False
departments_calendar_load_fail = False
departments_calendar_class_tables_load_fail = False
contacts_departments_load_fail = False
contacts_classes_load_fail = False

name_to_short = {}
short_to_name = {}
department_names = {}

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
#        dept,num,name,short,prereq,antireq,coreq,,desc,notes,aka,repeat,nogpa
        #raw and various fields exist by the time I leave here        

    def get(self,s):
        return getattr(self,s,'')

    def add_field(self,name,data):
        setattr(self,name,data)
        self.fields.append(name)

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

class SCHED:
    def __init__(self,parent,_type,num,day,time,room,prof,associated=None,seats=None,free=None):
        self.parent     = parent
        self.type       = _type
        self.num        = num
        self.day        = day
        self.time       = time
        self.room       = room
        self.prof       = prof
        self.associated = associated
        self.seats      = seats
        self.free       = free

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
            departments_calendar_class_tables_load_fail = True
            table = getTableFile(path, short)

#gets calendar department links, loads file if exists, tests loaded obj, removes erroneous file and resets on failure
def parse_depts(departments_path):
    global departments_calendar_load_fail
    global name_to_short
    global short_to_name
    loaded_d, departments = load_or_scrape(ucalgary_root,departments_path)
    loaded_n, name_to_short = load_obj(objs_path+'/name_to_short')
    loaded_s, short_to_name = load_obj(objs_path+'/short_to_name')
    if loaded_d and loaded_n and loaded_s:
        departments_calendar_load_fail = False
        return departments
    else:
        if loaded_d:
            #then not n or not s, so parse those
            name_to_short = {}
            short_to_name = {}
            for key in departments.keys():
                name_to_short[departments[key]['title']] = key
                short_to_name[key] = departments[key]['title']
            save_objs(objs_path+'/name_to_short', name_to_short)
            save_objs(objs_path+'/short_to_name', short_to_name)
            return departments
        else:
            lines = departments.split('\n')
            departments={}
            name_to_short = {}
            short_to_name = {}
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
                            try:
                                name_to_short[title] = short
                            except:
                                print(type(name_to_short),type(title),type(short))
                                3/0
                            short_to_name[short] = title
            if type(departments) == type({}) and 'ACCT' in departments.keys() and 'Accounting' in name_to_short.keys() and 'ACCT' in short_to_name.keys():
                save_objs(departments_path, departments)
                save_objs(objs_path+'/name_to_short', name_to_short)
                save_objs(objs_path+'/short_to_name', short_to_name)
            else:
                departments_calendar_load_fail = True
                os.remove(departments_path)
                departments = parse_depts(departments_path)
    departments_calendar_load_fail = False
    return departments

def load_or_scrape(root,path):
    raw = 'raw_html/'
    if os.path.exists(path):
        with open(path) as f:
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
        
        folder = os.path.dirname(raw+path)
        
        if not os.path.exists(folder):
            os.makedirs(folder)
        
        lines = requests.get(root+path,headers=headers).iter_lines()
        with open(raw+path,'w') as f:
            for line in lines:
                f.write(str(line))
        return load_or_scrape(root,path)

def load_obj(obj):
    print('attempting to open',obj)
    if os.path.exists(obj):
        with open(obj) as f:
            return True, jsonpickle.decode(json.load(f))
    else:
        print(obj,'doesn\'t exist')
        return False,None


#will have faculties,with sub-departments, classes schedules, locations, and professors by end of this function
def parse_faculties():
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
        if 'Qatar' in faculty:
            faculty = faculty.replace('\\t',' ')
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
        os.remove(faculties_path)
        contacts_departments_load_fail = True
        faculties = parse_faclties()
    contacts_classes_load_fail = False
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
    global name_to_short
    global short_to_name
    loaded, full_class_info = load_obj(objs_path+'/requisites')
    loaded_n, name_to_short = load_obj(objs_path+'/name_to_short')
    loaded_s, short_to_name = load_obj(objs_path+'/short_to_name')
    if loaded and loaded_n and loaded_s:
        return full_class_info
    departments = parse_depts(departments_path)
    full_class_info = {}
    finished_departments = False
    working = ''
    print('\t',end='')
    while not finished_departments:
        for d in sorted(departments.keys()):
            if d[0] != working:
                working = d[0]
                print ('.',end='')
            class_table = getTableFile(departments[d]['link'],d)
            full_class_info[d] = DEPT(d,departments[d]['title'],class_table)
        finished_departments = not(departments_calendar_load_fail or departments_calendar_class_tables_load_fail)
    print('\n')
    save_objs(objs_path+'/requisites',full_class_info)
    return full_class_info

def scrape_faculties_and_class_schedules(depts):
    loaded_d, departments = load_obj(objs_path+'/schedules')
    loaded_f, faculties = load_or_scrape(contacts_root,faculties_path)

    if loaded_d and loaded_f:
        return departments, faculties
    faculties = parse_faculties()
    departments = {}
    working = ''
    print('\t',end='')
    schedules = {}
    for dept in depts.keys():
        schedules = parse_schedules(dept.lower())
        if schedules is not None:
            for short in schedules.keys():
                if short[0] != working:
                    working = short[0]
                    print ('.',end='')
                departments[short] = schedules[short]
    print('\n')
    save_objs(objs_path+'/schedules',departments)
    return departments, faculties

def joinDepartmentsFaculties(departments, faculties):
    print('combining department and faculty data')
    path_to_file = objs_path+'/FoundDeptFac'
    loaded, found = load_obj(path_to_file)
    
    if loaded:
        print('loaded from disk')
        return found
    else:
        found = {}
        for key in departments.keys():
            if key in faculties:
                found[key] = departments[key]
                for ID in found[key].IDS:
                    if ID in faculties[key]:
                        found[key].IDS[ID].add_field('details',faculties[key][ID]['details'])
        #post merge cleaning - some miscellaneous characters to murder
        for key in found.keys():
            for ID in found[key].IDS:
                for field in found[key].IDS[ID].fields:
                    if field == 'hours':
                        found[key].IDS[ID].hours= re.findall('([0-9]{0,2}|[0-9]{0,2}.[0-9]{0,2}) units',found[key].IDS[ID].hours)[0]
                    elif field != 'raw'and field != 'details':
                        content = getattr(found[key].IDS[ID],field)
                        content2 = content.replace("'b'\\t\\t",'\n').replace("\"b'\\t\\t",'\n').replace("'b\"\\t\\t",'\n')
                        content2 = content2.replace("'b'",' ').replace("\"b'",' ').replace("'b\"",' ').replace('\\t','	')
                        content2 = content2.replace('\\xe2\\x80\\x98','‘').replace('\\xe2\\x80\\x99','’').replace('\\xe2\\x80\\x93','–')
                        content2 = content2.replace('\\xc3\\x89','É').replace('\\xc3\\xaf','ï').replace('\\xc3\\xa0','à').replace('\\xc3\\xa8','è')
                        content2 = content2.replace('\\xc3\\x82','Â').replace('\\xc3\\xb4','ô').replace('\\xc3\\xa2','â')
                        content2 = content2.replace('\\xe2\\x80\\x9c','“').replace('\\xe2\\x80\\x9d','”').replace('\\xe2\\x80\\x94','—')
                        content2 = content2.replace("\\'","'")
                        if content != content2:
                            setattr(found[key].IDS[ID],field,content2)
                            found[key].IDS[ID].raw[field] = content2
        print('saving combined faculties/departments object to disk')
        save_objs(path_to_file,found)
        return found

def bool_parser(ID,s):
    dept_names = []
    for key in department_names:
        dept_names.append(key.strip())
        for key2 in department_names[key]:
            dept_names+= department_names[key][key2]
    #special case program names know previouusly found
    dept_names+=['Master of Management Program','Program Co-ordinator','School of Languages, Linguistics, Literatures and Cultures','Anthropology Honours Program','Archaeology BSc Honours program']
    s = parse.steps(s, name_to_short, dept_names)
    print('')
    print(s)

def bool_parser_old(ID,s):
    #A and B; or C
    #A and B; or A and #units and consent
    #admssion and units including
    #admission including A or B, and C
    
    #replace long names with shorts
    #replace ful names with shorts
    names = sorted([x for x in name_to_short.keys() if x in s],key=len, reverse=True)
    for name in sorted([x for x in name_to_short.keys() if x in s],key=len, reverse=True):
        s = s.replace(name,name_to_short[name])
    short = ''
    words = s.split(' ')
    for i,word in enumerate(words):
        if word in short_to_name.keys():
            short = word
        if re.search('[0-9]{3}',word):
            if words[i-1] != short:
                words[i]=short+word  #REMOVED THE SPACE BETWEEN, NOW CAUSES CLASS ID TOKENISING
    s = ' '.join(words)
#    print('matches = ',[x.strip() for x in re.findall('([A-Z]{2,5} [0-9]{3}.[0-9]{2}[A-Z]{1}|[A-Z]{2,5} [0-9]{3}.[0-9]{2}|[A-Z]{2,5} [0-9]{3})',s) if x.strip() != ID])
    print(s)
    if 'consent' in s.lower() or 'admission' in s.lower():  #then split the string there, the regex fails if thematch is inside the string, not sure why
        #find it
        indices = [i.start() for i in re.finditer('[Aa]dmission|[Cc]onsent',s)]
        indices2 = [i.start() for i in re.finditer(',|\.|;| or| and',s)]
        groups = []
        j=0
        for i in indices:
            groups.append((i,min([k for k in indices2 if k > i]+[len(s)])))
        print(groups)
        for substring in groups:
            s2 = s[substring[0]:substring[1]]+'.'
            print(s2)
            admission = re.match('[aA]dmission to (the |)(.+?(?=\.|,| and| will| may))',s2)
            if admission is not None:
                admission = admission.groups()[-1]
                print('Admission req: ',admission)
            consent = re.match('[cC]onsent of (the |)(.+?(?=\.|,| and| will| may))',s2)
            if consent is not None:
                consent=consent.groups()[-1]
                print('Consent req: ',consent)
    #any n of     list      n may be zero, return n of list matches

def get_everything():
    global department_names
    print('attempting load full class obj')

    print('getting class requisites')
    departments = scrape_department_and_class_reqs()
    print('getting class schedules')
    faculties, department_names = scrape_faculties_and_class_schedules(departments)
    print('data scrape/load completed')
    name_to_short['Applied Mathematics']='AMAT'
    name_to_short['Pure Mathematics']='PMAT'
    short_to_name['AMAT'] = 'Applied Mathematics'
    short_to_name['PMAT'] = 'Pure Mathematics'
    
#    not_found = [x for x in departments.keys() if x not in faculties.keys()]

    found = joinDepartmentsFaculties(departments, faculties)
    
#    found = {}
#    #join data from departments and faculties
#    for key in departments.keys():
#        if key in faculties:
#            found[key] = departments[key]
#            for ID in found[key].IDS:
#                if ID in faculties[key]:
#                    found[key].IDS[ID].add_field('details',faculties[key][ID]['details'])
#                    print(found[key].IDS[ID].details)
#                    input(513)
#    pretty_print_classes(found)
    pretty_print_fields(found)

def pretty_print_fields2(found):
    desire_class_short = None     #if you only want to see a given short
    desire_class_num   =  None       #if you only want a given class number
    desire_class_field = 'prereq'    #if you only want a given field
    begin_from_short = None
    do_print=begin_from_short == None

    print('pretty printing classes...')
    if begin_from_short is not None:
        print('skipping print until '+begin_from_short)
    for key in sorted(found.keys()):
        do_print = do_print or begin_from_short.upper() == key.upper()
        if do_print:
            if desire_class_short is None or desire_class_short == key:  
                for ID in found[key].IDS:
                    if desire_class_num is None or desire_class_num == int(ID[:3]):
                        printed=False
                        for field in found[key].IDS[ID].fields:
                            if desire_class_field is not None:
                                if field == desire_class_field:
                                    printed=True
                                    if field == 'details':
                                        pretty_print_details(getattr(found[key].IDS[ID],field),'\t\t\t')
                                    else:
                                        s = '\t'
                                        for word in getattr(found[key].IDS[ID],field).split(' '):
                                                s = s + word + ' ' 
                                        print(s,end='')
                            else:
                                if field != 'raw':
                                    printed=True
                                    print(field)
                                    if field == 'details':
                                        pretty_print_details(getattr(found[key].IDS[ID],field),'\t\t')
                                    else:
                                        print('\t\t',getattr(found[key].IDS[ID],field))
                        if printed:
                            input()

def pretty_print_fields(found):
    desire_class_short = None     #if you only want to see a given short
    desire_class_num   =  None       #if you only want a given class number
    desire_class_field = 'prereq'    #if you only want a given field
    begin_from_short = 'ENCH'
    do_print=begin_from_short == None
#    desire_terms = ['One of','ONE of','1 of','one of','one from','one from','ONE from','1 from']
    desire_terms = ['Two of','TWO of','2 of','two of','two from','Two from','TWO from','2 from']
    desire_terms+= ['Three of','THREE of','3 of','three of','three from','Three from','THREE from','3 from']
    desire_terms+= ['Four of','FOUR of','4 of','four of','four from','Four from','FOUR from','4 from']
    desire_terms=None

    
    print('pretty printing classes...')
    if begin_from_short is not None:
        print('skipping print until '+begin_from_short)
    for key in sorted(found.keys()):
        do_print = do_print or begin_from_short.upper() == key.upper()
        if do_print:
            if desire_class_short is None or desire_class_short == key:  
                for ID in found[key].IDS:
                    if desire_class_num is None or desire_class_num == int(ID[:3]):
                        printed=False
                        for field in found[key].IDS[ID].fields:
                            if desire_class_field is not None:
                                if field == desire_class_field and (desire_terms==None or [x for x in desire_terms if x in getattr(found[key].IDS[ID],field)]):
                                    printed=True
                                    print(getattr(found[key].IDS[ID],'short'),getattr(found[key].IDS[ID],'num'),getattr(found[key].IDS[ID],'name'))
                                    print('\t'+field)
                                    if field == 'details':
                                        pretty_print_details(getattr(found[key].IDS[ID],field),'\t\t\t')
                                    else:
                                        s = '\t\t'
                                        for word in getattr(found[key].IDS[ID],field).split(' '):
                                            if len(s + word) > 80:
                                                print(s)
                                                s = '\t\t'+word+' '
                                            elif len(word) > 0:
                                                s = s + word + ' ' 
                                        s=s+'\n\n'
                                        print(s)
                                        if field in ['antireq','coreq','prereq']:
                                            bool_parser(key+' '+ID,getattr(found[key].IDS[ID],field))
                            else:
                                if field != 'raw':
                                    printed=True
                                    print(field)
                                    if field == 'details':
                                        pretty_print_details(getattr(found[key].IDS[ID],field),'\t\t')
                                    else:
                                        print('\t\t',getattr(found[key].IDS[ID],field))
                                        if field in ['antireq','coreq','prereq']:
                                            bool_parser(key+' '+ID,getattr(found[key].IDS[ID],field))
                        if printed:
                            print('\n\npress enter for next class...')
                            input('you can safely use crl-c to exit immediately as well\n\n')

            
def pretty_print_details(details,prefix=''):
    for t in details:  #type, lec, lab, etc
        for n in details[t]:   #number of type, tut2, lec 3, etc
            print(prefix,t,n,'\t',details[t][n]['day'],'\t',details[t][n]['time'],'\t',details[t][n]['room'],'\t',details[t][n]['prof'])

#outputs every class that yielded schedule data, and for each of those the schedules indented on following lines.
def pretty_print_classes(found):
    dept_count = 0
    class_count = 0
    schedule_count = 0

    last_dept=None
    last_class=None

    for key in sorted(found.keys()):
        for i in sorted(found[key].IDS.keys()):
            if hasattr(found[key].IDS[i],'details') and len(found[key].IDS[i].details.keys()) > 0:
                for t in ['SEM','LEC','LAB','TUT']:
                    if t in found[key].IDS[i].details:
                        for n in sorted(found[key].IDS[i].details[t].keys()):
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
#
#
#       #  implementing soon
#       class.scheds                                # (collection of schedule objects, a dict in python)
#       class.scheds.type.n                         # (location of each schedule object)
#
#       #  deprecating soon
#       #   class.details                               # (details, will likely replace with a schedule object to be built soon
#       #   class.details.type                          # (LEC,LAB,TUT,SEM)
#       #   class.details.type.n                        # (number of type, 2 for tut2, 3 for lec3, etc)
#       #   class.details.type.n.day                    # (day of class, in string format with MTWRF for mon, tues, wed, thurs, fri respectively)
#       #   class.details.type.n.time                   # (time of each class, currently in string format as "XX:XX - XX:XX" 
#       #   class.details.type.n.room                   # (room the class is held in)
#       #   class.details.type.n.prof                   # (prof/TA teaching)
#       #   class.details.type.n.seats                  # (not yet contained, want/need this for knowing if schedule is open)
#       #   class.details.type.n.free                   # (not yet contained, want/need this for knowing if schedule is open)
#       #   class.details.type.n.associated             # (not yet contained, want/need this for knowing related classes, such as Lec N must take TUT M and Lab O)
#
#   might generate a schedule to replace the class details field with
#   might generate a schedule to replace the class details field with
#   schedule may contain relevant class info:
#       sched.parent                                # (parent class obj for object backtracing - to ease swapping one class schedule for another)
#       sched.type                                  # (LEC,LAB,TUT,SEM)
#       sched.n                                     # (number of type, 2 for tut2, 3 for lec3, etc)
#       sched.day                                   # (day of class, in string format with MTWRF for mon, tues, wed, thurs, fri respectively)
#       sched.time                                  # (time of each class, currently in string format as "XX:XX - XX:XX" 
#       sched.room                                  # (room the class is held in)
#       sched.prof                                  # (prof/TA teaching)
#       sched.seats                                 # (want/need this for knowing if schedule is open)
#       sched.free                                  # (want/need this for knowing if schedule is open)
#       sched.associated                            # (obj cross references, want/need this for knowing related classes, such as Lec N must take TUT M and Lab O)







