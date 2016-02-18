#TODO Review Soegaard unsup parser
#TODO Review the UD specs
#TODO Which tokens are always leaves

from collections import defaultdict, Counter
from itertools import islice
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

#THE HEAD OF AN OPEN CLASS IS ONLY AN OPEN CLASS OR ROOT
#THE HEAD OF A CLOSED CLASS IS AN OPEN CLASS
#THE HEAD OF OTHER IS OPEN CLASS

scorerdict = defaultdict(list)

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
    for s in treebank:
        for n,n_next in zip(s.nodes()[1:],s.nodes()[2:]):
            pos_n = s.node[n]['cpostag']
            pos_n_next = s.node[n_next]['cpostag']
            C[(pos_n,pos_n_next)]+=1

    return C


def add_high_confidence_edges(s,bigramcount):
    pos_index_dict = defaultdict(list)
    T = set()
    D = set()
    goldedgeset=set(s.edges())
    global scorerdict

    possibleheads = [x for x in s.nodes() if s.node[x]['cpostag'] in OPEN]
    if len(possibleheads) == 1:
        T.add((0,possibleheads[0]))
        for d in s.nodes():
            if d != 0 and d!= possibleheads[0]:
                T.add((possibleheads[0],d))
        scorerdict["__shortsentence"].append(get_scores(T,goldedgeset))
        D.update(T)
        T = set()
        return D

    for n in s.nodes():
        pos_index_dict[s.node[n]['cpostag']].append(n)


    for n in pos_index_dict["DET"]:
        if bigramcount[("DET","NOUN")] > bigramcount[("NOUN","DET")]:
            noundist=[abs(n-x) for x in pos_index_dict["NOUN"] if x > n ]
        else:
            noundist=[abs(n-x) for x in pos_index_dict["NOUN"] if x < n ]
        noundist=[abs(n-x) for x in pos_index_dict["NOUN"]]
        if noundist:
            closestnoun=pos_index_dict["NOUN"][np.argmin(noundist)]
            T.add((closestnoun,n))
            localgoldedgeset = set([(h,d) for h,d in goldedgeset if d in pos_index_dict["DET"]])
            scorerdict["DET"].append(get_scores(T,localgoldedgeset))
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
        if bigramcount[("adj","noun")] > bigramcount[("noun","adj")]:
            noundist=[abs(n-x) for x in pos_index_dict["noun"] if x > n ]
        else:
            noundist=[abs(n-x) for x in pos_index_dict["noun"] if x < n ]
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

    elif pos_index_dict["ADJ"]:
        adjroot = min(pos_index_dict["ADJ"])
        T.add((0,adjroot))
        scorerdict["ADJ_root"].append(get_scores(T,goldedgeset))
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

    scorerdict["__TOTAL"].append(get_scores(D,goldedgeset))
    return D

    # attach all DET to the closest noun



def add_all_edges(s):
    #connect each word wwith w+1 and w-1
    #this ensures connectedness
    for h in s.nodes():
        for d in s.nodes():
            if h != d:
                s.add_edge(h,d)
    return s

def manage_function_words(s):
    """such as reducing their predisposition to be heads"""
    for h in [x for x in s.nodes() if s.node[x]['cpostag'] in OPEN]:
        for d in [x for x in s.nodes()[h-3:h+3] if s.node[x]['cpostag'] in CLOSED]:
            if h != d:
                s.add_edge(h,d)
    return s


def relate_content_words(s):
    for h in [x for x in s.nodes() if s.node[x]['cpostag'] in OPEN]:
        for d in [x for x in s.nodes() if s.node[x]['cpostag'] in OPEN and x !=h]:
             s.add_edge(h,d)
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
    for n in s.nodes():
        if n+1 in s.nodes():
            s.add_edge(n+1,n)
        if n-1 in s.nodes():
            s.add_edge(n-1,n)
    return s

