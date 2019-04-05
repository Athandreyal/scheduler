import json,copy

class BOOL():
    def __new__(self,*new_items):
        if self is BOOL:
            raise TypeError("\n\tusing BOOL object not permited\n\tuse AND,OR,NAND,NOR,or XOR instead")
        else:
            return object.__new__(self)
    def __init__(self,*items):
        self.items = []
        for i in items:
            if hasattr(i,'items'):
                for j in i.items:
                    self.items.append(copy.deepcopy(j))
            else:
                self.items.append(i)
    def append(self,item):
        self.items.append(item)
    def __bool__(self):
        return bool(self.eval())
    def __str__(self):
        return str(self.__bool__())
    def __repr__(self):
        return str(type(self)).split('.')[1][:-2]+': '+str(self.eval())+' -> '+json.dumps([bool(i) for i in self.items])
    def __iter__(self):
        return iter([bool(i) for i in self.items])
    def __call__(self,item=None):
        return self.eval(item)
    def eval(self, item=None):
        if not self.items:  #nothing to eval, default True
            return True
        else:
            return self.eval2(item)
    def contains(self,o):
        return o in self.items
    def type(self):
        return type(self)
    def parent_type(self):
        return type(BOOL)

class AND(BOOL):
    def eval2(self,items=None):
        print('eval2')
        return not False in self.__iter__()

class OR(BOOL):
    def eval2(self,items=None):
        return True in self.__iter__()

class NAND(AND):
    def eval2(self,items=None):
        return False in self.__iter__()

class NOR(OR):
    def eval2(self,items=None):
        return not True in self.__iter__()

class XOR(OR):
    def eval2(self,items=None):
        return sum([1 for i in self.__iter__() if i == True]) == 1

#counted or - Must have this many true
class COR(OR):
    #strips off and keeps count value, passes remainder onto super for constructor
    def __init__(self,*items):
        super().__init__(items[1])
		self.count, items = int(items[0]),items[2:]
        for item in items:
            self.items.append(item)
                
    def eval2(self,items=None):
        return sum([1 for i in self.__iter__() if i == True]) >= self.count
    
    def __repr__(self):
        c = sum([1 for i in self.__iter__() if i == True])
        return str(type(self)).split('.')[1][:-2]+': '+str(c)+'+ '+str(self.eval())+' -> '+json.dumps([bool(i) for i in self.items])

def pre_parse(string):
    string = string.replace(',',', ').replace(';','; ').replace('.','. ')
    tokens = string.split(' ')
    string = '('
    last = None
    parens=0
    OR =0
    q = []
    while tokens:
        substring = ''
        token,tokens = tokens[0],tokens[1:]
        if token.strip().upper() in ['AND','OR']:
            last = token.upper().strip()
            token = token.upper()
        if ';' in token:
            token = token.replace(';',' ) AND ( ')
            last = None
        if ',' in token:
            if last is not None:
                token = token.replace(',',' '+last+' ')
            else:
                q.append(token.replace(',',''))
                token = ''
        if last is not None:
            while q:
                t,q = q[0],q[1:]
                substring += t+' '
                if q:
                    substring += last+' '
            token = substring+token.replace(',',' '+last+' ')
        if '.' in token:
            last = None
        if token:
            string+=token+' '
    string+=')'
    while '  ' in string:
        string = string.replace('  ',' ')
    string = string.replace('AND OR','OR').replace('OR AND','AND')
    return string

#print(pre_parse('a and b and c;d or e,f,g;h and i,j,k,l,m;n,o,p,or q'))
#a or b;c or d; and one of e, f or g
# ( (a or b) and (c or d) and (e or1 f or1 g or1 h) )

#a,b; c or d; one of e,f,g
#( (a and b) and (c or d) and (e or1 f or1 g or1 h) )

def pre(string):
    import re
    segments = re.split(';|\.',string)
    print(segments)
    string = '( ' + ' ) and ( '.join(segments) + ' )'
    string = string.replace(',',' , ')
    print(string)
    string = string.replace('one of','1:')
    #parse the chained elements
    print(string)
    segments = string.split(' ')
    print(segments)
    for i,token in enumerate(segments):
        if token.lower() == 'and':
            segments[i] = '*'
        elif token.lower() == 'or':
            segments[i] = '+'
        elif token.lower() == ',':
            segments[i]=','
        elif token not in '()':
            segments[i] = token
    string = ' '.join(segments)
    print(string)
    

#def preShunt(string):
    

    
    
def strNum_to_num(string):
    words = string.split(' ')
    n = {'one':'1','two':'2','three':'3','four':'4','five':'5','six':'6','seven':'7','eight':'8','nine':'9','ten':'10','eleven':'11','twelve':'12','thirteen':'13'}
    for i in range(len(words)):
        words[i] = n.get(words[i].lower(),words[i])
    return ' '.join(words)
        
def any_N(string):
    import re
    string = strNum_to_num(string)
    'and n of'
    'any n of'
    'n from'
    
