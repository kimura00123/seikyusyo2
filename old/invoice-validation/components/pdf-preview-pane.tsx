"use client"

import * as React from "react"
import { Minus, Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import Image from "next/image"

interface PDFPreviewPaneProps {
  selectedInvoiceNumber: string
}

export function PDFPreviewPane({ selectedInvoiceNumber }: PDFPreviewPaneProps) {
  const [zoom, setZoom] = React.useState(1)
  const [imageError, setImageError] = React.useState(false)

  const invoiceImageUrls: Record<string, string> = {
    "1": "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/1-yyDSeFkGvtRBd2OCKP6fq2qBKYjzZD.png",
    "2": "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/2-fijU1sP6hPWMxnjiTKUaJYb0y1vIk7.png",
    "3": "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/3-nWY94xJryYKEVHUGlkzjT8hv6cFMDT.png",
  }

  const imagePath = invoiceImageUrls[selectedInvoiceNumber] || "/placeholder.svg"

  React.useEffect(() => {
    setImageError(false)
  }, [selectedInvoiceNumber])

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2 p-2 border-b">
        <Button variant="outline" size="icon" onClick={() => setZoom((z) => Math.max(0.5, z - 0.1))}>
          <Minus className="h-4 w-4" />
        </Button>
        <span className="text-sm">{Math.round(zoom * 100)}%</span>
        <Button variant="outline" size="icon" onClick={() => setZoom((z) => Math.min(2, z + 0.1))}>
          <Plus className="h-4 w-4" />
        </Button>
      </div>
      <ScrollArea className="flex-1">
        <div
          style={{
            transform: `scale(${zoom})`,
            transformOrigin: "top left",
          }}
        >
          {imageError ? (
            <div className="flex items-center justify-center h-full min-h-[300px] bg-gray-100 text-gray-500">
              画像が見つかりません
            </div>
          ) : (
            <Image
              src={imagePath || "/placeholder.svg"}
              alt={`明細番号 ${selectedInvoiceNumber} のプレビュー`}
              width={800}
              height={600}
              className="max-w-none"
              onError={() => setImageError(true)}
            />
          )}
        </div>
      </ScrollArea>
    </div>
  )
}

