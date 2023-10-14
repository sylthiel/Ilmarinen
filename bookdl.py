import requests
from bs4 import BeautifulSoup
from ebooklib import epub

book = epub.EpubBook()

# set metadata
book.set_identifier('id123456')
book.set_title('12 miles below')
book.set_language('en')

book.spine = ['nav']
chapter_count = 1
# gets the link to the initial chapter
link = "https://web.archive.org/web/20220804042520/https://www.royalroad.com/fiction/42367/12-miles-below/chapter/744074/book-2-prologue"
head_url = 'https://web.archive.org'
while True:
    content = requests.get(link).content
    soup = BeautifulSoup(content, 'html.parser')

    # find chapter text
    chapter_text = soup.find('div', {'class': 'chapter-inner chapter-content'}).text
    # create unique filename for each chapter
    filename = f'chap_{str(chapter_count).zfill(2)}.xhtml'
    # create epub html chapter
    chapter = epub.EpubHtml(title='Chapter title', file_name=filename, lang='en')
    chapter.content = f'<h1>Chapter pyth{chapter_count}</h1><p>' + chapter_text + '</p>'

    # add chapter
    book.add_item(chapter)
    book.spine.append(chapter)
    chapter_count += 1
    # Look for the next chapter
    try:
        next_btn = soup.find_all('a', {'class': 'btn btn-primary col-xs-4'})[2]
    except IndexError:
        break
    link = head_url + next_btn['href']
    if 'book-3' in link:
        break
    print(f"Trying link {link}")

# black magic that actually makes the epub work
book.set_identifier('id123456')
book.set_title('12 miles below')
book.set_language('en')

# Initialize navigation
nav = epub.EpubNav()
nav.id = "nav" # The "nav" property is for books in the EPUB 3 format.
book.add_item(nav)

# Extract only chapters
chapter_items = [item for item in book.get_items() if item.id.startswith('chapter_')]

# Update book.toc & book.spine
book.toc = chapter_items
book.spine = [nav] + chapter_items

# Define EPUB version
book.version = '2.0'

# Write book to an .epub file
epub.write_epub('12_miles_below.epub', book, {})
epub.write_epub('12_miles_below.epub', book, {})