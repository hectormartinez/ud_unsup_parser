
for s in 'verbs neighbors function' 'verbs neighbors' 'verbs function' 'neighbors' 'verbs' 'function' 'content' 'headrule'
do
    cd src
    python udup.py --steps $s --reverse
    cd ..
    perl eval.pl -g data/en-ud-dov.conllu -s src/testout.conllu > "$s.pers.reverse.eval"
done



for s in 'verbs neighbors function' 'verbs neighbors' 'verbs function' 'neighbors' 'verbs' 'function' 'content' 'headrule'
do
    cd src
    python udup.py --steps $s
    cd ..
    perl eval.pl -g data/en-ud-dov.conllu -s src/testout.conllu > "$s.pers.norev.eval"
done
