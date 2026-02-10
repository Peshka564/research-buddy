import { useState } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { Box, CircularProgress } from '@mui/material';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';
import type { ChunkWithCoords } from '../types/paper';
import { ChunkEmbedded } from './chunk-embedded';

// This is a big hack with vite and react-pdf to use a web worker and load the pdf
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url
).toString();

interface Props {
  pdfUrl: string;
  onChunkSelect: (c: ChunkWithCoords) => void;
  chunks: ChunkWithCoords[];
}

export function PdfOverlay({ pdfUrl, onChunkSelect, chunks }: Props) {
  const [numPages, setNumPages] = useState<number>(0);

  // Display width of the pdf
  const PDF_WIDTH = 800;

  // Renders the highlight boxes on top of the pdf text
  const renderHighlights = (pageNumber: number, originalPageWidth: number) => {
    const pageChunks = chunks.filter(c => c.page === pageNumber);
    const scale = PDF_WIDTH / originalPageWidth;

    return pageChunks.map(chunk => (
      <ChunkEmbedded
        chunk={chunk}
        onChunkSelect={onChunkSelect}
        scale={scale}
      />
    ));
  };

  return (
    <Box
      sx={{
        bgcolor: '#525659',
        p: 4,
        minHeight: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
      }}
    >
      {pdfUrl && (
        <Document
          file={pdfUrl}
          onLoadSuccess={({ numPages }) => setNumPages(numPages)}
          onLoadError={error => console.error('React-PDF Error:', error)}
          loading={<CircularProgress sx={{ color: 'white' }} />}
        >
          {Array.from(new Array(numPages), (_, index) => (
            <Box
              key={`page_${index + 1}`}
              sx={{ position: 'relative', mb: 2, boxShadow: 5 }}
            >
              <Page
                pageNumber={index + 1}
                width={PDF_WIDTH}
                renderAnnotationLayer={false} // Disable standard annotations for performance
              >
                {/* Overlay Layer */}
                <div
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '100%',
                  }}
                >
                  {/* 595.28 is standard A4 width in PDF points */}
                  {renderHighlights(index + 1, 595.28)}
                </div>
              </Page>
            </Box>
          ))}
        </Document>
      )}
    </Box>
  );
}
