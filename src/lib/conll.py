import networkx as nx
from collections import Counter
import re


#TODO make these parse functions static methods of ConllReder
def parse_id(id_str):
    if id_str == '_':
        return None
    ids = tuple(map(int, id_str.split("-")))
    if len(ids) == 1:
        return ids[0]
    else:
        return ids

def parse_feats(feats_str):
    if feats_str == '_':
        return {}
    feat_pairs = [pair.split("=") for pair in feats_str.split("|")]
    return {k: v for k, v in feat_pairs}

def parse_deps(dep_str):
    if dep_str == '_':
        return []
    dep_pairs = [pair.split(":") for pair in dep_str.split("|")]
    return [(int(pair[0]), pair[1]) for pair in dep_pairs]




class DependencyTree(nx.DiGraph):
    """
    A DependencyTree as networkx graph:
    nodes store information about tokens
    edges store edge related info, e.g. dependency relations
    """

    def __init__(self):
        nx.DiGraph.__init__(self)

    def pathtoroot(self, child):
        path = []
        newhead = self.head_of(self, child)
        while newhead:
            path.append(newhead)
            newhead = self.head_of(self, newhead)
        return path

    def head_of(self, n):
        for u, v in self.edges():
            if v == n:
                return u
        return None


    def sentence_plus_word(self,n, attr_dict={},head=None,edge_attribs={}):
        #n is the insertion point right before the new word
        #the new node can either be disconnected if head==None, or a leaf, if head is specified
        "the sequence of nodes mmmmnppp becomes mmmnOppp"
        newsent = DependencyTree()
        newsent.add_node(0,attr_dict={'form' :'ROOT', 'lemma' :'ROOT', 'cpostag' :'ROOT', 'postag' : 'ROOT'})
        for k in self.graph.keys():
            newsent.graph[k]=self.graph[k]


        #the starting nodes mmm and insertion point n
        for j in self.nodes()[1:n+1]:
            newsent.add_node(j,attr_dict=self.node[j])

            original_head = self.head_of(j)
            adjusted_head = self.head_of(j)
            if adjusted_head > n: #TODO There might a boundary case if the original head is *the* insertion point
                adjusted_head +=1
            newsent.add_edge(adjusted_head,j,attr_dict=self[original_head][j])

        #the new O node,
        newsent.add_node(n+1,attr_dict=attr_dict)
        if head:
            if head > n:
                adjusted_head = head + 1
            else:
                adjusted_head = head
            newsent.add_edge(adjusted_head,n+1,attr_dict=edge_attribs)

        #the trailing pppp nodes
        for j in self.nodes()[n+1:]:
            adjusted_node = j + 1
            original_head = self.head_of(j)

            if original_head > n:
                adjusted_head = original_head + 1
            else:
                adjusted_head = original_head

            newsent.add_node(adjusted_node,attr_dict=self.node[j])
            newsent.add_edge(adjusted_head,adjusted_node,attr_dict=self[original_head][j])

        return newsent


    def sentence_minus_word(self,n,propagate_edges=False): #notice we are not using remove_node because we need to recalculate node indices and so on
        # deleting a word implies
        # a word is not a node, i.e. its index is >0
        # A - if propagate_edges is True, then all the dependents of i must become dependents of the head of i
        # B- removing the graph node i that contains the word
        # C- changing the index of all nodes j > i to j+=j-1

        if n == 0:
            return self

        newsent = DependencyTree()
        for k in self.graph.keys():
            newsent.graph[k]=self.graph[k]

        head_of_deleted_word = self.head_of(n)

        # A - if propagate_edges is True, then all the dependents of i must become dependents of the head of i
        if propagate_edges:
            for d in self.successors(n):
                deprel = self[n][d]
                self.remove_edge(n,d)
                self.add_edge(head_of_deleted_word,d,attr_dict={'deprel' : deprel })

        # C- readjusting indices into a new blank sentence
        newsent.add_node(0,attr_dict={'form' :'ROOT', 'lemma' :'ROOT', 'cpostag' :'ROOT', 'postag' : 'ROOT'})
        for j in self.nodes()[1:]:
            if j == n:
                continue
            head_of_j = self.head_of(j)
            if j > n:
                adjusted_node = j - 1
            else:
                adjusted_node = j

            if head_of_j > n:
                adjusted_head = head_of_j -1
            else:
                adjusted_head = head_of_j

            newsent.add_node(adjusted_node,attr_dict=self.node[j])
            newsent.add_edge(adjusted_head,adjusted_node,attr_dict=self[head_of_j][j])

        return newsent


    def get_sentence_as_string(self,printid=False):
        out = []
        for token_i in range(1, max(self.nodes()) + 1):
            if printid:
                out.append(str(token_i)+":"+self.node[token_i]['form'])
            else:
                out.append(self.node[token_i]['form'])
        return u" ".join(out)

    def subsumes(self, head, child):
        if head in self.pathtoroot(self, child):
            return True

    def remove_arabic_diacritics(self):
        # The following code is based on nltk.stem.isri
        # It is equivalent to an interative application of isri.norm(word,num=1)
        # i.e. we do not remove any hamza characters

        re_short_vowels = re.compile(r'[\u064B-\u0652]')
        for n in self.nodes():
            self.node[n]["form"] = re_short_vowels.sub('', self.node[n]["form"])

    def get_highest_index_of_span(self, span):  # retrieves the node index that is closest to root
        #TODO: CANDIDATE FOR DEPRECATION
        distancestoroot = [len(self.pathtoroot(self, x)) for x in span]
        shortestdistancetoroot = min(distancestoroot)
        spanhead = span[distancestoroot.index(shortestdistancetoroot)]
        return spanhead

    def get_deepest_index_of_span(self, span):  # retrieves the node index that is farthest from root
        #TODO: CANDIDATE FOR DEPRECATION
        distancestoroot = [len(self.pathtoroot(self, x)) for x in span]
        longestdistancetoroot = max(distancestoroot)
        lownode = span[distancestoroot.index(longestdistancetoroot)]
        return lownode

    def span_makes_subtree(self, initidx, endidx):
        G = nx.DiGraph()
        span_nodes = list(range(initidx,endidx+1))
        span_words = [self.node[x]["form"] for x in span_nodes]
        G.add_nodes_from(span_nodes)
        for h,d in self.edges():
            if h in span_nodes and d in span_nodes:
                G.add_edge(h,d)
        return nx.is_tree(G)

    def _choose_spanhead_from_heuristics(self,span_nodes,pos_precedence_list):
        distancestoroot = [len(nx.ancestors(self,x)) for x in span_nodes]
        shortestdistancetoroot = min(distancestoroot)
        distance_counter = Counter(distancestoroot)

        highest_nodes_in_span = []
        # Heuristic Nr 1: If there is one single highest node in the span, it becomes the head
        # N.B. no need for the subspan to be a tree if there is one single highest element
        if distance_counter[shortestdistancetoroot] == 1:
            spanhead = span_nodes[distancestoroot.index(shortestdistancetoroot)]
            return spanhead

        # Heuristic Nr 2: Choose by POS ranking the best head out of the highest nodes
        for x in span_nodes:
            if len(nx.ancestors(self,x)) == shortestdistancetoroot:
                highest_nodes_in_span.append(x)

        best_rank = len(pos_precedence_list) + 1
        candidate_head = - 1
        span_upos  = [self.node[x]["cpostag"]for x in highest_nodes_in_span]
        for upos, idx in zip(span_upos,highest_nodes_in_span):
            if pos_precedence_list.index(upos) < best_rank:
                best_rank = pos_precedence_list.index(upos)
                candidate_head = idx
        return candidate_head

    def _remove_node_properties(self,fields):
        for n in sorted(self.nodes()):
            for fieldname in self.node[n].keys():
                if fieldname in fields:
                    self.node[n][fieldname]="_"

    def _remove_deprel_suffixes(self):
        for h,d in self.edges():
            if ":" in self[h][d]["deprel"]:
                self[h][d]["deprel"]=self[h][d]["deprel"].split(":")[0]

    def _keep_fused_form(self,posPreferenceDicts):
        # For a span A,B  and external tokens C, such as  A > B > C, we have to
        # Make A the head of the span
        # Attach C-level tokens to A
        #Remove B-level tokens, which are the subtokens of the fused form della: de la

        if self.graph["multi_tokens"] == {}:
            return

        spanheads = []
        spanhead_fused_token_dict = {}
        # This double iteration is overkill, one could skip the spanhead identification
        # but in this way we avoid modifying the tree as we read it
        for fusedform_idx in sorted(self.graph["multi_tokens"]):
            fusedform_start, fusedform_end = self.graph["multi_tokens"][fusedform_idx]["id"]
            fuseform_span = list(range(fusedform_start,fusedform_end+1))
            spanhead = self._choose_spanhead_from_heuristics(fuseform_span,posPreferenceDicts)
            #if not spanhead:
            #    spanhead = self._choose_spanhead_from_heuristics(fuseform_span,posPreferenceDicts)
            spanheads.append(spanhead)
            spanhead_fused_token_dict[spanhead] = fusedform_idx

        bottom_up_order = [x for x in nx.topological_sort(self) if x in spanheads]
        for spanhead in bottom_up_order:
            fusedform_idx = spanhead_fused_token_dict[spanhead]
            fusedform = self.graph["multi_tokens"][fusedform_idx]["form"]
            fusedform_start, fusedform_end = self.graph["multi_tokens"][fusedform_idx]["id"]
            fuseform_span = list(range(fusedform_start,fusedform_end+1))

            if spanhead:
                #Step 1: Replace form of head span (A)  with fusedtoken form  -- in this way we keep the lemma and features if any
                self.node[spanhead]["form"] = fusedform
                # 2-  Reattach C-level (external dependents) to A
                #print(fuseform_span,spanhead)

                internal_dependents = set(fuseform_span) - set([spanhead])
                external_dependents = [nx.bfs_successors(self,x) for x in internal_dependents]
                for depdict in external_dependents:
                    for localhead in depdict:
                        for ext_dep in depdict[localhead]:
                            deprel = self[localhead][ext_dep]["deprel"]
                            self.remove_edge(localhead,ext_dep)
                            self.add_edge(spanhead,ext_dep,deprel=deprel)

                #3- Remove B-level tokens
                for int_dep in internal_dependents:
                    self.remove_edge(self.head_of(int_dep),int_dep)
                    self.remove_node(int_dep)

        #4 reconstruct tree at the very end
        new_index_dict = {}
        for new_node_index, old_node_idex in enumerate(sorted(self.nodes())):
            new_index_dict[old_node_idex] = new_node_index

        T = DependencyTree() # Transfer DiGraph, to replace self

        for n in sorted(self.nodes()):
            T.add_node(new_index_dict[n],self.node[n])

        for h, d in self.edges():
            T.add_edge(new_index_dict[h],new_index_dict[d],deprel=self[h][d]["deprel"])
        #4A Quick removal of edges and nodes
        self.__init__()

        #4B Rewriting the Deptree in Self
        # TODO There must a more elegant way to rewrite self -- self= T for instance?
        for n in sorted(T.nodes()):
            self.add_node(n,T.node[n])

        for h,d in T.edges():
            self.add_edge(h,d,T[h][d])

        # 5. remove all fused forms form the multi_tokens field
        self.graph["multi_tokens"] = {}

        if not nx.is_tree(self):
            print("Not a tree after fused-form heuristics:",self.get_sentence_as_string())

    def filter_sentence_content(self,replace_subtokens_with_fused_forms=False, lang=None, posPreferenceDict=None,node_properties_to_remove=None,remove_deprel_suffixes=False,remove_arabic_diacritics=False):
        if replace_subtokens_with_fused_forms:
            self._keep_fused_form(posPreferenceDict)
        if remove_deprel_suffixes:
            self._remove_deprel_suffixes()
        if node_properties_to_remove:
            self._remove_node_properties(node_properties_to_remove)
        if remove_arabic_diacritics:
            self.remove_arabic_diacritics()



