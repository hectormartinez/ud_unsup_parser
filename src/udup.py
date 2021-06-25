from collections import defaultdict, Counter
from pathlib import Path
import argparse
import sys, copy
import networkx as nx
import numpy as np
from lib.conll import CoNLLReader, DependencyTree
from pandas import pandas as pd

OPEN="ADJ ADV INTJ NOUN PROPN VERB".split()
CLOSED="ADP AUX CONJ DET NUM PART PRON SCONJ".split()
OTHER="PUNCT SYM X".split()

CONTENT="ADJ NOUN PROPN VERB CONTENT".split(" ")
FUNCTION="ADP AUX CONJ DET NUM PART PRON SCONJ PUNCT SYM X ADV FUNCTION".split(" ")

RIGHTATTACHING = []
LEFTATTACHING = []

scorerdict = defaultdict(list)



def map_to_two_tags(s,functionlist):
    for n in list(s.nodes()):
        if s.nodes[n]['form'].lower() in functionlist:
            s.nodes[n]['cpostag'] = 'FUNCTION'
        else:
            s.nodes[n]['cpostag'] = 'CONTENT'
    return s

def get_head_direction(sentences):
    D = Counter()
    for s in sentences:
        for h,d in s.edges():
            if h != 0 and h > d:
                D[s.nodes[d]['cpostag']+"_right"]+=1
            else:
                D[s.nodes[d]['cpostag']+"_left"]+=1
    for k in sorted(D.keys()):
        print(k,D[k])

def fill_out_left_and_right_attach(bigramcounter):
    LEFTATTACHING.append("CONJ")
    LEFTATTACHING.append("PUNCT")
    LEFTATTACHING.append("PROPN")


    RIGHTATTACHING.append("AUX")
    RIGHTATTACHING.append("DET")
    RIGHTATTACHING.append("SCONJ")


    if  bigramcounter[("ADP","DET")] + bigramcounter[("ADP","NOUN")] +  bigramcounter[("ADP","PROPN")] + bigramcounter[("ADP","PRON")] >  bigramcounter[("DET","ADP")] + bigramcounter[("NOUN","ADP")] +  bigramcounter[("PROPN","ADP")] +  bigramcounter[("PRON","ADP")]:
        RIGHTATTACHING.append("ADP")
    else:
        LEFTATTACHING.append("ADP")




def get_scores(predset,goldset):
    tp = len(predset.intersection(goldset))
    fp = len(predset.difference(goldset))
    fn = len(goldset.difference(predset))
    try:
        precision = tp / (fp + tp)
    except:
        precision = 0
    try:
        recall = tp / (fn + tp)
    except:
        recall = 0
    return (precision,recall)


def count_pos_bigrams(treebank):
    C = Counter()
    W = Counter()
    for s in treebank:
        for n,n_next in zip(list(s.nodes())[1:],list(s.nodes())[2:]):
            pos_n = s.nodes[n]['cpostag']
            pos_n_next = s.nodes[n_next]['cpostag']
            C[(pos_n,pos_n_next)]+=1
        for n in list(s.nodes())[1:]:
            word_n = s.nodes[n]['form'].lower()
            W[word_n]+=1

    return C,W


