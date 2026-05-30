import sys
sys.path.append('.')
from research_assistant.indexer import Indexer

indexer = Indexer()
text = indexer._extract_text('test_papers/deep_learning.txt')
print('Extracted text length:', len(text))
print('First 100 chars:', repr(text[:100]))
print('Lines:', text.count('\\n'))
tokens = indexer._tokenize(text)
print('Number of tokens:', len(tokens))
print('First 10 tokens:', tokens[:10])