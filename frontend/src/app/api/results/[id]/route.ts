import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001";

export async function GET(
  _request: Request,
  { params }: { params: { id: string } }
) {
  const res = await fetch(`${BACKEND_URL}/results/${params.id}`, { cache: 'no-store' });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
