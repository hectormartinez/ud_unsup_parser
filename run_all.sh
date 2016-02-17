
for s in 'neighbors' 'verbs' 'function' 'content' 'headrule'
do
    cd src
    python udup.py --steps $step
    cd ..
    perl eval -g data/en-ud-dev.conllu > $s.eval
done
