#expects and requires spaces between terms and operators
def shunt(s):
    ops = []
    end = []
    precedence = '()[]!/*+-'
    for c in precedence:
       s = s.replace(c,'_'+c.strip()+'_')
    print(s)
    left = '()[]*/+-'
    right = '!'
    s = s.replace('_ _','_').replace('__','_')
    s = s.split('_')
    print(s)
    for term in s:
        term = term.strip()
        print("'"+term+"'",'\t',end = '')
        
        if term not in precedence:   #1
            print(term,'is term, appending to end')
            end.append(term)
            
        else: #is operand
            
            if term in '([':  #2
                print(term,'in \'([\', adding to ops')
                ops.append(term)
                
            elif term in ')]':  #3
                print(term,'in \')]\', emptying ops')
                while ops:
                    t = ops[-1]
                    ops = ops[:-1]
                    if t in '[(':
                        break
                    else:
                        end.append(t)
                        
            else: #is operator
                if not ops or ops[-1] in '[(':  #4
                    ops.append(term)
                    
                elif precedence.index(term) < precedence.index(ops[-1]): #5.1
                    ops.append(term)
                elif precedence.index(term) == precedence.index(ops[-1]) and term in right: #5.2
                    ops.append(term)
                    
                elif precedence.index(term) > precedence.index(ops[-1]): #6.1
                    while ops:
                        t = ops[-1]
                        ops = ops[:-1]
                        if t in '[(':
                            break
                        else:
                            end.append(t)
                    ops.append(term)
                elif precedence.index(term) == precedence.index(ops[-1]) and term in left:
                    while ops:
                        t = ops[-1]
                        ops = ops[:-1]
                        if t in '[(':
                            break
                        else:
                            end.append(t)
                    ops.append(term)
                    
        print(ops,'\t',end)
    while ops:
        t = ops[-1]
        ops = ops[:-1]
        if t not in '[(':
            end.append(t)
    print(end)
    print(ops)
    return end

def calc(formula):
    formula = shunt(formula)
    terms = []
    for e in formula:
        print(e)
        if e in '+-*/':
            print(terms)
            a = float(terms[-2])
            b = float(terms[-1])
            print(a,e,b)
            terms = terms[:-2]
            if e == '*':
                terms.append(a*b)
            if e == '/':
                terms.append(a/b)
            if e == '+':
                terms.append(a+b)
            if e == '-':
                terms.append(a-b)
            print(terms[-1])
        elif e in '!':
            print(e,terms[-1])
            terms[-1] = not float(terms[-1])
            print(terms[-1])
        else:
            terms.append(e)
    return terms[-1]
