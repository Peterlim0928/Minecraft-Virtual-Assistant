import os
import re
import requests
from bs4 import BeautifulSoup
import logging
import json

# Configure logging
logging.basicConfig(
    filename='output.txt',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    filemode='w'  # 'w' to overwrite, 'a' to append
)

HEADERS = {
    "User-Agent": "FriendlyResearchBot/1.0 (contact: limjiantao@gmail.com)"
}

class MinecraftWikiParser:
    """Parser for extracting structured content from Minecraft Wiki pages."""
    
    def __init__(self, url):
        self.url: str = url
        self.title: str = None
        self.content: list = None
        self.parse()  # Automatically parse on initialization
    
    def parse(self):
        """Parse the page and extract content into a list."""
        # Fetch HTML
        response = requests.get(self.url, headers=HEADERS)
        if response.status_code != 200:
            logging.error(f"Failed to fetch page: {self.url}")
            return
        
        # Create BeautifulSoup object
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract title
        self.title = soup.find('h1', {'id': 'firstHeading'}).get_text()
        
        # Build tree structure
        self._extract(soup)
    
    def _extract(self, soup):
        """Extract the content from BeautifulSoup object."""
        main_content = soup.find('div', {'class': 'mw-parser-output'})
        content = []
        section_hierarchy = ["Introduction"]  # Track section path as a list

        for element in main_content.children:
            if element.name in ['h2', 'h3', 'h4']:
                # Header - update section hierarchy but don't append to content
                header_text = element.get_text().replace('[edit | edit source]', '').strip()
                header_level = int(element.name[1])  # 2, 3, or 4
                
                # Update hierarchy based on level
                # h2 replaces everything, h3 replaces from index 1, h4 replaces from index 2
                if header_level == 2:
                    section_hierarchy = [header_text]
                elif header_level == 3:
                    section_hierarchy = section_hierarchy[:1] + [header_text]
                elif header_level == 4:
                    section_hierarchy = section_hierarchy[:2] + [header_text]
            elif element.name == 'p':
                # Paragraph
                paragraph_text = element.get_text()
                if paragraph_text:
                    content.append({
                        "type": "paragraph",
                        "section": " > ".join(section_hierarchy),
                        "text": paragraph_text
                    })
            elif element.name in ['ul', 'ol']:
                # List
                items = [li.get_text() for li in element.find_all('li')]
                if items:
                    content.append({
                        "type": "list",
                        "section": " > ".join(section_hierarchy),
                        "items": items
                    })
            elif element.name == 'table':
                # Table (simple extraction)
                table_data = []
                for row in element.find_all('tr'):
                    cols = [col.get_text() for col in row.find_all(['td', 'th'])]
                    if cols:
                        table_data.append(cols)
                if table_data:
                    content.append({
                        "type": "table",
                        "section": " > ".join(section_hierarchy),
                        "data": table_data
                    })
            elif element.name == 'div' and 'infobox' in element.get('class', []):
                # Infobox
                infobox_data = {}
                for row in element.find_all('tr'):
                    header = row.find('th')
                    value = row.find('td')
                    if header and value:
                        infobox_data[header.get_text()] = value.get_text()
                if infobox_data:
                    content.append({
                        "type": "infobox",
                        "section": " > ".join(section_hierarchy),
                        "data": infobox_data
                    })
            elif element.name == 'div' and 'droptable-tabber' in element.get('class', []):
                # Droptable
                drop_tables = []
                for table in element.find_all('table'):
                    table_data = []
                    for row in table.find_all('tr'):
                        cols = [col.get_text() for col in row.find_all(['td', 'th'])]
                        if cols:
                            table_data.append(cols)
                    if table_data:
                        drop_tables.append(table_data)
                if drop_tables:
                    content.append({
                        "type": "droptable",
                        "section": " > ".join(section_hierarchy),
                        "data": drop_tables
                    })
        
        self.content = content

    def to_json(self):
        """Convert the extracted content to JSON format."""
        return json.dumps(self.content, indent=2)
    
    def save_to_file(self, folder):
        """Save the content to a JSON file using the page title as filename."""
        if not self.title or not self.content:
            logging.error("Cannot save: title or content is missing")
            return
        
        # Sanitize filename (remove invalid characters)
        filename = re.sub(r'[<>:"/\\|?*]', '_', self.title) + '.json'
        
        filepath = os.path.join(folder, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.content, f, indent=2, ensure_ascii=False)
        
        logging.info(f"Saved content to {filename}")
        return filename

if __name__ == "__main__":
    # Example usage
    parser = MinecraftWikiParser("https://minecraft.wiki/w/Iron_Golem")
    parser.save_to_file("json")