def add_high_confidence_edges(s,bigramcount,backoff):
    pos_index_dict = defaultdict(list)
    T = set()
    D = set()
    goldedgeset=set(s.edges())
    global scorerdict
    verbroot = None
    adjroot = None

    possibleheads = [x for x in list(s.nodes()) if s.nodes[x]['cpostag'] in OPEN]
    if len(possibleheads) == 1:
        T.add((0,possibleheads[0]))
        for d in list(s.nodes()):
            if d != 0 and d!= possibleheads[0]:
                T.add((possibleheads[0],d))
        scorerdict["__shortsentence"].append(get_scores(T,goldedgeset))
        D.update(T)
        T = set()
    else:
        for n in list(s.nodes()):
            pos_index_dict[s.nodes[n]['cpostag']].append(n)


        for n in pos_index_dict["DET"]:
            #if bigramcount[("DET","NOUN")] > bigramcount[("NOUN","DET")]:
            #    noundist=[abs(n-x) for x in pos_index_dict["NOUN"] if x > n ]
            #else:
            #    noundist=[abs(n-x) for x in pos_index_dict["NOUN"] if x < n ]
            noundist=[abs(n-x) for x in pos_index_dict["NOUN"]]
            if noundist:
                closestnoun=pos_index_dict["NOUN"][np.argmin(noundist)]
                T.add((closestnoun,n))
                localgoldedgeset = set([(h,d) for h,d in goldedgeset if d in pos_index_dict["DET"]])
                scorerdict["DET"].append(get_scores(T,localgoldedgeset))
                D.update(T)
                T = set()

        for n in pos_index_dict["NUM"]:
            #if bigramcount[("DET","NOUN")] > bigramcount[("NOUN","DET")]:
            #    noundist=[abs(n-x) for x in pos_index_dict["NOUN"] if x > n ]
            #else:
            #    noundist=[abs(n-x) for x in pos_index_dict["NOUN"] if x < n ]
            noundist=[abs(n-x) for x in pos_index_dict["NOUN"]]
            if noundist:
                closestnoun=pos_index_dict["NOUN"][np.argmin(noundist)]
                T.add((closestnoun,n))
                localgoldedgeset = set([(h,d) for h,d in goldedgeset if d in pos_index_dict["DET"]])
                scorerdict["NUM"].append(get_scores(T,localgoldedgeset))
                D.update(T)
                T = set()



        for n in pos_index_dict["ADP"]:
            # if bigramcount[("ADP","NOUN")] > bigramcount[("NOUN","ADP")]:
            #     noundist=[abs(n-x) for x in pos_index_dict["NOUN"] if x > n ]
            # else:
            #     noundist=[abs(n-x) for x in pos_index_dict["NOUN"] if x < n ]
            noundist=[abs(n-x) for x in pos_index_dict["NOUN"] ]
            if noundist:
                closestnoun=pos_index_dict["NOUN"][np.argmin(noundist)]
                T.add((closestnoun,n))
                scorerdict["ADP"].append(get_scores(T,goldedgeset))
                D.update(T)
                T = set()


        for n in pos_index_dict["ADJ"]:
            # if bigramcount[("adj","noun")] > bigramcount[("noun","adj")]:
            #     noundist=[abs(n-x) for x in pos_index_dict["noun"] if x > n ]
            # else:
            #     noundist=[abs(n-x) for x in pos_index_dict["noun"] if x < n ]
            noundist=[abs(n-x) for x in pos_index_dict["NOUN"] ]
            if noundist:
                closestnoun=pos_index_dict["NOUN"][np.argmin(noundist)]
                T.add((closestnoun,n))
                scorerdict["ADJ_nounhead"].append(get_scores(T,goldedgeset))
                D.update(T)
                T = set()


        for n in pos_index_dict["AUX"]:
            # if bigramcount[("AUX","VERB")] > bigramcount[("VERB","AUX")]:
            #     noundist=[abs(n-x) for x in pos_index_dict["VERB"] if x > n ]
            # else:
            #     noundist=[abs(n-x) for x in pos_index_dict["VERB"] if x < n ]
            noundist=[abs(n-x) for x in pos_index_dict["VERB"] ]
            if noundist:
                closestnoun=pos_index_dict["VERB"][np.argmin(noundist)]
                T.add((closestnoun,n))
                scorerdict["AUX"].append(get_scores(T,goldedgeset))
                D.update(T)
                T = set()


        for n in pos_index_dict["NOUN"]:
            # if bigramcount[("AUX","VERB")] > bigramcount[("VERB","AUX")]:
            #     noundist=[abs(n-x) for x in pos_index_dict["VERB"] if x > n ]
            # else:
            #     noundist=[abs(n-x) for x in pos_index_dict["VERB"] if x < n ]
            noundist=[abs(n-x) for x in pos_index_dict["VERB"] ]
            if noundist:
                closestnoun=pos_index_dict["VERB"][np.argmin(noundist)]
                T.add((closestnoun,n))
                scorerdict["NOUN"].append(get_scores(T,goldedgeset))
                D.update(T)
                T = set()


        for n in pos_index_dict["PRON"]:
            noundist=[abs(n-x) for x in pos_index_dict["VERB"]]
            if noundist:
                closestnoun=pos_index_dict["VERB"][np.argmin(noundist)]
                T.add((closestnoun,n))
                scorerdict["PRON"].append(get_scores(T,goldedgeset))
                D.update(T)
                T = set()


        for n in pos_index_dict["ADV"]:
            noundist=[abs(n-x) for x in pos_index_dict["VERB"]+pos_index_dict["ADJ"]]
            if noundist:
                closestnoun=(pos_index_dict["VERB"]+pos_index_dict["ADJ"])[np.argmin(noundist)]
                T.add((closestnoun,n))
                scorerdict["ADV"].append(get_scores(T,goldedgeset))
                D.update(T)
                T = set()


        if pos_index_dict["VERB"]:
            verbroot = min(pos_index_dict["VERB"])
            T.add((0,verbroot))
            scorerdict["VERB_root"].append(get_scores(T,goldedgeset))
            D.update(T)
            T = set()
            for n in pos_index_dict["VERB"]:
                noundist=[abs(n-x) for x in pos_index_dict["VERB"] if x != n and n != verbroot]
                if noundist:
                    closestnoun=pos_index_dict["VERB"][np.argmin(noundist)]
                    T.add((closestnoun,n))
                    scorerdict["VERB_head"].append(get_scores(T,goldedgeset))
                    D.update(T)
                    T = set()

            for n in pos_index_dict["SCONJ"]:
                noundist=[abs(n-x) for x in pos_index_dict["VERB"]]
                if noundist:
                    closestnoun=pos_index_dict["VERB"][np.argmin(noundist)]
                    T.add((closestnoun,n))
                    scorerdict["SCONJ"].append(get_scores(T,goldedgeset))
                    D.update(T)
                    T = set()

        elif pos_index_dict["ADJ"] or pos_index_dict["NOUN"]: #or pos_index_dict["PROPN"]:
            adjroot = min(pos_index_dict["ADJ"]+pos_index_dict["NOUN"])#+pos_index_dict["PROPN"])
            T.add((0,adjroot))
            scorerdict["CONTENT_root"].append(get_scores(T,goldedgeset))
            D.update(T)
            T = set()

        if pos_index_dict["PROPN"]:
            li = sorted(pos_index_dict["PROPN"])
            operation = []
            for idx,v in enumerate(li):
                if idx == 0:
                    operation.append("head")
                elif v -1 == li[idx-1]:
                    operation.append("dep")
                else:
                    operation.append("head")
            for v, o in zip(li,operation):
                if o == 'head':
                    head = v
                else:
                    T.add((head,v))
                    scorerdict["PROPN_chain"].append(get_scores(T,goldedgeset))
                    D.update(T)
                    T = set()
        if s.nodes[max(list(s.nodes()))]['cpostag'] == 'PUNCT':
            if verbroot:
                T.add((verbroot,max(list(s.nodes()))))
            elif adjroot:
                T.add((adjroot,max(list(s.nodes()))))
            scorerdict["PUNCT"].append(get_scores(T,goldedgeset))
            T = set()

    scorerdict["__TOTAL"].append(get_scores(D,goldedgeset))
    ausgraph = nx.DiGraph()
    ausgraph.add_nodes_from(list(s.nodes()))
    ausgraph.add_edges_from(D)

    for n in list(s.nodes())[1:]:
        if not ausgraph.predecessors(n): # if n has no head
            ausgraph.add_edge(n,n)
    s.remove_edges_from(list(s.edges()))

    if len(list(ausgraph.successors(0))) > 0:
        print("LIST",list(ausgraph.successors(0)),len(list(ausgraph.successors(0))))
        mainpred = list(ausgraph.successors(0))[0]
    else:
        mainpred = 0

    for h,d in ausgraph.edges():
        label = "dep"
        if h == 0:
            label = "root"
        elif h == d:
            label = 'backoff'
            if backoff == 'cycle':
                h = d
            elif backoff == 'left':
                if d == 1:
                    h = mainpred
                else:
                    h = d -1
            elif backoff == 'right':
                if d == max(list(s.nodes())):
                    h = mainpred
                else:
                    h = d + 1
        #s.add_edge(h,d,{'deprel' : label})
        s.add_edge(h,d,deprel= label)


    return s





