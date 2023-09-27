---
title: Human-like informative conversations via conditional mutual information
extlink: https://arxiv.org/pdf/2104.07831.pdf
authors: Ashwin Paranjape and Christopher D. Manning
venue: North American Chapter of the Association for Computational Linguistics (NAACL), 2021
---
The goal of this work is to build a dialogue agent that can weave new factual content into conversations as naturally as humans. We draw insights from linguistic principles of conversational analysis and annotate human-human conversations from the Switchboard Dialog Act Corpus, examinining how humans apply strategies for acknowledgement, transition, detail selection and presentation. However, when current chatbots (explicitly provided with new factual content) introduce facts in a
conversation, their generated responses do not acknowledge the prior turns. This is because, while current methods are trained with two contexts, new factual content and conversational history, we show that their generated responses are not simultaneously specific to both the contexts and in particular, lack specificity w.r.t conversational history. 
We propose using pointwise conditional mutual information (pcmi) to measure specificity w.r.t. conversational history. We show that responses that have a higher pcmi_h are judged by human evaluators to be better at acknowledgement 74% of the time.
To show its utility in improving overall quality, we compare baseline responses that maximize pointwise mutual information (Max. PMI) with our alternative responses (Fused-PCMI) that trade off pmi for pcmi_h and find that human evaluators prefer Fused-PCMI 60% of the time. 
