# index.py
import httpx
import os
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

# 'app' adalah nama variabel yang akan dicari oleh Vercel
app = FastAPI()

# Ambil URL ngrok dari Environment Variables di Vercel
TARGET_URL = os.environ.get("NGROK_TARGET_URL")

# Pastikan variabel diatur untuk menghindari error saat runtime
if not TARGET_URL:
    # Jika dijalankan lokal tanpa .env, ini akan muncul
    print("PERINGATAN: NGROK_TARGET_URL tidak diatur.")

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def reverse_proxy(request: Request, path: str):
    # Jika NGROK_TARGET_URL belum diset di Vercel, kirim error yang jelas
    if not TARGET_URL:
        return {"error": "Target URL proxy belum dikonfigurasi di server."}

    # Gunakan httpx untuk membuat klien setiap kali, lebih aman untuk serverless
    async with httpx.AsyncClient(base_url=TARGET_URL) as client:
        url = httpx.URL(path=path, query=request.url.query.encode("utf-8"))
        body = await request.body()
        headers = dict(request.headers)
        headers["host"] = client.base_url.host

        rp_req = client.build_request(
            request.method, url, headers=headers, content=body
        )
        rp_resp = await client.send(rp_req, stream=True)

        return StreamingResponse(
            rp_resp.aiter_raw(),
            status_code=rp_resp.status_code,
            headers=rp_resp.headers,
        )