def add_all_edges(s):
    #connect each word wwith w+1 and w-1
    #this ensures connectedness
    for h in list(s.nodes()):
        for d in list(s.nodes()):
            if h != d:
                s.add_edge(h,d)
    return s

def manage_function_words(s):
    """such as reducing their predisposition to be heads"""
    for h in [x for x in list(s.nodes()) if s.nodes[x]['cpostag'] in OPEN]:
        for d in [x for x in s.nodes()[h-3:h+3] if s.nodes[x]['cpostag'] in CLOSED]:
            if h != d:
                s.add_edge(h,d)
    return s


def relate_content_words(s):
    for h in [x for x in list(s.nodes()) if s.nodes[x]['cpostag'] in OPEN]:
        for d in [x for x in list(s.nodes()) if s.nodes[x]['cpostag'] in OPEN and x !=h]:
             s.add_edge(h,d)
    return s



def attach_adjacent(s,direction):
    s.remove_edges_from(list(s.edges()))
    if direction == 'left':
        for n in s.nodes()[1:]:
            s.add_edge(n-1,n,{'deprel' : 'backoff'})
    else:
        s.add_edge(0,s.nodes()[-1],{'deprel' : 'backoff'})
        for n in s.nodes()[1:-1]:
            s.add_edge(n+1,n,{'deprel' : 'backoff'})
    return s



