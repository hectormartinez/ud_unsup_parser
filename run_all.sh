
for s in 'neighbors' 'verbs' 'function' 'content' 'headrule'
do
    cd src
    python udup.py --steps $s
    cd ..
    perl eval.pl -g data/en-ud-dev.conllu -s src/testout.conllu > $s.eval
done
