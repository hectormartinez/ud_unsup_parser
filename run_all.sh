
#Best system so far is only headrules

for s in 'headrule' #'verbs neighbors function headrule' 'verbs neighbors' 'verbs function' 'neighbors' 'verbs' 'function' 'content'
do
    cd src
    python udup.py --steps $s --input ../data/en-ud-dov.conllu --output devdovdev.conllu
    cd ..
    perl eval07.pl -g data/en-ud-dov.conllu -s src/devdovdev.conllu > "$s.pers.reverse.eval"
done

