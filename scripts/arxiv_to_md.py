#!/usr/bin/env python3
"""
ArXiv to Markdown Converter
Usage: python arxiv_to_md.py <arxiv_id>
Example: python arxiv_to_md.py 1706.03762
"""

import sys
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
import re

def fetch_arxiv_paper(arxiv_id):
    """Fetch paper metadata from ArXiv API"""
    # Clean arxiv_id (remove version if present)
    clean_id = arxiv_id.split('v')[0]
    
    url = f"http://export.arxiv.org/api/query?id_list={clean_id}"
    response = requests.get(url)
    
    if response.status_code != 200:
        raise Exception(f"Failed to fetch paper: {response.status_code}")
    
    # Parse XML
    root = ET.fromstring(response.content)
    
    # Find entry
    entry = root.find('{http://www.w3.org/2005/Atom}entry')
    if entry is None:
        raise Exception("Paper not found")
    
    # Extract data
    paper = {}
    paper['id'] = entry.find('{http://www.w3.org/2005/Atom}id').text.split('/')[-1]
    paper['title'] = entry.find('{http://www.w3.org/2005/Atom}title').text.strip()
    paper['summary'] = entry.find('{http://www.w3.org/2005/Atom}summary').text.strip()
    paper['published'] = entry.find('{http://www.w3.org/2005/Atom}published').text
    
    # Authors
    authors = []
    for author in entry.findall('{http://www.w3.org/2005/Atom}author'):
        name = author.find('{http://www.w3.org/2005/Atom}name').text
        authors.append(name)
    paper['authors'] = authors
    
    # Categories
    categories = []
    for category in entry.findall('{http://www.w3.org/2005/Atom}category'):
        categories.append(category.get('term'))
    paper['categories'] = categories
    
    # Links
    paper['arxiv_url'] = f"https://arxiv.org/abs/{clean_id}"
    paper['pdf_url'] = f"https://arxiv.org/pdf/{clean_id}.pdf"
    
    return paper

def create_markdown(paper):
    """Convert paper data to markdown format"""
    
    # Clean title for filename
    safe_title = re.sub(r'[^\w\s-]', '', paper['title']).strip()
    safe_title = re.sub(r'[-\s]+', '_', safe_title)[:50]
    
    # Format date
    date_str = paper['published'][:10]  # YYYY-MM-DD
    
    # Format authors
    authors_md = "\n".join([f"- {author}" for author in paper['authors']])
    
    # Format categories
    categories_str = ", ".join(paper['categories'])
    
    # Create markdown content
    md_content = f"""# {paper['title']}

**ArXiv ID**: {paper['id']}  
**Published**: {date_str}  
**Categories**: {categories_str}  

## Authors
{authors_md}

## Abstract

{paper['summary']}

## Links
- [ArXiv Paper]({paper['arxiv_url']})
- [PDF]({paper['pdf_url']})

---
*Generated from ArXiv API on {date_str}*
"""
    
    return md_content, f"{paper['id'].replace('/', '_')}_{safe_title}.md"

def main():
    if len(sys.argv) != 2:
        print("Usage: python arxiv_to_md.py <arxiv_id>")
        print("Example: python arxiv_to_md.py 1706.03762")
        sys.exit(1)
    
    arxiv_id = sys.argv[1]
    
    try:
        print(f"Fetching paper {arxiv_id}...")
        paper = fetch_arxiv_paper(arxiv_id)
        
        print(f"Creating markdown for: {paper['title']}")
        md_content, filename = create_markdown(paper)
        
        # Create papers directory (relative to script location)
        papers_dir = Path("../papers")
        papers_dir.mkdir(exist_ok=True)
        
        # Save file in papers directory
        filepath = papers_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"✅ Created: {filepath}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
