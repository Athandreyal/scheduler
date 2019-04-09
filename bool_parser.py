import re
if __name__ == '__main__':
    strings = {
        'ACCT641': 'Accounting 601 and 603; or consent of the Haskayne School of Business.',
        'ACSC325': 'One of: Mathematics 249, 265 or 275.',
        'ACSC425': 'Actuarial Science 325 and Statistics 323; or Actuarial Science 325 and 60 units and consent of the Department.',
        'ACSC427': 'Actuarial Science 327; Statistics 323; one of Mathematics 311, 313, 367 or 375.',
        'ACSC527': 'Actuarial Science 327; Statistics 323; one of Mathematics 311, 313, 367 or 375; and one of Computer Science 217, 231, 235 or Data Science 211.',
        'ACSC627': 'Actuarial Science 327; and one of Statistics 323 or Mathematics 323; and one of Mathematics 311 or 313 or 353 or 367 or 375 or 381; and one of Computer Science 217 or 231 or 235.',
        'ANTH501': 'Anthropology 203 and one senior Anthropology course and consent of the Department.',
        'ARHI501': '18 units in Art History at the 300 level or above and consent of the Department.',
        'ARKY595': 'Anthropology 201, Archaeology 555 and either Anthropology 350 or Archaeology 203, and admission to the Archaeology or Anthropology major.',
         'ART661': 'For Art 661.01: Admission to a graduate program in the Department of Art. For Art 661.02, the prerequisite is Art 661.01.',
        'ASPH307': 'Astrophysics 213 or 305; one of Physics 211, 221, 227 or Engineering 202; and one of Physics 255, 259 or 323.',
        'BCEM393': 'Chemistry 351; and Biology 311 or admission to the BHSc Honours program and Medical Sciences 341.',
        'BCEM471': 'Biochemistry 341 or 393; Chemistry 353 or 355; one of Mathematics 249, 251, 265, 275, 281, or Applied Mathematics 217 and one of Mathematics 253, 267, 277, 283, 211, 213, or Applied Mathematics 219; and Physics 211 or 221, and 223.',
        'CHEM201': 'Chemistry 30 (or Continuing Education - Chemistry 2) and one of Mathematics 30-1 or Mathematics 2 (offered by Continuing Education).',
        'CNST501': 'One of: Art 361, Communication and Media Studies 313, History 300, Political Science 399 or Sociology 313 and consent of the Department.',
    }
    dept = ['Haskayne School of Business','BHSc Honours program','Department of Art']

    name_to_short = {
        'Accounting':'ACCT',
        'Mathematics':'MATH',
        'Pure Mathematics':'MATH',
        'Applied Mathematics':'MATH',
        'Actuarial Science':'ACSC',
        'Statistics':'STAT',
        'Computer Science':'CPSC',
        'Data Science':'DATA',
        'Anthropology':'ANTH',
        'Archaeology':'ARKY',
        'Art':'ART',
        'Astrophysics':'ASPH',
        'Physics':'PHYS',
        'Engineering':'ENGI',
        'Chemistry':'CHEM',
        'Biology':'BIOL',
        'Biochemistry':'BCEM',
        'Communication and Media Studies':'COMS',
        'History':'HIST',
        'Political Science':'POLI',
        'Sociology':'SOCI',
        'Medical Sciences':'MEDI',
        'Art History':'ARHI'}
else:
    dept = {}
    name_to_short = {}

