import json
import os
import math
import re

def load_index(directory):
    index_path = os.path.join(directory, 'index.json')
    with open(index_path, 'r') as f:
        return json.load(f)

def tokenize(text):
    tokens = re.findall(r'\b\w+\b', text.lower())
    # We'll mimic the indexer's tokenization (stopwords + stemming)
    try:
        import nltk
        from nltk.corpus import stopwords
        from nltk.stem import PorterStemmer
        stop_words = set(stopwords.words('english'))
        stemmer = PorterStemmer()
        tokens = [t for t in tokens if t not in stop_words]
        tokens = [stemmer.stem(t) for t in tokens]
    except ImportError:
        pass
    return tokens

index = load_index('test_papers')
print("Index for 'learn':", index.get('learn', {}))

# Compute doc lengths
doc_lengths = {}
for term, postings in index.items():
    for doc_id, freq in postings.items():
        doc_lengths[doc_id] = doc_lengths.get(doc_id, 0) + freq
print("Doc lengths:", doc_lengths)
num_docs = len(doc_lengths)
print("Num docs:", num_docs)

query = "learning"
query_tokens = tokenize(query)
print("Query tokens:", query_tokens)
# compute query freq
q_freq = {}
for t in query_tokens:
    q_freq[t] = q_freq.get(t,0)+1
print("Query freq:", q_freq)

# compute scores
scores = {}
for term, qtf in q_freq.items():
    if term in index:
        idf = math.log(num_docs / (1 + len(index[term])))
        print(f"Term {term}: qtf={qtf}, idf={idf}")
        for doc_id, dtf in index[term].items():
            print(f"  Doc {doc_id}: dtf={dtf}")
            d_weight = dtf * idf
            q_weight = qtf * idf
            scores[doc_id] = scores.get(doc_id,0.0) + q_weight * d_weight
print("Raw scores:", scores)
# normalize by doc length
norm_scores = {}
for doc_id, score in scores.items():
    length = doc_lengths.get(doc_id,1)
    norm_scores[doc_id] = score / (length + 1)
    print(f"Doc {doc_id}: raw={score}, length={length}, normalized={norm_scores[doc_id]}")
print("Normalized scores:", norm_scores)