def add_all_edges(s):
    #connect each word wwith w+1 and w-1
    #this ensures connectedness
    for h in s.nodes():
        for d in s.nodes():
            if h != d:
                s.add_edge(h,d)
    return s


def add_short_edges(s):
    #connect each word wwith w+1 and w-1
    #this ensures connectedness
    for n in list(s.nodes()):
        if n+1 in list(s.nodes()):
            s.add_edge(n+1,n)
        if n-1 in list(s.nodes()):
            s.add_edge(n-1,n)
    return s

def add_head_rule_edges(s,headrules):
    for h in list(s.nodes()):
        for d in [x for x in s.nodes() if x!=h]:
            pos_h = s.nodes[h]['cpostag']
            pos_d = s.nodes[d]['cpostag']
            if not headrules[(headrules["head"]==pos_h) & (headrules["dep"]==pos_d)].empty:
                s.add_edge(h,d)
    return s


def morphological_inequality():
    #if two words have different prefixes or suffixes, we add an edge between them
    #How to relate this to UD morphofeats if available?
    return

def add_verb_edges(s):
    #all words are attached to all VERB-type words
    #we add all nouns to verbs i.e. NOUN and PROPN
    ALLVERBS = [n for n in list(s.nodes()) if s.nodes[n]['cpostag']=='VERB']
    ALLNOUNS = [n for n in list(s.nodes()) if s.nodes[n]['cpostag']=='NOUN' or s.nodes[n]['cpostag']=='PROPN' ]

    for n in s.nodes():
        for v in ALLVERBS:
            s.add_edge(v,n) # all words are dependent on verbs
            if n in ALLNOUNS: #nouns are 2x dependent on verbs
                s.add_edge(v,n)
    return s




