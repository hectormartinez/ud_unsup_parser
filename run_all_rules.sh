
#Best system so far is only headrules

cd src
for postype in 'goldpos' 'predpos'
do
    for lang in 'ar' 'bg' 'cs' 'da' 'de' 'en' 'es' 'eu' 'fa' 'fi' 'fr' 'he' 'hi' 'hr' 'id' 'it' 'nl' 'no' 'pl' 'pt' 'sl' 'sv'
    do

        filename=$lang-ud-test.conllu.delex.sample_1
        inputpath=../data/delex_joined_tokens/$postype/test/$filename
        evalpath=../data/delex_joined_tokens/goldpos/test/$filename

        python udup.py --parsing_strategy rules --input $inputpath --output $filename > /dev/null
        perl ../eval07.pl -g $filename.rules -s $filename.rules 2> /dev/null |head -n2|tail -n1
    done
done