#prepatory work to fix difficult edge cases
def step1(s):
    #straight replace
    s = s.replace('For certain topics,','For certain topics')
    s = s.replace('The corresponding language in ','')
    s = s.replace('School of Languages, Linguistics, Literatures and Cultures','School_of_Languages_Linguistics_Literatures_and_Cultures'.upper())
    s = s.replace('Anthropology 350,','Anthropology 350 and')
    s = s.replace(' level, including',' level including',)
    s = s.replace('Applied Mathematics','MATH')
    s = s.replace('Pure Mathematics','MATH')
    s = s.replace('Drama or Drama Education program','DRAMA_PROGRAM OR DRAMA_EDUCATION_PROGRAM')
    s = s.replace('Master of Arts Economics ( ','MASTER_OF_ARTS_ECONOMICS_PROGRAM')
    
    #rto upper and join with _
    strings = ['Anthropology Honours Program','Archaeology BSc Honours program','Archaeology BA Honours program',
               'BHSc Honours program','BHSc program','Schulich School of Engineering','Management and Society',
               'Master Management program','Applied Chemistry','Chemical Physics','Department of Physics and Astronomy',
               'Biological Sciences Honours program','Canadian Studies Honours Program','Master of Arts Economics program',
               'Leadership in Pedagogy and Coaching','Graduate Certificate in Fundamental Data Science and Analytics',
               'Graduate Diploma in Data Science and Analytics','Development Studies Honours Program','PhD program in Economics',
               
     ]
    for p in strings:
        s = s.replace(p,('_'.join(p.split(' '))).upper())
    
    #s = s.replace('Anthropology Honours Program','_'.join('Anthropology Honours Program'.split(' ')).upper())
    #s = s.replace('Archaeology BSc Honours program','_'.join('Archaeology BSc Honours program'.split(' ')).upper())
    #s = s.replace('Archaeology BA Honours program','_'.join('Archaeology BA Honours program'.split(' ')).upper())
    #s = s.replace('BHSc Honours program','BHSc_Honours_program'.upper())
    #s = s.replace('BHSc program','BHSc_program'.upper())
    #s = s.replace('Schulich School of Engineering','Schulich_School_of_Engineering'.upper())
    #s = s.replace('Management and Society','Management_and_Society'.upper())
    #s = s.replace('Master Management program','Master_Management_program'.upper())
    #s = s.replace('Applied Chemistry','Applied_Chemistry'.upper())
    #s = s.replace('Chemical Physics','Chemical_Physics'.upper())
    #s = s.replace('Department of Physics and Astronomy','Department_of_Physics_and_Astronomy'.upper())
    #s = s.replace('Biological Sciences Honours program','Biological_Sciences_Honours_program'.upper())
    return s
    

#substitute continuing ED/high school classes:  https://conted.ucalgary.ca/public/category/programArea.do?method=load&selectedProgramAreaId=10550
def step2(s):
    cted_classes = {
    'biology 20':'UPG110',
    'biology 30':'UPG210',
    'chemistry 20':'UPG140',
    'chemistry 30':'UPG240',
    'english language arts 30-1':'UPG222',
    'mathematics 10c':'UPG010',
    'mathematics 20-1':'UPG020',
    'mathematics 30-1':'UPG101',
    'mathematics 31':'UPG031',
    'physics 20':'UPG130',
    'physics 30':'UPG230',
    }
    for c in sorted(cted_classes.keys(),reverse=True):
        pattern = re.compile(re.escape(c+' '),re.IGNORECASE)
        s = pattern.sub(cted_classes[c]+' ',s)
    r = ''
    skip=False
    for c in s:
        if c == '(':
            skip = True
        if not skip:
            r+=c
        else:
            if c == ')':
                skip=False
    return r

#substitute '([cC]onsent of [the|]|[aA]dmission to [the|])' with CONSENT or ADMISSION respectively
def step3(s):
    pattern0=re.compile('((^| )consent (of )?(the )?)',re.IGNORECASE)
    pattern1=re.compile('((^| )admission (to |into)?(the |a )?)',re.IGNORECASE)
    pattern2=re.compile('((to |in |of )?(the )?department)( |\.|,|;)+',re.IGNORECASE)
    pattern3=re.compile('((to |in |of )?(the )?faculty)( |\.|,|;)+',re.IGNORECASE)
    pattern4=re.compile('((to |in |of )?(the )?director)( |\.|,|;)+',re.IGNORECASE)
    pattern5=re.compile('((to |in |of )?(the )?designate)( |\.|,|;)+',re.IGNORECASE)
    pattern6=re.compile('((^| )enrolment (in |into)?(the )?)',re.IGNORECASE)
    pattern7=re.compile('((^| )audition( in)?( the)?)( |\.|,|;)+',re.IGNORECASE)
    pattern8=re.compile('((to |in |of )?(the )?Division Chair)( |\.|,|;)+',re.IGNORECASE)
    
    match0 = re.search(pattern0,s)
    match1 = re.search(pattern1,s)
    match2 = re.search(pattern2,s)
    match3 = re.search(pattern3,s)
    match4 = re.search(pattern4,s)
    match5 = re.search(pattern5,s)
    match6 = re.search(pattern6,s)
    match7 = re.search(pattern7,s)
    match8 = re.search(pattern8,s)
    if match0:
        s = pattern0.sub(' CONSENT ',s)
    if match1:
        s = pattern1.sub(' ADMISSION ',s)
    if match2:
        s = pattern2.sub('THIS_DEPT ',s)
    if match3:
        s = pattern3.sub('THIS_FACULTY ',s)
    if match4:
        s = pattern4.sub('DIRECTOR ',s)
    if match5:
        s = pattern5.sub('DESIGNATE ',s)
    if match6:
        s = pattern6.sub(' ENROLMENT ',s)
    if match7:
        s = pattern7.sub(' AUDITION ',s)
    if match8:
        s = pattern8.sub(' DIVISION_CHAIR ',s)
    return s