def add_head_rule_edges(s,headrules):
    for h in s.nodes():
        for d in [x for x in s.nodes() if x!=h]:
            pos_h = s.node[h]['cpostag']
            pos_d = s.node[d]['cpostag']
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
    ALLVERBS = [n for n in s.nodes() if s.node[n]['cpostag']=='VERB']
    ALLNOUNS = [n for n in s.nodes() if s.node[n]['cpostag']=='NOUN' or s.node[n]['cpostag']=='PROPN' ]

    for n in s.nodes():
        for v in ALLVERBS:
            s.add_edge(v,n) # all words are dependent on verbs
            if n in ALLNOUNS: #nouns are 2x dependent on verbs
                s.add_edge(v,n)
    return s




def tree_decoding_algorithm_content_and_function(s,headrules,reverse):
    #This is the algorithm in Fig 3 in Søgaard(2012).

    personalization = dict([[x,5] for x in s.nodes() if s.node[x]['cpostag'] in OPEN]+[[x,1] for x in s.nodes() if s.node[x]['cpostag'] not in OPEN])

    if reverse:
        rev_s = nx.reverse(nx.DiGraph(s))
    else:
        rev_s = nx.DiGraph(s)
    rankdict = nx.pagerank_numpy(rev_s,alpha=0.95,personalization=personalization)
    rankedindices=[k for k,v in Counter(rankdict).most_common()]
    pi = rankedindices
    H = set()
    D = set()

    contentindices = [x for x in rankedindices if s.node[x]['cpostag'] in OPEN]
    functionindices =  [x for x in rankedindices if x not in contentindices]
    for i in contentindices: #We attach elements from highest to lowest, i.e. the word with the highest PR will be the dependent of root
        if len(H) == 0:
            n_j_prime = 0
        else:
            n_j_prime_index_headrules = None
            if not headrules.empty:
                POS_i = s.node[i]['cpostag']
                possible_headsin_table = list(headrules[headrules['dep']==POS_i]['head'].values)
                H_headrules = [h for h in H if s.node[h]['cpostag'] in possible_headsin_table]
                if H_headrules:
                    n_j_prime_index_headrules = np.argmin([abs(i - j) for j in sorted(H_headrules)]) #find the head of i
                    n_j_prime=sorted(H_headrules)[n_j_prime_index_headrules]

                if not n_j_prime_index_headrules:
                    n_j_prime_index = np.argmin([abs(i - j) for j in sorted(H)]) #find the head of i
                    n_j_prime=sorted(H)[n_j_prime_index]
        D.add((n_j_prime,i))
        H.add(i)
        s.node[i]['lemma']=str(rankedindices.index(i))
    for i in functionindices: #We attach elements from highest to lowest, i.e. the word with the highest PR will be the dependent of root
        if len(H) == 0:
            n_j_prime = 0
        else:
            n_j_prime_index_headrules = None
            if not headrules.empty:
                POS_i = s.node[i]['cpostag']
                possible_headsin_table = list(headrules[headrules['dep']==POS_i]['head'].values)
                H_headrules = [h for h in H if s.node[h]['cpostag'] in possible_headsin_table]
                if H_headrules:
                    n_j_prime_index_headrules = np.argmin([abs(i - j) for j in sorted(H_headrules)]) #find the head of i
                    n_j_prime=sorted(H_headrules)[n_j_prime_index_headrules]

                if not n_j_prime_index_headrules:
                    n_j_prime_index = np.argmin([abs(i - j) for j in sorted(H)]) #find the head of i
                    n_j_prime=sorted(H)[n_j_prime_index]
        D.add((n_j_prime,i))
        s.node[i]['lemma']=str(rankedindices.index(i))

    s.add_node(0,attr_dict={'form' :'ROOT', 'lemma' :'ROOT', 'cpostag' :'ROOT', 'postag' : 'ROOT'})
    s.remove_edges_from(s.edges())
    s.add_edges_from(D)
    for h,d in s.edges():
        s[h][d]['deprel'] = 'root' if h == 0 else 'dep'
    return s




