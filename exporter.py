import os

from bs4 import BeautifulSoup

import utils
import shutil
from constants import bcolors
from dtstructures import Shelve, Book


class Exporter:
    def __init__(self, bookstack_session, user):
        self.pages = []
        self.books = []
        self.shelves = []
        self.bookstack_session = bookstack_session
        self.xwiki_user = {'login': user["xwiki"]["login"], 'password': user["xwiki"]["password"]}
        self.bookstack_user = {'login': user["bookstack"]["login"], 'password': user["bookstack"]["password"]}
        self.xwiki_url = user["xwiki"]["url"]
        self.xwiki_home_url = user["xwiki"]["home"]
        self.bookstack_url = user["bookstack"]["url"]
        self.link_dict = {}
        class Exporter:
    """A class that exports data from a bookstack_session to a wiki.

    Args:
        bookstack_session (object): An object representing a session with the Bookstack API.
        user (dict): A dictionary containing user login credentials and urls for the Bookstack and XWiki platforms.

    Attributes:
        pages (list): A list containing all the pages to be exported.
        books (list): A list containing all the books to be exported.
        shelves (list): A list containing all the shelves to be exported.
        bookstack_session (object): An object representing a session with the Bookstack API.
        xwiki_user (dict): A dictionary containing the user login credentials for XWiki.
        bookstack_user (dict): A dictionary containing the user login credentials for Bookstack.
        xwiki_url (str): A string representing the url for the XWiki platform.
        xwiki_home_url (str): A string representing the url for the XWiki home page.
        bookstack_url (str): A string representing the url for the Bookstack platform.
        link_dict (dict): A dictionary containing links to pages, books, and shelves.

    """

    def __init__(self, bookstack_session, user):
        """Initializes an Exporter object with the given Bookstack session and user credentials."""
        self.pages = []
        self.books = []
        self.shelves = []
        self.bookstack_session = bookstack_session
        self.xwiki_user = {'login': user["xwiki"]["login"], 'password': user["xwiki"]["password"]}
        self.bookstack_user = {'login': user["bookstack"]["login"], 'password': user["bookstack"]["password"]}
        self.xwiki_url = user["xwiki"]["url"]
        self.xwiki_home_url = user["xwiki"]["home"]
        self.bookstack_url = user["bookstack"]["url"]
        self.link_dict = {}

    def export_shelves(self):
        result = utils.get_page(self.bookstack_session, self.bookstack_url)
        content = utils.preprocess_page(result.content)
        main_page = BeautifulSoup(content, features="html.parser")
        content = main_page.body.find_all('div', attrs={'class', 'grid-card-content'})
        print("SHELVES EXPORT:")
        self.shelves = []
        for i in range(0, len(content)):
            shelve = Shelve(self.xwiki_url, self.xwiki_url + '/bin/view/ITG', user=self.xwiki_user).export(
                content[i].find('a').attrs['href'], self.bookstack_session)
            self.link_dict[shelve.page_name] = self.xwiki_url + '/bin/view/ITG'
            self.shelves.append(shelve)
            print(shelve.page_name, " exported")
        return self.shelves
    
     """
    Exports all shelves from Bookstack to XWiki.

    Returns
    -------
    shelves : list
        A list containing all the shelves that were exported.

    Notes
    -----
    This function calls the Shelve.export() function to export each individual shelf from Bookstack to XWiki.
    """
   

    def import_shelves(self):
        print("SHELVES IMPORT:")
        for shelve in self.shelves:
            resp = shelve.import_elem()
            if 200 < resp.status_code <= 202:
                print(bcolors.OKGREEN + "Shelve: ", shelve.page_name, " , response code: ", resp, " " + bcolors.ENDC)
            else:
                print(bcolors.FAIL + "Shelve: ", shelve.page_name, " , response code: ", resp, " " + bcolors.ENDC)

 
    """Imports all shelves from XWiki.

    Notes
    -----
    This function calls the Shelve.import_elem() function to import each individual shelf from XWiki.
    """

    def export_books(self):
        print("BOOKS EXPORT:")
        self.books = []
        for shelve in self.shelves:
            for book in shelve.subelems:
                self.books.append(book.export(book.export_url, self.bookstack_session))
                print("Book ", book.title, " exported, pages and chapters: ", book.subelems)
        for book in self.export_missing_books(self.books):
            self.books.append(book.export(book.export_url, self.bookstack_session))
            print("Book ", book.title, " exported, pages and chapters: ", book.subelems)
        return self.books
    
      """
    Exports all books from Bookstack to XWiki.

    Notes
    -----
    This function exports all books from Bookstack to XWiki. It loops through each shelve in self.shelves and then loops through
    each book in the shelve's subelements. For each book, it calls the Book.export() function to export the book to XWiki.
    If any books are missing from self.books, the function calls self.export_missing_books() to export those books as well.
    """

    def import_books(self):
        for book in self.books:
            resp = book.import_elem()
            self.link_dict[book.page_name] = book.link
            if 200 < resp.status_code <= 202:
                print(bcolors.OKGREEN + "Book: ", book.page_name, " , response code: ", resp, "" + bcolors.ENDC)
            else:
                print(bcolors.FAIL + "Book: ", book.page_name, " , response code: ", resp, "" + bcolors.ENDC)
    """
    Imports the books in the `self.books` list to the XWiki instance specified by `self.xwiki_url`.
    Sets the `link_dict` dictionary with page names and their corresponding links in XWiki.
    
    Returns:
    None
    
    Raises:
    None
   """
    def export_missing_books(self, books):
        additional_books = []
        for i in range(1, 6):
            html_links = self.export_books_page_links(i)
            for html_link in html_links:
                if not utils.book_exists(books, html_link['href']):
                    additional_books.append(
                        Book(
                            self.xwiki_url,
                            '',
                            self.xwiki_url + '/bin/view/ITG/' + utils.get_link_page_name(html_link['href']),
                            html_link['href'],
                            self.xwiki_url + '/rest/wikis/xwiki/spaces/ITG',
                            user=self.xwiki_user
                        )
                    )
        return additional_books

 
    """Searches for missing books in the Bookstack instance and creates Book objects for them.

    Parameters
    ----------
    books : list
        A list of Book objects that have already been exported from Bookstack.

    Returns
    -------
    additional_books : list
        A list of Book objects that were found in the Bookstack instance but not in the input list of books.

    Notes
    -----
    This function searches the first 5 pages of the "Books" section in the Bookstack instance for book links that have
    not been exported yet. For each missing book, a new Book object is created and added to the output list.
"""


    def export_books_page_links(self, page_number):
        page = self.bookstack_session.get(
            self.bookstack_url + '/books?page=' + str(page_number),
            headers=dict(referer=self.bookstack_url)
        ).content.decode('utf-8')
        return BeautifulSoup(utils.preprocess_page(page), features="html.parser").body.find_all('a', attrs={'class',
                                                                                                            'entity-list-item-link'})
    """
    Export the links to all books on the given page number.

    Parameters
    ----------
    page_number : int
        The page number of the books to export.

    Returns
    -------
    numpy.ndarray
        A 1D numpy array of book links as strings.

    Raises
    ------
    ValueError
        If the given page_number is not an integer greater than zero.
    """


    def export_pages(self):
        print("PAGES EXPORT:")
        os.mkdir(os.curdir + "/exports")
        print("Created exports directory")
        pages, chapters = self.export_pages_and_chapters(self.books)
        self.books += chapters
        self.pages = pages
        for page in self.pages:
            self.link_dict[page.page_name] = page.link
        return self.pages
    """
    Export all pages in the BookStack instance and store them in the 'exports' directory.

    Returns
    -------
    List[Page]
        A list of all exported pages as `Page` objects.

    Notes
    -----
    This function creates a new directory called 'exports' in the current working directory
    and exports all pages in the BookStack instance to this directory using the
    `export_pages_and_chapters` function. It also adds all exported pages and chapters to
    the `books` attribute of the `Exporter` instance and updates the `link_dict` attribute
    with the links to the exported pages. Finally, it returns a list of all exported pages
    as `Page` objects.
    """
    def export_pages_and_chapters(self, books):
        chapters = []
        pages = []
        for book in books:
            additional_books, pg = self.export_pages_and_books(book.subelems)
            pages += pg
            if len(additional_books) > 0:
                additional_pages, chapters = self.export_pages_and_chapters(additional_books)
                chapters += additional_books
                pages += additional_pages
        return pages, chapters
    """
        Export pages and chapters from a list of books.

        Parameters
        ----------
        books : list of Book
            The books to export pages and chapters from.

        Returns
        -------
        pages : list of Page
            The exported pages.
        chapters : list of Chapter
            The exported chapters.

        Notes
        -----
        This function recursively exports pages and chapters from a list of books.
        For each book, it exports its subelements (if any) and adds them to the list of pages.
        If the subelements include additional books, this function calls itself recursively
        to export their pages and chapters as well. The exported pages and chapters are returned
        as separate lists.

        """
    

    def export_pages_and_books(self, subelems):
        additional_books = []
        pages = []
        for subelem in subelems:
            if isinstance(subelem, Book):
                subelem.export(subelem.export_url, self.bookstack_session)
                resp = subelem.import_elem()
                self.link_dict[subelem.page_name] = subelem.link
                additional_books.append(subelem)
                print("Chapter ", subelem.title, " exported, pages and chapters: ", subelem.subelems)
                continue
            pages.append(subelem)
            print("Page ", subelem.page_name, "exported")
        return additional_books, pages
       """
    Exports all pages and books in a list of sub-elements recursively.

    Parameters
    ----------
    subelems : list
        A list of sub-elements to export.

    Returns
    -------
    tuple
        A tuple containing two lists: additional_books, and pages. 
        additional_books is a list of Book objects that were exported, and 
        pages is a list of Page objects that were exported.

    Raises
    ------
    None

    Notes
    -----
    This method exports all Book objects in subelems and recursively 
    exports all their sub-elements. Pages are added to the pages list 
    and Book objects are added to the additional_books list. 

    """
    

    def parse_pages(self):
        print("PAGES PARSING:")
        for page in self.pages:
            page.export(self.bookstack_session)
            if 'business-trips' in page.page_name:
                print(1)
            page.parse_page(self.link_dict)
            print("Page ", page.page_name, " parsed")
    """
    Parse the exported pages.

    This method exports each page, then parses its content using the `parse_page` method of the `Page` class.

    Returns:
        None
    """

    def import_pages(self):
        print("PAGES IMPORT:")
        counter = 0
        for page in self.pages:
            request_result = page.import_page(self.xwiki_url)
            if 200 < request_result.status_code <= 202:
                print(bcolors.OKGREEN + "Page: ", page.page_name, "imported , response code: ", request_result, "" + bcolors.ENDC)
            else:
                print(bcolors.FAIL + "Page: ", page.page_name, " failed , response code: ", request_result, "" + bcolors.ENDC)
            counter+=1
        print("Pages imported: ", str(counter))
        shutil.rmtree("exports")
        print("Removed exports folder")
    """
    Imports pages to the XWiki instance.

    Returns
    -------
    None
        This method has no return value.

    Notes
    -----
    This method sends a POST request to the XWiki instance to import each page
    in the `self.pages` list. If the request returns a status code between 200
    and 202, the page is considered successfully imported, otherwise it is
    considered failed.

    After importing all pages, the `exports` directory created in the
    `export_pages` method is deleted.

    Examples
    --------
    >>> my_importer = MyWikiImporter()
    >>> my_importer.import_pages()
    PAGES IMPORT:
    Page: Page1 imported , response code: 200
    Page: Page2 failed , response code: 500
    Pages imported: 2
    """

    def filter_similar_pages(self):
        unique_pages = []
        for elem in self.pages:
            if not utils.find_page(elem, unique_pages):
                unique_pages.append(elem)
        self.pages = unique_pages

    """
     Filter out similar pages from the list of pages.
    
    The method compares each page in the current list of pages with a list of unique pages. If a page is already
    present in the list of unique pages, it is not added again. This way, only unique pages are kept in the final list
    of pages.
    
    Returns:
        list: A list of unique pages.
    """