#SUBSTITUTE DEFUNCT PMAT AND AMAT WITH MATH WHERE KNOWN.  Substitute all class long names for short tokens, ie 'Cellular, Molecular and Microbial Biology 343' -> 'CMMB343'
def step4(s):
    for name in sorted([x for x in name_to_short.keys() if x in s],key=len, reverse=True):
        pattern = re.compile(name+'( |\.)',re.IGNORECASE)
        s = pattern.sub(name_to_short[name]+' ',s)
    short = ''
    words = s.split(' ')
    for i,word in enumerate(words):
        if word in name_to_short.values():
            short = word
        if re.search('[0-9]{3}',word):
            if i > 0 and (words[i-1] == short or ',' in words[i-1] or words[i-1].lower() in ['and','or']):
                words[i]=short+word  #REMOVED THE SPACE BETWEEN, NOW CAUSES CLASS ID TOKENISING
                if words[i-1]==short:
                    words[i-1]=''  #REMOVED THE SPACE BETWEEN, NOW CAUSES CLASS ID TOKENISING
    for i,word in enumerate(words):  #second round to catch a few exceptions to the above
        if i > 0 and words[i-1] in name_to_short.values():
            try:
                int(words[i])
                words[i-1]=words[i-1]+words[i]
                words[i]=''
            except:
                pass
    s = ' '.join([w for w in words if w])
    return s

#SUBSTITUTE rename named departments with 'A C D' -> 'A_B_C' to make them a single token
def step5(s):
    for name in sorted([x for x in dept if x in s],key=len, reverse=True):
        s = s.replace(name,' '+'_'.join(name.strip().split(' ')).upper())
    return s

#SUBSTITUTE '. AND' OR '. OR' WITH ', AND' OR ', OR' RESPECTIVELY.
#SUBSTITUTE "either a,b,c,d or e" with (XOR a,b,c,d,e), substitute 'including' with AND and ('any of:' or 'any of') or ('any N of' or 'any N of:') with 'ONE_OF' or 'N_OF', respectively, and replace contained 'OR' or 'AND' with ', '.
def step6(s):
    s = s.replace(',',', ').replace(';','; ')
    pattern0=re.compile('any of[ :|:|]',re.IGNORECASE)
    pattern1=re.compile('one( or two)? of[ :|:|]',re.IGNORECASE)
    pattern2=re.compile('two of[ :|:|]',re.IGNORECASE)
    pattern3=re.compile('three of[ :|:|]',re.IGNORECASE)
    s = pattern3.sub('ANY_3',pattern2.sub('ANY_2',pattern1.sub('ANY_1',pattern0.sub('ANY_1',s))))
    s = s.replace('ANY_1','ANY_1 ').replace('ANY_2','ANY_2 ').replace('ANY_3','ANY_3 ').replace('  ',' ')
    #for some retarded reason, sometimes the pattern match insists on consuming the space, no idea why yet.  Forcefully ensure space exists.
    s = s.replace('(','( ').replace(')',' )')
    tokens = s.split(' ')
    any_=None
    for i,token in enumerate(tokens):
        if 'ANY_' in token: #any N list
            any_=True
        elif '.' in token or ';' in token:
            any_=False
        if token.lower() in ['or'] and any_:
            tokens[i]=''
        elif token.lower() in ['and'] and any_:
            any_=False
    s = ' '.join([x for x in tokens if x])
    s = s.replace(' ,',',')
    return s

