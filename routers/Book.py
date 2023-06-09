from supabase import create_client, Client
from fastapi import APIRouter, Depends, HTTPException
import os
from dotenv import load_dotenv

from config.jwt_utils import User, verify_jwt
load_dotenv('.env')
from celery_tasks.email_task import reminder_schedule
from starlette.responses import JSONResponse
import datetime

router = APIRouter(prefix='/book', tags=['book'], responses={404: {"description": "Not found"}})

url = os.getenv('supabase_url')
key = os.getenv('supabase_key')

supabase: Client = create_client(url, key)
@router.get("/get-books")
async def getBook():
    books = supabase.table('bookshelf_book').select('*', count='exact').limit(1000).execute()
    return books.data

@router.get("/get-book-by-id")
async def getBookbyId(id:int):
    books = supabase.table('bookshelf_book').select('*', count='exact').eq('id', id).execute()
    if books.count == 0:
        return "Buku tidak ditemukan."
    return books.data

@router.get("/get-targetreminder")
async def getTargetReminderbyId(id:int):
    data = supabase.table('targetmembaca').select('*', count='exact').eq('id', id).execute()
    if data.count == 0:
        raise HTTPException(status_code=404, detail="Target Reminder Item not found")
    return data.data
#guys kalo emg butuh user tinggal naro -> user: User = Depends(verify_jwt), nanti klo mau akses datanya tinggal user.username atau user.email
@router.post("/target-reminder")
async def targetReminder(idbuku:int, targetdate:datetime.date, user: User = Depends(verify_jwt)):
    buku = supabase.table('bookshelf_book').select('*', count='exact').eq('id', idbuku).execute()
    if buku.count == 0:
        raise HTTPException(status_code=404, detail="Buku Item not found. Failed to create Target Reminder.")
    if datetime.date.today() > targetdate:
        raise HTTPException(status_code=400, detail="The target date must be filled with a date after today (or today).")
    data, count = supabase.table('targetmembaca').insert({"target_date": str(targetdate), "id_buku":idbuku, "email_user":user.email}).execute()
    mulai = data[1][0]['start_date'][0:10]
    task = reminder_schedule.apply_async(args=[buku.data[0], mulai, str(targetdate), user.email])
    return data

@router.get("/get-targetreminder-user")
async def getTargetReminderUser(user: User = Depends(verify_jwt)):
    data = supabase.table('targetmembaca').select('*', count='exact').eq('email_user', user.email).execute()
    if data.count == 0:
        raise HTTPException(status_code=404, detail="Target Reminder Item not found")
    for datanya in data.data:
        buku = await getBookbyId(datanya['id_buku'])
        datanya['buku'] = buku
    return data.data

@router.post("/konfirmasi-pinjam")
async def konfirmasiPinjam(idbuku:int, returndate:datetime.date, user: User = Depends(verify_jwt)):
    buku = supabase.table('bookshelf_book').select('*', count='exact').eq('id', idbuku).execute()
    if buku.count == 0:
        raise HTTPException(status_code=404, detail="Buku Item not found. Failed to create Peminjaman.")
    if datetime.date.today() > returndate:
        raise HTTPException(status_code=400, detail="The return (returning book) date must be filled with a date after today (or today).")
    data, count = supabase.table('peminjaman').insert({"return_date": str(returndate), "id_buku":idbuku, "email_user":user.email}).execute()
    return data

@router.get("/get-peminjaman")
async def getpeminjamanbyId(id:int):
    data = supabase.table('peminjaman').select('*', count='exact').eq('id', id).execute()
    if data.count == 0:
        raise HTTPException(status_code=404, detail="Peminjaman Item not found")
    return data.data

@router.get("/get-peminjaman-user")
async def getpeminjamanUser(user: User = Depends(verify_jwt)):
    data = supabase.table('peminjaman').select('*', count='exact').eq('email_user', user.email).execute()
    if data.count == 0:
        raise HTTPException(status_code=404, detail="Peminjaman Item not found")
    for datanya in data.data:
        buku = await getBookbyId(datanya['id_buku'])
        datanya['buku'] = buku
    return data.data

@router.put("/konfirmasi-pengembalian")
async def getpeminjamanUser(idpeminjaman:int, user: User = Depends(verify_jwt)):
    data = supabase.table('peminjaman').select('*', count='exact').eq('id', idpeminjaman).execute()
    if data.count == 0:
        raise HTTPException(status_code=404, detail="Peminjaman Item not found")
    if data.data[0]['email_user'] != user.email:
        raise HTTPException(status_code=403, detail="Forbidden, user doesn't have permission to edit this Peminjaman.")
    data = supabase.table('peminjaman').update({ 'status': 'dikembalikan' }).match({'id':idpeminjaman, 'email_user': user.email}).execute()
    return data.data