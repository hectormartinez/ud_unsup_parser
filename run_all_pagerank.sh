
#Best system so far is only headrules

for s in 'headrule' #'verbs neighbors function headrule' 'verbs neighbors' 'verbs function' 'neighbors' 'verbs' 'function' 'content'
do
    cd src
    python udup.py --steps $s
    cd ..
    perl eval.pl -g data/en-ud-dev.conllu -s src/testout.conllu > "$s.pers.reverse.eval"
done
