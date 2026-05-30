import argparse
import sys
from .indexer import Indexer
from .searcher import Searcher

def main():
    parser = argparse.ArgumentParser(description='Research Assistant')
    subparsers = parser.add_subparsers(dest='command')

    # Index command
    index_parser = subparsers.add_parser('index', help='Index a directory of documents')
    index_parser.add_argument('--dir', required=True, help='Directory to index')
    index_parser.add_argument('--ext', nargs='*', default=['.txt', '.pdf'], help='File extensions to index')

    # Search command
    search_parser = subparsers.add_parser('search', help='Search the index')
    search_parser.add_argument('--query', required=True, help='Search query')
    search_parser.add_argument('--limit', type=int, default=10, help='Maximum results to return')

    args = parser.parse_args()

    if args.command == 'index':
        indexer = Indexer()
        indexer.index_directory(args.dir, args.ext)
        print(f'Indexed documents from {args.dir}')
    elif args.command == 'search':
        searcher = Searcher()
        results = searcher.search(args.query, args.limit)
        for i, (doc, score) in enumerate(results, 1):
            print(f'{i}. {doc} (score: {score:.2f})')
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()