import os
import sys
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT_DIR)

from fastapi import APIRouter
from typing import Optional

from supabase import create_client
from dotenv import load_dotenv

router = APIRouter(prefix='/search', tags=['Search'], responses={404: {"description": "Not found"}})

load_dotenv() 
SUPABASE_URL = os.getenv('supabase_url')
SUPABASE_KEY = os.getenv('supabase_key')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@router.get("/title")
def search_books_author(title: Optional[str] = None):
    query = supabase.table('bookshelf_book').select('*')
    if title:
        query = query.ilike('title', f'%{title}%')
    response = query.execute()
    return response.data

@router.get("/author")
def search_books_title(author: Optional[str] = None):
    query = supabase.table('bookshelf_book').select('*')
    if author:
        query = query.ilike('author', f'%{author}%')
    response = query.execute()
    return response.data

@router.get('/isbn')
def search_books_isbn(isbn: Optional[str] = None):
    query = supabase.table('bookshelf_book').select('*')
    if isbn:
        query = query.ilike('isbn', f'%{isbn}%')
    response = query.execute()
    return response.data

@router.get('/publisher')
def search_books_publisher(publisher: Optional[str] = None):
    query = supabase.table('bookshelf_book').select('*')
    if publisher:
        query = query.ilike('publisher', f'%{publisher}%')
    response = query.execute()
    return response.data

@router.get("/")
async def search_books(keyword: Optional[str] = None):
    response = []
    
    if not keyword:
        query_no_key = supabase.table('bookshelf_book').select('*').limit(1000).execute()
        response.extend(query_no_key.data)
        return response
    
    split_query = keyword.split(' ')
    print(split_query)

    for word in split_query:
        query_title = supabase.table('bookshelf_book').select('*').ilike('title', f'%{word}%').execute()
        query_author = supabase.table('bookshelf_book').select('*').ilike('author', f'%{word}%').execute()
        query_isbn = supabase.table('bookshelf_book').select('*').ilike('isbn', f'%{word}%').execute()
        response.extend(query_title.data)
        response.extend(query_author.data)
        response.extend(query_isbn.data)

    return list({book['id']: book for book in response}.values())