#  Find and replace chained 'a,b,c [,and|,or|and|or] d' lists with 'a and/or b and/or c and/or d'
#   ignore ANY_N lists, they are dealt with later.
def step7(s):
    #a AND b OR c,d,e,f     -> a AND (b OR c OR d OR e OR f)
    #a AND b,c,d,e, or f    -> a AND (b OR c OR d OR e OR f)

    #runs off the end of the array without this.
    if s.strip()[-1] !='.':
        s+='.'

    tokens = s.split(' ')
    last=None
    q=[]
    string=''
    any_=False
    XOR=False
#    print(s)
#    print(tokens)
    while tokens:
        token,tokens = tokens[0],tokens[1:]
#        print('155 any=',any_,', XOR=',XOR,', L=',last,', t=',token,', q=',q,', str=',string)
        if 'any_' in token.lower():  #beginning of an any list
            any_ = True
            XOR=False
            last=None
            string+='('+token+' '
#            print('161 any=',any_,', XOR=',XOR,', L=',last,', t=',token,', q=',q,', str=',string)
        elif any_ and not '.' in token and not ';' in token:
            if token.strip().lower() == 'and':
                string+= ') '+token+' '
                any_=False
#                print('166 any=',any_,', XOR=',XOR,', L=',last,', t=',token,', q=',q,', str=',string)
            else:
                string+= token+(' ' if ',' in token else ', ')
#                print('169 any=',any_,', XOR=',XOR,', L=',last,', t=',token,', q=',q,', str=',string)
        elif any_ and ('.' in token or ';' in token):
            any_=False
            string+=token.replace('.','). ').replace(';','); ')
#            print('173 any=',any_,', XOR=',XOR,', L=',last,', t=',token,', q=',q,', str=',string)
        else:
            if token.strip().lower() == 'either':
                string+='('
                XOR=True
                last=None
            elif XOR:
                if '.' in token or ';' in token:
                    XOR=False
                    string+=token.replace(';',');').replace('.',').')+' '
#                    print('183 any=',any_,', XOR=',XOR,', L=',last,', t=',token,', q=',q,', str=',string)
                elif 'and' == token.strip().lower():
                    string+=') AND '
                    XOR=False
#                    print('187 any=',any_,', XOR=',XOR,', L=',last,', t=',token,', q=',q,', str=',string)
                elif 'or' == token.strip().lower():
                    pass
#                    print('190 any=',any_,', XOR=',XOR,', L=',last,', t=',token,', q=',q,', str=',string)
                elif ',' in token:
                    string+='XOR '+token.replace(',','')
#                    print('193 any=',any_,', XOR=',XOR,', L=',last,', t=',token,', q=',q,', str=',string)
                elif string[-1] == '(':
                    string+= token+' '
#                    print('196 any=',any_,', XOR=',XOR,', L=',last,', t=',token,', q=',q,', str=',string)
                else:
                    string+= 'XOR '+token+' '
#                    print('199 any=',any_,', XOR=',XOR,', L=',last,', t=',token,', q=',q,', str=',string)
            else:
                if token.strip().upper() in ['AND','OR']:
                    last = token.strip().upper()
                    if q:
                        while q:
                            token,q=q[0],q[1:]
                            string+= token+' '+last+' '
                    else:
                        string+=token.upper()+' '
#                    print('209 any=',any_,', XOR=',XOR,', L=',last,', t=',token,', q=',q,', str=',string)
                else:
                    if '.' in token or ';' in token:
                        if q:
                            while q:
                                t,q=q[0],q[1:]
                                if re.match('[A-Z]{3-4}[0-9]{3}',t) is not None:
                                    string+= t+' '+ ('AND' if last == None else last)+' '
                                else:
                                    string+= t+' '
                        string+= token+' '
                        last=None
#                        print('221 any=',any_,', XOR=',XOR,', L=',last,', t=',token,', q=',q,', str=',string)
                    elif ',' in token:
                        if last is not None:
                            string+= token+' '+((last +' ') if tokens[0].strip().lower() not in ['and','or'] else '')
#                            print('225 any=',any_,', XOR=',XOR,', L=',last,', t=',token,', q=',q,', str=',string)
                        else:
                            q.append(token)
