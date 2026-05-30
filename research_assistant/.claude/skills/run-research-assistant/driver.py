#!/usr/bin/env python3
"""
Driver script for Research Assistant skill.
Provides programmatic interface to build, run, and test the research assistant.
"""

import subprocess
import sys
import os
import json
import time
from pathlib import Path

# Add the project root to Python path so we can import research_assistant
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def run_command(cmd, cwd=None, check=True):
    """Run a command and return result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
    return result


def install_dependencies():
    """Install required dependencies."""
    print("Installing dependencies...")
    run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])


def index_documents(directory="test_papers", extensions=None):
    """Index documents in the specified directory."""
    cmd = [sys.executable, "-m", "research_assistant.cli", "index", "--dir", directory]
    if extensions:
        cmd.extend(["--ext"] + extensions)
    run_command(cmd)
    print(f"Indexed documents from {directory}")


def search_index(query, directory="test_papers", limit=10):
    """Search the index and return results."""
    cmd = [
        sys.executable, "-m", "research_assistant.cli", "search",
        "--dir", directory,
        "--query", query,
        "--limit", str(limit)
    ]
    result = run_command(cmd, check=False)
    if result.returncode != 0:
        print(f"[FAIL] Search error: {result.stderr}")
        return []

    # Parse output to extract results
    lines = result.stdout.strip().split('\n')
    results = []
    for line in lines:
        line = line.strip()
        if line and ('.txt' in line or '.docx' in line or '.md' in line):
            # Format: "1. filename (score: 0.45)"
            if '. ' in line and ' (score:' in line:
                parts = line.split('. ', 1)
                if len(parts) > 1:
                    rest = parts[1]
                    filename_score = rest.split(' (score:')
                    if len(filename_score) == 2:
                        filename = filename_score[0]
                        try:
                            score = float(filename_score[1].rstrip(')'))
                            results.append((filename, score))
                        except ValueError:
                            pass
    return results


def verify_installation():
    """Verify the installation works."""
    print("Verifying installation...")
    # Test CLI help - this tests both that the module can be found and works
    # Run from the project root so that research_assistant package can be found
    result = run_command([sys.executable, "-m", "research_assistant.cli", "--help"], cwd=PROJECT_ROOT, check=False)
    if result.returncode == 0 and "Research Assistant" in result.stdout:
        print("[PASS] CLI help works correctly")
        return True
    else:
        print("[FAIL] CLI help failed")
        if result.stderr:
            print(f"       Error: {result.stderr.strip()}")
        return False


def demo_workflow():
    """Demonstrate a complete workflow."""
    print("\n=== Research Assistant Demo Workflow ===\n")

    # 1. Verify installation
    if not verify_installation():
        return False

    # 2. Index documents (if not already indexed)
    index_path = Path("test_papers/index.json")
    if not index_path.exists():
        print("1. Indexing documents...")
        index_documents()
    else:
        print("1. Index already exists, skipping indexing...")

    # 2. Search for terms
    print("\n2. Testing search functionality...")

    test_queries = [
        "machine learning",
        "deep learning",
        "artificial intelligence",
        "neural network"
    ]

    for query in test_queries:
        print(f"\n   Searching for: '{query}'")
        results = search_index(query, limit=3)
        if results:
            for i, (filename, score) in enumerate(results, 1):
                print(f"      {i}. {filename} (score: {score:.2f})")
        else:
            print("      No results found")

    # 3. Test with specific file types if available
    print("\n3. Testing extended format support...")
    docx_path = Path("test_papers/test_doc.docx")
    md_path = Path("test_papers/test_doc.md")

    if docx_path.exists() or md_path.exists():
        # Re-index with all extensions
        print("   Re-indexing with .docx and .md support...")
        index_documents(extensions=[".txt", ".pdf", ".docx", ".md"])

        print("   Searching for test content...")
        results = search_index("test", limit=5)
        for i, (filename, score) in enumerate(results, 1):
            print(f"      {i}. {filename} (score: {score:.2f})")
    else:
        print("   No test .docx/.md files found - skipping extended format test")

    print("\n=== Demo Complete ===")
    return True


def main():
    """Main driver function."""
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nUsage:")
        print("  python driver.py install     - Install dependencies")
        print("  python driver.py index [dir] - Index documents")
        print("  python driver.py search <q>  - Search index")
        print("  python driver.py verify      - Verify installation")
        print("  python driver.py demo        - Run complete demo workflow")
        return 1

    command = sys.argv[1].lower()

    try:
        if command == "install":
            install_dependencies()
        elif command == "index":
            directory = sys.argv[2] if len(sys.argv) > 2 else "test_papers"
            extensions = None
            if len(sys.argv) > 3:
                extensions = sys.argv[3:]  # Accept multiple extensions
            index_documents(directory, extensions)
        elif command == "search":
            if len(sys.argv) < 3:
                print("Error: search query required")
                return 1
            query = sys.argv[2]
            directory = sys.argv[3] if len(sys.argv) > 3 else "test_papers"
            limit = int(sys.argv[4]) if len(sys.argv) > 4 else 10
            results = search_index(query, directory, limit)
            print(f"Search results for '{query}':")
            for i, (filename, score) in enumerate(results, 1):
                print(f"  {i}. {filename} (score: {score:.2f})")
        elif command == "verify":
            if verify_installation():
                print("✓ Installation verified successfully")
                return 0
            else:
                print("✗ Installation verification failed")
                return 1
        elif command == "demo":
            if demo_workflow():
                return 0
            else:
                return 1
        else:
            print(f"Unknown command: {command}")
            return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())