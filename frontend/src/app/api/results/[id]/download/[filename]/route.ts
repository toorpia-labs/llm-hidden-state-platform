import { NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8000";

export async function GET(
  _request: Request,
  { params }: { params: { id: string; filename: string } }
) {
  const res = await fetch(
    `${BACKEND_URL}/results/${params.id}/download/${params.filename}`
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
