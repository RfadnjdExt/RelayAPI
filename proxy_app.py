# proxy_app.py
import httpx
import os
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

app = FastAPI()

# AMBIL URL NGROK ANDA DARI ENVIRONMENT VARIABLE
# Ini sangat penting agar Anda tidak perlu mengubah kode setiap kali ngrok restart
TARGET_URL = os.environ.get("NGROK_TARGET_URL")

if not TARGET_URL:
    raise ValueError("NGROK_TARGET_URL environment variable not set!")

client = httpx.AsyncClient(base_url=TARGET_URL)

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def reverse_proxy(request: Request, path: str):
    """
    Fungsi ini menangkap semua request dan meneruskannya ke target ngrok.
    """
    url = httpx.URL(path=path, query=request.url.query.encode("utf-8"))
    
    # Baca body dari request asli
    body = await request.body()
    
    # Ambil semua header dari request asli
    headers = dict(request.headers)
    # Host header harus diubah ke target, ini krusial!
    headers["host"] = client.base_url.host

    # Buat request baru ke server target (localhost via ngrok)
    rp_req = client.build_request(
        request.method, url, headers=headers, content=body,
    )
    
    # Kirim request dan tunggu response
    rp_resp = await client.send(rp_req, stream=True)

    # Kembalikan response ke klien asli, termasuk status code, header, dan content
    return StreamingResponse(
        rp_resp.aiter_raw(),
        status_code=rp_resp.status_code,
        headers=rp_resp.headers,
    )