class CoNLLReader(object):
    """
    conll input/output
    """

    "" "Static properties"""
    CONLL06_COLUMNS = [('id',int), ('form',str), ('lemma',str), ('cpostag',str), ('postag',str), ('feats',str), ('head',int), ('deprel',str), ('phead', str), ('pdeprel',str)]
    #CONLL06_COLUMNS = ['id', 'form', 'lemma', 'cpostag', 'postag', 'feats', 'head', 'deprel', 'phead', 'pdeprel']
    CONLL06DENSE_COLUMNS = [('id',int), ('form',str), ('lemma',str), ('cpostag',str), ('postag',str), ('feats',str), ('head',int), ('deprel',str), ('edgew',str)]
    CONLL_U_COLUMNS = [('id', parse_id), ('form', str), ('lemma', str), ('cpostag', str),
                   ('postag', str), ('feats', str), ('head', parse_id), ('deprel', str),
                   ('deps', parse_deps), ('misc', str)]
    #CONLL09_COLUMNS =  ['id','form','lemma','plemma','cpostag','pcpostag','feats','pfeats','head','phead','deprel','pdeprel']



    def __init__(self):
        pass

    def read_conll_2006(self, filename):
        sentences = []
        sent = DependencyTree()
        for line_num, conll_line in enumerate(open(filename)):
            parts = conll_line.strip().split("\t")
            if len(parts) in (8, 10):
                token_dict = {key: conv_fn(val) for (key, conv_fn), val in zip(self.CONLL06_COLUMNS, parts)}

                sent.add_node(token_dict['id'], token_dict)
                sent.add_edge(token_dict['head'], token_dict['id'], deprel=token_dict['deprel'])
            elif len(parts) == 0  or (len(parts)==1 and parts[0]==""):
                sentences.append(sent)
                sent = DependencyTree()
            else:
                raise Exception("Invalid input format in line nr: ", line_num, conll_line, filename)
     
        return sentences

    def read_conll_2006_dense(self, filename):
        sentences = []
        sent = DependencyTree()
        for conll_line in open(filename):
            parts = conll_line.strip().split("\t")
            if len(parts) == 9:
                token_dict = {key: conv_fn(val) for (key, conv_fn), val in zip(self.CONLL06DENSE_COLUMNS, parts)}

                sent.add_node(token_dict['id'], token_dict)
                sent.add_edge(token_dict['head'], token_dict['id'], deprel=token_dict['deprel'])
            elif len(parts) == 0 or (len(parts)==1 and parts[0]==""):
                sentences.append(sent)
                sent = DependencyTree()
            else:
                raise Exception("Invalid input format in line: ", conll_line, filename)

        return sentences



    def write_conll(self, list_of_graphs, conll_path,conllformat='conllu', print_fused_forms=False,print_comments=False):
        # TODO add comment writing
        if conllformat == "conllu":
            columns = [colname for colname, fname in self.CONLL_U_COLUMNS]
        else:
            columns = [colname for colname, fname in self.CONLL06_COLUMNS]

        with conll_path.open('w') as out:
            for sent_i, sent in enumerate(list_of_graphs):
                if sent_i > 0:
                    print("", file=out)
                if print_comments:
                    for c in sent.graph["comment"]:
                        print(c, file=out)
                for token_i in range(1, max(sent.nodes()) + 1):
                    token_dict = dict(sent.node[token_i])
                    head_i = sent.head_of(token_i)
                    token_dict['head'] = head_i
                    # print(head_i, token_i)
                    try:
                        token_dict['deprel'] = sent[head_i][token_i]['deprel']
                        token_dict['id'] = token_i
                    except:
                        print("error at",head_i,token_i,token_dict)
                    row = [str(token_dict.get(col, '_')) for col in columns]
                    if print_fused_forms and token_i in sent.graph["multi_tokens"]:
                       currentmulti = sent.graph["multi_tokens"][token_i]
                       currentmulti["id"]=str(currentmulti["id"][0])+"-"+str(currentmulti["id"][1])
                       currentmulti["feats"]="_"
                       currentmulti["head"]="_"
                       rowmulti = [str(currentmulti.get(col, '_')) for col in columns]
                       print(u"\t".join(rowmulti),file=out)
                    print(u"\t".join(row), file=out)
            print(u"\t".join(row),file=out)
            # emtpy line afterwards
            print(u"", file=out)


    def read_conll_u(self,filename,keepFusedForm=False, lang=None, posPreferenceDict=None):
        sentences = []
        sent = DependencyTree()
        multi_tokens = {}

        for line_no, line in enumerate(open(filename).readlines()):
            line = line.strip("\n")
            if not line:
                # Add extra properties to ROOT node if exists
                if 0 in sent:
                    for key in ('form', 'lemma', 'cpostag', 'postag'):
                        sent.node[0][key] = 'ROOT'

                # Handle multi-tokens
                sent.graph['multi_tokens'] = multi_tokens
                multi_tokens = {}
                sentences.append(sent)
                sent = DependencyTree()
            elif line.startswith("#"):
                if 'comment' not in sent.graph:
                    sent.graph['comment'] = [line]
                else:
                    sent.graph['comment'].append(line)
            else:
                parts = line.split("\t")
                if len(parts) != len(self.CONLL_U_COLUMNS):
                    error_msg = 'Invalid number of columns in line {} (found {}, expected {})'.format(line_no, len(parts), len(self.CONLL_U_COLUMNS))
                    raise Exception(error_msg)

                token_dict = {key: conv_fn(val) for (key, conv_fn), val in zip(self.CONLL_U_COLUMNS, parts)}
                if isinstance(token_dict['id'], int):
                    sent.add_edge(token_dict['head'], token_dict['id'], deprel=token_dict['deprel'])
                    sent.node[token_dict['id']].update({k: v for (k, v) in token_dict.items()
                                                        if k not in ('head', 'id', 'deprel', 'deps')})
                    for head, deprel in token_dict['deps']:
                        sent.add_edge(head, token_dict['id'], deprel=deprel, secondary=True)
                else:
                    #print(token_dict['id'])
                    first_token_id = int(token_dict['id'][0])
                    multi_tokens[first_token_id] = token_dict
        return sentences