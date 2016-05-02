
#Best system so far is only headrules

postype="goldpos"


s='headrule' #'verbs neighbors function headrule' 'verbs neighbors' 'verbs function' 'neighbors' 'verbs' 'function' 'content'
for lang in 'en' 'ar' 'cu' 'bg' 'cs' 'da' 'de' 'el' 'et' 'es' 'eu' 'fa' 'fi' 'fr' 'ga' 'got' 'grc' 'he' 'hi' 'hr' 'hu' 'id' 'it' 'la' 'nl' 'no' 'pl' 'pt' 'ro' 'sl' 'sv' 'ta'
do
    cd src
    python udup_ablation.py --steps $s --input ../data/orgtok/$postype/$lang-ud-test.conllu --lang $lang
    cd ..
    perl eval07.pl -g data/orgtok/goldpos/$lang-ud-test.conllu -s src/$lang"_testout.conllu" > "$lang.ablation.eval"
done

