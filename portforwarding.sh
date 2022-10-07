kubectl port-forward corenlp-7fd4974bb-8mq5g                4080:5001 -n chirpy &
kubectl port-forward dialogact-849b4b67d8-ngzd5             4081:5001 -n chirpy &
kubectl port-forward g2p-7644ff75bd-cjj57                   4082:5001 -n chirpy &
kubectl port-forward gpt2ed-68f849f64b-wr8zw                4083:5001 -n chirpy &
kubectl port-forward questionclassifier-668c4fd6c6-7nl2k   4084:5001 -n chirpy &
kubectl port-forward convpara-dbdc8dcfb-csktj               4085:5001 -n chirpy &
kubectl port-forward entitylinker-59b9678b8-nmwx9           4086:5001 -n chirpy &
kubectl port-forward blenderbot-695c7b5896-gkz2s            4087:5001 -n chirpy &
kubectl port-forward responseranker-666ff584c6-hq2w7        4088:5001 -n chirpy &
kubectl port-forward stanfordnlp-6894cd686b-j2qk2           4089:5001 -n chirpy &
kubectl port-forward infiller-bfdf7d9cb-ms7x2               4090:5001 -n chirpy &
kubectl port-forward postgresql-postgresql-0                5432:5432 -n chirpy