#                            print('228 any=',any_,', XOR=',XOR,', L=',last,', t=',token,', q=',q,', str=',string)
                    else:
                        if tokens[0].lower() in ['and','or']:# or ',' in tokens[0]:
                            q.append(token)
#                            print('232 any=',any_,', XOR=',XOR,', L=',last,', t=',token,', q=',q,', str=',string)
                        else:
                            string+= token+' '
#                            print('235 any=',any_,', XOR=',XOR,', L=',last,', t=',token,', q=',q,', str=',string)
#    print('L=',last,', t=',token,', q=',q,', str=',string)
    s = string
    while '  ' in s:
        s = s.replace('  ',' ')  #remove multiple spaces that might result
    return s

#determine which or's are higher precedence and parenthesize them to preserve it.  eg, "; and ONE_OF CPSC217, CPSC231, CPSC235"  or "; and PHYS211 or PHYS221,"
def step8(s):
    indices = [0]+[i.span()[0]+1 for i in re.finditer(';',s,re.IGNORECASE)]+[len(s)]
    pieces= [(s[indices[i]:indices[i+1]])[:-1] for i in range(len(indices)-1)]
    
    if len(pieces) > 1:
        for i,piece in enumerate([s.strip() for s in pieces]):
            if 'and ' in piece[:4].lower():
                pieces[i] = piece[:4]+'( '+piece[4:]
            elif 'or ' in piece[:3].lower():
                pieces[i] = piece[:3]+'( '+piece[3:]
            else:
                pieces[i] = '( '+piece
            if (pieces[i].strip())[-1] == '.':
                pieces[i] = (pieces[i].strip())[:-1]+' ).'
            else:
                pieces[i]+=' )'
        s = ' '.join(pieces)
        s = s.replace(') (',') AND (').replace('( (','( ').replace(') )',' )')
    pieces = s.split(' ')
    for i,p in enumerate(pieces):
        if p == ')' and pieces[i-2] == '(':
            pieces[i]=''
            pieces[i-2]=''
    s = ' '.join([p for p in pieces if p])
    return s

#substitute '[at |][the |]XXX level or above' with '>XXX' and 'X units' with 'X_UNITS' and ('X units from' or 'X units in') with 'X_UNITS_IN'
def step9(s):
    pattern0=re.compile('(( at)?( the)? (?P<L>[0-9]{3}) level(,| )(or above)?)',re.IGNORECASE)
    pattern1=re.compile('((^| )(completion of )?(at least )?(?P<U>[0-9]+) unit(s)? (in |from |of ))',re.IGNORECASE)
    pattern2=re.compile('((^| )(completion of )?(at least )?(?P<U>[0-9]+) unit(s)?(.|,| ))',re.IGNORECASE)
    pattern3=re.compile('(including (?P<L>(.+?(?=\.))))',re.IGNORECASE)
    pattern4=re.compile('((^| )(completion of )?(at least )?(?P<U>[0-9]+) unit(s)? (of )?(?P<c>[A-Z]{3,4}) course(s)?)',re.IGNORECASE)
    match0 = re.search(pattern0,s)
    match1 = re.search(pattern1,s)
    match2 = re.search(pattern2,s)
    match3 = re.search(pattern3,s)
    match4 = re.search(pattern4,s)
    
    if match4:
        s = pattern4.sub(' '+match4.group('U')+'_UNITS_IN '+match4.group('c')+' ',s)
    if match0:
        s = pattern0.sub(' >'+match0.group('L'),s)
    if match1:
        s = pattern1.sub(' '+match1.group('U')+'_UNITS_IN  ',s)
    if match2:
        s = pattern2.sub(' '+match2.group('U')+'_UNITS  ',s)
    if match3:
        s = pattern3.sub(' AND ( '+match3.group('L')+' )',s)

    return s

#SUBSTITUTE remaining and/or tokens with all caps for simplicity
def step10(s):
    s = s.replace(' and ',' AND ').replace(' or ',' OR ')
    return s


 #retag mention of major/minor/program,
    #'([a|the|an|]* [under|][gG]rad[uate|] [program |in |the |]*<NAME>)'    -> UNDERGRAD/GRAD <NAME>
    # <name> [major|minor]                                                  -> MAJOR/MINOR NAME
    # '[major|minor] in <name>'                                             -> MAJOR/MINOR NAME
    # note lists involving multiple major/minor references and retage each:
    # <name> and/or <name> [major|minor]                                    -> MAJOR/MINOR NAME and/or MAJOR/MINOR NAME
