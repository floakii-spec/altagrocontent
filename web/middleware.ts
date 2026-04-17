import { NextRequest, NextResponse } from 'next/server'
import { createHash } from 'crypto'

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl

  if (
    pathname.startsWith('/api/auth') ||
    pathname.startsWith('/_next') ||
    pathname.startsWith('/favicon')
  ) {
    return NextResponse.next()
  }

  const token = req.cookies.get('auth_token')?.value
  const expected = createHash('sha256')
    .update(process.env.APP_PASSWORD! + process.env.AUTH_SECRET!)
    .digest('hex')

  if (token !== expected) {
    return NextResponse.redirect(new URL('/login', req.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
}
