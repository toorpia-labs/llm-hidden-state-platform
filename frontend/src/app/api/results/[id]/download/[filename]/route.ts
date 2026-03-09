import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001";

export async function GET(
  _request: Request,
  { params }: { params: { id: string; filename: string } }
) {
  const res = await fetch(
    `${BACKEND_URL}/results/${params.id}/download/${params.filename}`,
    { cache: 'no-store' }
  );

  if (!res.ok) {
    return NextResponse.json(
      { error: "File not found" },
      { status: res.status }
    );
  }

  const blob = await res.blob();
  return new NextResponse(blob, {
    headers: {
      "Content-Type": "application/octet-stream",
      "Content-Disposition": `attachment; filename="${params.filename}"`,
    },
  });
}