def tree_decoding_algorithm_content_and_function(s,headrules,reverse=True):
    #This is the algorithm in Fig 3 in Søgaard(2012).

    personalization = dict([[x,1] for x in s.nodes() if s.nodes[x]['cpostag'] in CONTENT]+[[x,1] for x in s.nodes() if s.nodes[x]['cpostag'] not in CONTENT])

    ALLVERBS = sorted([n for n in list(s.nodes()) if s.nodes[n]['cpostag']=='VERB'])
    ALLCONTENT = sorted([n for n in list(s.nodes()) if s.nodes[n]['cpostag'] in CONTENT])

    if ALLVERBS:
        personalization[ALLVERBS[0]]=5
    elif ALLCONTENT:
        personalization[ALLCONTENT[0]]=5
    if reverse:
        rev_s = nx.reverse(nx.DiGraph(s))
    else:
        rev_s = nx.DiGraph(s)
    rankdict = nx.pagerank_numpy(rev_s,alpha=0.95,personalization=personalization)
    rankedindices=[k for k,v in Counter(rankdict).most_common()]
    pi = rankedindices
    H = set()
    D = set()

    contentindices = [x for x in rankedindices if s.nodes[x]['cpostag'] in CONTENT]
    functionindices =  [x for x in rankedindices if x not in contentindices]
    for i in contentindices: #We attach elements from highest to lowest, i.e. the word with the highest PR will be the dependent of root
        if len(H) == 0:
            n_j_prime = 0
        else:
            n_j_prime_index_headrules = None
            POS_i = s.nodes[i]['cpostag']
            possible_headsin_table = list(headrules[headrules['dep']==POS_i]['head'].values)
            H_headrules = [h for h in H if s.nodes[h]['cpostag'] in possible_headsin_table]

            if H_headrules:
                n_j_prime_index_headrules = np.argmin([abs(i - j) for j in sorted(H_headrules)]) #find the head of i
                n_j_prime=sorted(H_headrules)[n_j_prime_index_headrules]

            if not n_j_prime_index_headrules:
                n_j_prime_index = np.argmin([abs(i - j) for j in sorted(H)]) #find the head of i
                n_j_prime=sorted(H)[n_j_prime_index]
        D.add((n_j_prime,i))
        H.add(i)
        s.nodes[i]['feats']="rank:"+str(rankedindices.index(i))

    for i in functionindices: #We attach elements from highest to lowest, i.e. the word with the highest PR will be the dependent of root
        if len(H) == 0:
            n_j_prime = 0
        else:
            n_j_prime_index_headrules = None
            POS_i = s.nodes[i]['cpostag']

            possible_headsin_table = list(headrules[headrules['dep']==POS_i]['head'].values)

            if POS_i in RIGHTATTACHING:# ["ADP","DET","AUX","SCONJ"]:
                H_headrules = [h for h in H if s.nodes[h]['cpostag'] in possible_headsin_table and h > i]
            elif POS_i in LEFTATTACHING:
                H_headrules = [h for h in H if s.nodes[h]['cpostag'] in possible_headsin_table and h < i]
            else:
                H_headrules = [h for h in H if s.nodes[h]['cpostag'] in possible_headsin_table]

            if H_headrules:
                n_j_prime_index_headrules = np.argmin([abs(i - j) for j in sorted(H_headrules)]) #find the head of i
                n_j_prime=sorted(H_headrules)[n_j_prime_index_headrules]
            else:
            #if not n_j_prime_index_headrules:
                n_j_prime_index = np.argmin([abs(i - j) for j in sorted(H)]) #find the head of i
                n_j_prime=sorted(H)[n_j_prime_index]
        D.add((n_j_prime,i))
        s.nodes[i]['feats']="rank:"+str(rankedindices.index(i))

    s.add_node(0,attr_dict={'form' :'ROOT', 'lemma' :'ROOT', 'cpostag' :'ROOT', 'postag' : 'ROOT'})
    s.remove_edges_from(list(s.edges()))
    s.add_edges_from(D)


    #Make sure there are no full 0-attached sentences sentences

    mainpred = sorted(s.successors(0))[0]
    if len(list(s.successors(0))) > 1:
        for other in sorted(s.successors(0))[1:]:
            s.remove_edge(0,other)
            s.add_edge(mainpred,other)

    if s.nodes[max(list(s.nodes()))]['cpostag'] == 'PUNCT':
        lastperiod = max(list(s.nodes()))
        s.remove_edge(s.head_of(lastperiod),lastperiod)
        s.add_edge(mainpred,lastperiod)

    if s.nodes[1]['cpostag'] == 'PUNCT':
        s.remove_edge(s.head_of(1),1)
        s.add_edge(mainpred,1)


    for h,d in s.edges():
        s[h][d]['deprel'] = 'root' #if h == 0 else 'dep'
    return s




def tree_decoding_algorithm(s,headrules):
    #This is the algorithm in Fig 3 in Søgaard(2012).
    #TODO reconsider root-attachment after first iteration, it is non-UD

    personalization = dict([[x,1] for x in list(s.nodes()) if s.nodes[x]['cpostag'] in OPEN]+[[x,1] for x in s.nodes() if s.nodes[x]['cpostag'] not in OPEN])

    rankdict = nx.pagerank_numpy(s,alpha=0.95,personalization=personalization)
    rankedindices=[k for k,v in Counter(rankdict).most_common()]
    pi = rankedindices
    H = set()
    D = set()
    for i in rankedindices: #We attach elements from highest to lowest, i.e. the word with the highest PR will be the dependent of root
        if len(H) == 0:
            n_j_prime = 0
        else:
            n_j_prime_index_headrules = None
            if not headrules.empty:
                POS_i = s.nodes[i]['cpostag']
                possible_headsin_table = list(headrules[headrules['dep']==POS_i]['head'].values)
                H_headrules = [h for h in H if s.nodes[h]['cpostag'] in possible_headsin_table]
                if H_headrules:
                    n_j_prime_index_headrules = np.argmin([abs(i - j) for j in sorted(H_headrules)]) #find the head of i
                    n_j_prime=sorted(H_headrules)[n_j_prime_index_headrules]

                if not n_j_prime_index_headrules:
                    n_j_prime_index = np.argmin([abs(i - j) for j in sorted(H)]) #find the head of i
                    n_j_prime=sorted(H)[n_j_prime_index]
        D.add((n_j_prime,i))
        onlycontentheads = True
        if onlycontentheads and s.nodes[i]['cpostag'] in OPEN: #we only allow content words to be heads
            H.add(i)
        s.nodes[i]['lemma']=str(rankedindices.index(i))
    s.add_node(0,attr_dict={'form' :'ROOT', 'lemma' :'ROOT', 'cpostag' :'ROOT', 'postag' : 'ROOT'})
    s.remove_edges_from(list(s.edges()))
    s.add_edges_from(D)

    for h,d in s.edges():
        s[h][d]['deprel'] = 'root' if h == 0 else 'dep'
    return s

