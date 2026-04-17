import { NextRequest, NextResponse } from 'next/server'

const BACKEND = process.env.BACKEND_URL!

async function proxy(req: NextRequest, { params }: { params: Promise<{ proxy: string[] }> }) {
  const { proxy } = await params
  const path = proxy.join('/')
  const url = new URL(req.url)
  const target = `${BACKEND}/${path}${url.search}`

  const headers = new Headers()
  req.headers.forEach((value, key) => {
    if (!['host', 'connection'].includes(key.toLowerCase())) {
      headers.set(key, value)
    }
  })

  const body = req.method !== 'GET' && req.method !== 'HEAD'
    ? await req.arrayBuffer()
    : undefined

  const res = await fetch(target, {
    method: req.method,
    headers,
    body,
  })

  const responseHeaders = new Headers()
  res.headers.forEach((value, key) => {
    responseHeaders.set(key, value)
  })

  return new NextResponse(res.body, {
    status: res.status,
    headers: responseHeaders,
  })
}

export { proxy as GET, proxy as POST, proxy as PUT, proxy as DELETE, proxy as PATCH }