def tree_decoding_algorithm(s,headrules):
    #This is the algorithm in Fig 3 in Søgaard(2012).
    #TODO reconsider root-attachment after first iteration, it is non-UD

    personalization = dict([[x,1] for x in s.nodes() if s.node[x]['cpostag'] in OPEN]+[[x,1] for x in s.nodes() if s.node[x]['cpostag'] not in OPEN])

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
                POS_i = s.node[i]['cpostag']
                possible_headsin_table = list(headrules[headrules['dep']==POS_i]['head'].values)
                H_headrules = [h for h in H if s.node[h]['cpostag'] in possible_headsin_table]
                if H_headrules:
                    n_j_prime_index_headrules = np.argmin([abs(i - j) for j in sorted(H_headrules)]) #find the head of i
                    n_j_prime=sorted(H_headrules)[n_j_prime_index_headrules]

                if not n_j_prime_index_headrules:
                    n_j_prime_index = np.argmin([abs(i - j) for j in sorted(H)]) #find the head of i
                    n_j_prime=sorted(H)[n_j_prime_index]
        D.add((n_j_prime,i))
        if onlycontentheads and s.node[i]['cpostag'] in OPEN: #we only allow content words to be heads
            H.add(i)
        s.node[i]['lemma']=str(rankedindices.index(i))
    s.add_node(0,attr_dict={'form' :'ROOT', 'lemma' :'ROOT', 'cpostag' :'ROOT', 'postag' : 'ROOT'})
    s.remove_edges_from(s.edges())
    s.add_edges_from(D)
    for h,d in s.edges():
        s[h][d]['deprel'] = 'root' if h == 0 else 'dep'
    return s

def main():
    parser = argparse.ArgumentParser(description="""Convert conllu to conll format""")
    parser.add_argument('--input', help="conllu file", default='../data/en-ud-dov.conllu')
    parser.add_argument('--posrules', help="head POS rules file", default='../data/posrules.tsv')
    parser.add_argument('--output', help="target file",default="testout.conllu")
    parser.add_argument('--parsing_strategy', choices=['rules','pagerank'],default='pagerank')
    parser.add_argument('--steps', choices=['complete','neighbors','verbs','function','content','headrule'], nargs='+', default=[""])
    parser.add_argument('--reverse', action='store_true',default=False)
    args = parser.parse_args()

    if sys.version_info < (3,0):
        print("Sorry, requires Python 3.x.") #suggestion: install anaconda python
        sys.exit(1)

    headrules = pd.read_csv(args.posrules,'\t')
    cio = CoNLLReader()
    orig_treebank = cio.read_conll_u(args.input)
    ref_treebank = cio.read_conll_u(args.input)
    modif_treebank = []
    if args.parsing_strategy == 'pagerank':
        for o,r in zip(orig_treebank,ref_treebank):
            s = copy.copy(o)
            s.remove_edges_from(s.edges())
            s.remove_node(0) # From here and until tree reconstruction there is no symbolic root node, makes our life a bit easier
            #if "complete" in args.steps:
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
            s = tree_decoding_algorithm_content_and_function(s,headrules,args.reverse)
            modif_treebank.append(s)
            if args.reverse:
                r = ".rev"
            else:
                r = ".norev"
            outfile = Path(args.output +"_"+ "_".join(args.steps)+r+".conllu")
            cio.write_conll(modif_treebank,outfile,conllformat='conllu', print_fused_forms=False,print_comments=False)
            outfile = Path(args.output)
            cio.write_conll(modif_treebank,outfile,conllformat='conllu', print_fused_forms=False,print_comments=False)

    else:
        posbigramcounter = count_pos_bigrams(orig_treebank)
        for s in orig_treebank:
            D = add_high_confidence_edges(s,posbigramcounter)
            modif_treebank.append(s)
        for k in sorted(scorerdict.keys()):
            prec = sum([p for p,r in scorerdict[k]]) / len(scorerdict[k])
            reca = sum([r for p,r in scorerdict[k]]) / len(scorerdict[k])
            print('{0}, {1:.2f}, {2:.2f}'.format(k, prec, reca))


    #cio.write_conll(modif_treebank,args.output,conllformat='conllu', print_fused_forms=False,print_comments=False)

if __name__ == "__main__":
    main()