def main():
    parser = argparse.ArgumentParser(description="""Convert conllu to conll format""")
    parser.add_argument('--input', help="conllu file", default='../data/en-ud-dev.conllu')
    parser.add_argument('--lang', default="")
    parser.add_argument('--posrules', help="head POS rules file", default='../data/posrules.tsv')
    parser.add_argument('--output', help="target file",default="testout.conllu")
    parser.add_argument('--parsing_strategy', choices=['rules','pagerank','adjacent'],default='pagerank')
    parser.add_argument('--steps', choices=['twotags','complete','neighbors','verbs','function','content','headrule'], nargs='+', default=[""])
    parser.add_argument('--reverse', action='store_true',default=True)
    parser.add_argument('--rule_backoff', choices=['cycle','left','right'],default="left")
    parser.add_argument('--format', choices=['conll2006','conllu'],default="conllu")

    args = parser.parse_args()

    if sys.version_info < (3,0):
        print("Sorry, requires Python 3.x.") #suggestion: install anaconda python
        sys.exit(1)

    headrules = pd.read_csv(args.posrules,'\t')
    cio = CoNLLReader(args.format)
    orig_treebank = cio.read_conll(args.input)
    ref_treebank = cio.read_conll(args.input)
    modif_treebank = []
    posbigramcounter,wordcounter = count_pos_bigrams(orig_treebank)
    functionlist = [x for x,y in wordcounter.most_common(100)]
    print(functionlist)
    print("treebank size",len(orig_treebank))
    fill_out_left_and_right_attach(posbigramcounter)
    if args.parsing_strategy == 'pagerank':
        for o,ref in zip(orig_treebank,ref_treebank):
            s = copy.copy(o)

            s.remove_edges_from(list(s.edges()))
            s.remove_node(0) # From here and until tree reconstruction there is no symbolic root node, makes our life a bit easier

            if "twotags" in args.steps:
                s = map_to_two_tags(s,functionlist)
            if "complete" in args.steps:
                s = add_all_edges(s)
            if "neighbors" in args.steps:
                s = add_short_edges(s)
            if "verbs" in args.steps:
                s = add_verb_edges(s)
            if "function" in args.steps:
                s = manage_function_words(s)
            if "content" in args.steps:
                s = relate_content_words(s)
            if "headrule" in args.steps:
                s = add_head_rule_edges(s,headrules)

            tree_decoding_algorithm_content_and_function(s,headrules,args.reverse)

            modif_treebank.append(s)
            if args.reverse:
                r = ".rev"
            else:
                r = ".norev"
        outfile = Path(args.lang+"_"+args.output +"_"+ "_".join(args.steps)+r+".conllu")
    elif args.parsing_strategy == 'adjacent':
        for s in orig_treebank:
            s.remove_edges_from(s.edges())
            s = attach_adjacent(s,args.rule_backoff)
            modif_treebank.append(s)
            outfile = Path(args.output +"."+args.rule_backoff)

    else:
        for s in orig_treebank:
            s = add_high_confidence_edges(s,posbigramcounter,args.rule_backoff)
            modif_treebank.append(s)

        for k in sorted(scorerdict.keys()):
            prec = sum([p for p,r in scorerdict[k]]) / len(scorerdict[k])
            reca = sum([r for p,r in scorerdict[k]]) / len(scorerdict[k])
            print('{0}, {1:.2f}, {2:.2f}'.format(k, prec, reca))
            outfile = Path(args.output +".rules")
    cio.write_conll(modif_treebank,outfile,conllformat='conllu', print_fused_forms=False,print_comments=False)

if __name__ == "__main__":
    main()
