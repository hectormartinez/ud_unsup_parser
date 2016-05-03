
#Best system so far is only headrules


s='headrule'
for domain in 'bg_legal' 'bg_literature' 'bg_news' 'bg_predisentbulletin' 'bg_various' 'en_answers' 'en_bib50' 'en_email' 'en_newsgroup' 'en_questions' 'en_reviews' 'en_watch_56' 'en_weblog' 'hr_news' 'hr_wiki' 'it_europarl' 'it_newslegal' 'it_newspaper' 'it_questions' 'it_various' 'it_wiki' 'sr_news' 'sr_wiki'
do
    cd src
    python udup.py --steps $s --input ../data/orgtok/domains/predpos/$domain-ud-test.conllu --lang $domain
    cd ..
    perl eval07.pl -g data/orgtok/domains/$domain-ud-test.conllu -s src/$domain"_testout.conllu" > "$domain.domainspred.eval"
done

