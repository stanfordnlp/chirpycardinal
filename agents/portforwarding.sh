kubectl port-forward corenlp-645bf44dcd-nwjds               4080:5001 -n chirpy &
kubectl port-forward dialogact-5b96f9d88f-lcfvj             4081:5001 -n chirpy &
kubectl port-forward g2p-7cbcb758b4-bzkcb                   4082:5001 -n chirpy &
kubectl port-forward gpt2ed-5fb664cf7b-djvqm                4083:5001 -n chirpy &
kubectl port-forward questionclassifier-67f95b648d-vq2jw    4084:5001 -n chirpy &
kubectl port-forward convpara-dbdc8dcfb-csktj               4085:5001 -n chirpy &
kubectl port-forward entitylinker-57b8576774-qwfmr           4086:5001 -n chirpy &
kubectl port-forward blenderbot-74dd55549f-8gg4x           4087:5001 -n chirpy &
kubectl port-forward responseranker-6ff6946fb9-mwhpv        4088:5001 -n chirpy &
kubectl port-forward stanfordnlp-67d865db5f-b5xv5           4089:5001 -n chirpy &
kubectl port-forward infiller-bfdf7d9cb-ms7x2               4090:5001 -n chirpy &
kubectl port-forward postgresql-postgresql-0                5432:5432 -n chirpy