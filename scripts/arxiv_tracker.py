#!/usr/bin/env python3
import feedparser
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# ArXiv search queries for LLM-related papers -- https://arxiv.org/category_taxonomy --
QUERIES = [
    "cat:cs.CL+AND+(large+language+model+OR+LLM+OR+transformer+OR+GPT)",
    "cat:cs.AI+AND+(language+model+OR+LLM+OR+ChatGPT+OR+instruction+tuning)",
    "cat:cs.LG+AND+(foundation+model+OR+pre-trained+model+OR+RLHF)"
]

def fetch_recent_papers(days_back=1):
    """Fetch papers from the last N days"""
    papers = []
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    for query in QUERIES:
        url = f"http://export.arxiv.org/api/query?search_query={query}&start=0&max_results=50&sortBy=submittedDate&sortOrder=descending"
        
        feed = feedparser.parse(url)
        
        for entry in feed.entries:
            # Parse date
            published = datetime.strptime(entry.published, "%Y-%m-%dT%H:%M:%SZ")
            
            if published >= cutoff_date:
                paper = {
                    "title": entry.title.replace('\n', ' ').strip(),
                    "authors": [author.name for author in entry.authors],
                    "abstract": entry.summary.replace('\n', ' ').strip(),
                    "url": entry.link,
                    "arxiv_id": entry.id.split('/')[-1],
                    "published": entry.published,
                    "categories": [tag.term for tag in entry.tags]
                }
                papers.append(paper)
    
    # Remove duplicates by arxiv_id
    seen = set()
    unique_papers = []
    for paper in papers:
        if paper['arxiv_id'] not in seen:
            seen.add(paper['arxiv_id'])
            unique_papers.append(paper)
    
    return unique_papers

def load_existing_papers():
    """Load previously tracked papers"""
    papers_file = Path("data/arxiv_papers.json")
    if papers_file.exists():
        with open(papers_file) as f:
            return json.load(f)
    return []

def save_papers(papers):
    """Save papers to JSON file"""
    papers_file = Path("data/arxiv_papers.json")
    papers_file.parent.mkdir(exist_ok=True)
    
    with open(papers_file, 'w') as f:
        json.dump(papers, f, indent=2)

def create_paper_md(paper):
    """Create individual markdown file for paper"""
    papers_dir = Path("papers")
    papers_dir.mkdir(exist_ok=True)
    
    # Clean filename
    safe_title = "".join(c for c in paper['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
    filename = f"{paper['arxiv_id'].replace('/', '_')}_{safe_title[:50]}.md"
    
    # Format authors
    authors_list = "\n".join([f"- {author}" for author in paper['authors']])
    
    # Format categories
    categories_list = ", ".join(paper['categories'])
    
    # Create markdown content
    md_content = f"""# {paper['title']}

## Paper Information
- **ArXiv ID**: {paper['arxiv_id']}
- **URL**: {paper['url']}
- **Published**: {paper['published']}
- **Categories**: {categories_list}

## Authors
{authors_list}

## Abstract
{paper['abstract']}

## Links
- [ArXiv Paper]({paper['url']})
- [PDF]({paper['url'].replace('/abs/', '/pdf/')}.pdf)

---
*Auto-generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    # Save markdown file
    md_file = papers_dir / filename
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    return md_file

def update_readme(new_papers):
    """Update README with new papers"""
    if not new_papers:
        return
    
    readme_path = Path("README.md")
    with open(readme_path) as f:
        content = f.read()
    
    # Find the trending section
    trending_start = content.find("## Trending LLM Projects")
    if trending_start == -1:
        return
    
    # Add new papers after trending section
    new_entries = []
    for paper in new_papers[:5]:  # Only add top 5
        authors_str = ", ".join(paper['authors'][:3])
        if len(paper['authors']) > 3:
            authors_str += " et al."
        
        entry = f"- [{paper['title']}]({paper['url']}) - {authors_str}"
        new_entries.append(entry)
    
    if new_entries:
        # Insert after the trending section
        insert_pos = content.find("\n\n", trending_start)
        new_section = f"\n\n## Latest ArXiv Papers (Auto-updated)\n\n" + "\n".join(new_entries) + "\n"
        
        # Remove old auto-updated section if exists
        old_section_start = content.find("## Latest ArXiv Papers (Auto-updated)")
        if old_section_start != -1:
            old_section_end = content.find("\n## ", old_section_start + 1)
            if old_section_end == -1:
                old_section_end = len(content)
            content = content[:old_section_start] + content[old_section_end:]
            insert_pos = content.find("\n\n", trending_start)
        
        updated_content = content[:insert_pos] + new_section + content[insert_pos:]
        
        with open(readme_path, 'w') as f:
            f.write(updated_content)

def main():
    # Load existing papers
    existing_papers = load_existing_papers()
    existing_ids = {p['arxiv_id'] for p in existing_papers}
    
    # Fetch recent papers
    recent_papers = fetch_recent_papers()
    
    # Filter new papers
    new_papers = [p for p in recent_papers if p['arxiv_id'] not in existing_ids]
    
    if new_papers:
        print(f"Found {len(new_papers)} new papers")
        
        # Create markdown files for new papers
        created_files = []
        for paper in new_papers:
            md_file = create_paper_md(paper)
            created_files.append(md_file)
            print(f"Created: {md_file}")
        
        # Update data
        all_papers = new_papers + existing_papers
        save_papers(all_papers)
        
        # Update README
        update_readme(new_papers)
        
        # Print summary
        print(f"\nNew papers summary:")
        for paper in new_papers:
            print(f"- {paper['title']} ({paper['arxiv_id']})")
    else:
        print("No new papers found")

if __name__ == "__main__":
    main()
