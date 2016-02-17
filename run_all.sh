
for s in 'verbs neighbors function''verbs neighbors' 'verbs function' 'neighbors' 'verbs' 'function' 'content' 'headrule'
do
    cd src
    python udup.py --steps $s
    cd ..
    perl eval.pl -g data/en-ud-dev.conllu -s src/testout.conllu > "$s.nocomp.eval"
done
