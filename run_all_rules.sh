
#Best system so far is only headrules

evalfile="eval_all_langs_rules"
touch $evalfile

cd src
for postype in 'goldpos' 'predpos'
do
    #for lang in 'ar' 'bg' 'cs' 'da' 'de' 'el' 'en' 'et' 'es' 'eu' 'fa' 'fi' 'fr' 'grc' 'he' 'hi' 'hr' 'hu' 'id' 'it' 'la' 'nl' 'no' 'pl' 'pt' 'sl' 'sv' 'ta'
    for lang in 'ar' 'bg' 'cs' 'da' 'de'  'en' 'es' 'eu' 'fa' 'fi' 'fr' 'grc' 'he' 'hi' 'hr' 'id' 'it' 'nl' 'no' 'pl' 'pt' 'sl' 'sv'
    #for lang in 'en'
    do
        for n in 1 2 3 4 5 6 7 8 9 10
        do
        filename=$lang-ud-test.conllu.delex.sample_$n
        inputpath=../data/parse/$postype/test/$filename
        evalpath=../data/parse/goldpos/test/$filename

        python udup.py --parsing_strategy rules --input $inputpath --output $filename > /dev/null
        UAS=`perl ../eval07.pl -g $evalpath -s $filename.rules 2> /dev/null |head -n2|tail -n1`
        root=`perl ../eval07.pl -g $evalpath -s $filename.rules 2> /dev/null|grep root -m 1`
        echo "$postype $filename $UAS $root" #>> $evalfile
        done
    done
done

#python summarize_scores.py