def step11(s):
    pattern0 = re.compile('((^| )(a )?(the )?(an )?(?P<g>(under)?grad)(uate)? (program(s)? )?( in)?( the)?(?P<P>[a-zA-Z_]+))',re.IGNORECASE)
    pattern1 = re.compile('((?P<name>\w)(?P<m>(major |minor )))',re.IGNORECASE)
    pattern2 = re.compile('((?P<m>(major |minor ))(in |of |from )?(?P<name>[A-Z]{3,4}))',re.IGNORECASE)
    pattern3 = re.compile(' (to |in |of )?(the )?',re.IGNORECASE)
    
    pattern9 = re.compile('(?P<g>(minor|major))',re.IGNORECASE)
    s = s.replace('program offered by the','')
    
    match0 = re.search(pattern0,s)
    match1 = re.search(pattern1,s)
    match2 = re.search(pattern2,s)
    match3 = re.search(pattern3,s)
    match9 = re.search(pattern9,s)
    if match0:
        s = pattern0.sub(' '+match0.group('g').upper()+' '+match0.group('P')+' ',s) 
#        print('L354',s)
    if match1:
        s = pattern1.sub(' '+match1.group('name')+' '+match1.group('m').upper()+' ',s) 
#        print('L357',s)
    if match2:
#        print(match2)
        s = pattern2.sub(' '+match2.group('name')+' '+match2.group('m').upper()+' ',s) 
#        print('L360',s)
#    print('L361',s)
    if match3:
        s = pattern3.sub(' ',s)
#        print('L364',s)
    if match9:
        s = pattern9.sub(match9.group('g').upper(),s)
#    print('L365',s)
    return s

#remaining special cases...
def step12(s):
    pattern0 = re.compile('((, )?prerequisite is)',re.IGNORECASE)
    pattern1 = re.compile('((?P<N>(one |two |three |four |five |six |seven |eight |nine ))(?P<L>senior )(level )?(?P<P>[A-Z]+) course(s)?)',re.IGNORECASE)
    pattern3 = re.compile('((?P<N>(one |two |three |four |five |six |seven |eight |nine ))(?P<L>JUnior )(level )?(?P<P>[A-Z]+) course(s)?)',re.IGNORECASE)
    pattern2 = re.compile('((a )?grade (of )?(\"|\')?(?P<g>([a-z]|[0-9]{2}))(\"|\')?.* (?P<c>[A-Z]+[0-9]{3}))',re.IGNORECASE)
    match0=re.search(pattern0,s)
    match1=re.search(pattern1,s)
    match2=re.search(pattern2,s)
    match3=re.search(pattern3,s)
    if match0:
        s = pattern0.sub(':',s)
    if match1:
        s = pattern1.sub('( '+match1.group('N').upper()+match1.group('L').upper()+match1.group('P')+' )',s)
    if match2:
        s = pattern2.sub('( GRADE_'+match2.group('g')+' '+match2.group('c')+' )',s)
    if match3:
        s = pattern3.sub('( '+match3.group('N').upper()+match3.group('L').upper()+match3.group('P')+' )',s)
    s = s.replace('ADMISSION ARKY OR ANTH major','( ADMISSION MAJOR ARKY OR ADMISSION MAJOR ANTH )')
    return s

#misc cleanup
def step13(s):
    s = s.replace(', AND',' AND').replace(', OR',' OR')
    return s

def steps(s, n_to_s, depts):
    global name_to_short, dept
    if not s.strip():
        return s
    name_to_short = n_to_s
    dept=depts
    debug=False
    #loop steps through easch of the 'step' functions, calls it with s, and increments the integer for the next step
    func=1
    while 'step'+str(func) in globals():
        step=globals()['step'+str(func)]
        s = step(s)
        if debug:
            print(func,s)
        func+=1
        
    
    if __name__ == '__main__':
        print(s)
    return s

if __name__ == '__main__':
    print([(print(''),print(s,':',strings[s]),print(s,':',steps(strings[s],name_to_short, dept)),input()) for s in strings.keys()])
